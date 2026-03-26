# spool.py

import glob
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from observability import metrics
from shipper import SendResult, send_with_retry 

LOGGER_NAME = "spool_logger"
logger = logging.getLogger(LOGGER_NAME)

# Configuration for the disk-backed spool
@dataclass
class SpoolConfig:
    spool_dir: str = "./spool"
    max_spool_files: int = 10_000
    max_spool_bytes: int = 512 * 1024 * 1024 #512mb
    fsync_on_write: bool = True

# Disk-backed queue for persisted batches
# Writes batches as JSONL files
class DiskSpool:

    def __init__(self, cfg: SpoolConfig):
        self.cfg = cfg

        # Ensure spool directory exists before any writes
        os.makedirs(self.cfg.spool_dir, exist_ok=True)

        # Local counter helps make filenames unique
        self._counter = 0

        # Initialize spool metrics from current on-disk state
        num_files,total_bytes = self._dir_usage()
        metrics.spool_bytes.set(total_bytes)
        metrics.spool_files.set(num_files)

        logger.info(
            "disk spool initialized: spool_dir=%s files=%s bytes=%s max_files=%s max_bytes=%s",
            self.cfg.spool_dir,
            num_files,
            total_bytes,
            self.cfg.max_spool_files,
            self.cfg.max_spool_bytes,
        )

    # Millisecond timestamp used in filenames
    def _now_ms(self) -> int:
        return int(time.time() * 1000)
    
    # Builds a unique batch filename
    # Sorting by filename sorts by creation time
    def _batch_filename(self) -> str:
        self._counter += 1
        return f"batch_{self._now_ms()}_{self._counter}_{uuid.uuid4().hex[:8]}.jsonl"
    
    # Temporary path used during write: .tmp_
    # Needed for atomic write
    def _tmp_path(self, final_name: str) -> str:
        return os.path.join(self.cfg.spool_dir, f".tmp_{final_name}")
    
    # Final visible path for a persisted batch
    def _final_path(self, final_name: str) -> str:
        return os.path.join(self.cfg.spool_dir, final_name)
    
    # Returns batch files ordered oldest-first
    def list_batches_oldest_first(self) -> List[str]:
        pattern = os.path.join(self.cfg.spool_dir, "batch_*.jsonl")
        files = glob.glob(pattern)
        files.sort()
        return files
    
    # Calculates total spool usage:
    #   (number of files, total bytes)
    # If a file disappears during calculation, skips it and continues
    def _dir_usage(self, files: Optional[List[str]] = None) -> Tuple[int, int]:
        if files is None:
            files = self.list_batches_oldest_first()
        total = 0
        for p in files:
            try:
                total += os.path.getsize(p)
            except FileNotFoundError:
                continue
        return (len(files), total)
    
    # Enforces spool size limits before writing a new batch
    # Drops oldest batches if disk backlog exceeds configured limits
    # Protects the agent from unlimited disk growth
    def _enforce_limits_drop_oldest(self) -> None:
        files = self.list_batches_oldest_first()
        num_files, total_bytes = self._dir_usage()

        i = 0
        while (num_files > self.cfg.max_spool_files) or (total_bytes > self.cfg.max_spool_bytes):
            
            # Stop if there is nothing left to drop
            if i >= len(files):
                break
            oldest = files[i]
            i += 1
            
            try:
                oldest_file_size = os.path.getsize(oldest)
                os.remove(oldest)
                num_files -=1
                total_bytes -= oldest_file_size
                metrics.dropped_batches.inc()

                logger.warning(
                    "dropped oldest batch to enforce spool limits: path=%s size_bytes=%s remaining_files=%s remaining_bytes=%s",
                    oldest,
                    oldest_size,
                    num_files,
                    total_bytes,
                )

            except FileNotFoundError:
                continue
        
        metrics.spool_files.set(num_files)
        metrics.spool_bytes.set(total_bytes)

    # Saves one batch to disk atomically
    # Batch becomes durable and can be retried later even if the process crashes
    def persist_batch(self, batch: List[Dict]) -> str:
        
        self._enforce_limits_drop_oldest()

        name = self._batch_filename()
        tmp_path = self._tmp_path(name)
        final_path = self._final_path(name)

        # Write JSONL to temporary file first
        with open(tmp_path, "w", encoding="utf-8") as f:
            for event in batch:
                f.write(json.dumps(event, separators=(",",":"), ensure_ascii=False))
                f.write("\n")
            f.flush()
            
            if self.cfg.fsync_on_write:
                os.fsync(f.fileno())
        
        # Atomic rename: readers never see a half-written final file
        os.replace(tmp_path, final_path)
        
        file_size = os.path.getsize(final_path)
        metrics.spool_files.inc()
        metrics.spool_bytes.inc(file_size)

        logger.debug(
            "batch persisted: path=%s batch_size=%s file_size_bytes=%s",
            final_path,
            len(batch),
            file_size,
        )
        
        return final_path

    # Loads a batch file back into memory before sending it
    # Each line must be valid JSON
    def load_batch(self, path: str) -> List[Dict]:
        batch: List[Dict] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start = 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    batch.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in spool file {path} at line {line_number}") from exc
        
        return batch
    
    # Deletes a batch after successful delivery
    # "ack" means the batch no longer needs to stay in storage
    def ack_delete(self, path: str) -> None:
        try:
            file_size = os.path.getsize(path)
            os.remove(path)
            metrics.spool_files.dec()
            metrics.spool_bytes.dec(file_size)
            logger.debug(
                "acknowledged and deleted spool batch: path=%s size_bytes=%s", 
                path, 
                file_size
            )
        except FileNotFoundError:
            logger.warning("spool batch already missing during ack_delete: path=%s", path)

# Sends persisted batches from disk to backend
# Sends oldest batches first
class SpoolSender:

    def __init__(
            self, 
            spool: DiskSpool, 
            server_url: str,
            timeout_seconds: float,
            max_attempts: int,
            backoff_initial: float,
            backoff_max: float,
            ):
        self.spool = spool
        self.server_url = server_url
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.backoff_initial = backoff_initial
        self.backoff_max = backoff_max

    # Try to send at most one persisted batch
    # Returns True only when a batch was successfully delivered and removed
    def flush_once(self) -> bool:
        files = self.spool.list_batches_oldest_first()
        if not files:
            return False
        
        oldest = files[0]

        # Read the oldest batch from disk.
        # If the file is corrupt, quarantine it by renaming to .bad
        # so it does not block the queue forever.
        try:
            batch = self.spool.load_batch(oldest)
        except Exception:
            bad_path = oldest + ".bad"
            logger.exception(
                "failed to load batch from spool; moving to .bad", 
                extra={"path": oldest}
            )
            try:
                os.replace(oldest, bad_path)
            except FileNotFoundError:
                logger.warning(
                    "spool file disappeared before quarantine: path=%s", 
                    oldest
                )
            return False
        
        result = send_with_retry(
            server_url=self.server_url,
            batch=batch,
            timeout_seconds=self.timeout_seconds,
            max_attempts=self.max_attempts,
            backoff_initial=self.backoff_initial,
            backoff_max=self.backoff_max,
        )

        # Successfully sent -> remove batch from durable queue
        if result == SendResult.DELIVERED:
            self.spool.ack_delete(oldest)
            logger.info(
                "spool batch delivered and removed: path=%s batch_size=%s", 
                oldest, 
                len(batch)
            )
            return True
        # Non-retryable failure -> drop the batch so it does not block newer batches
        if result == SendResult.FAILED_NON_RETRYABLE:
            logger.error(
                "dropping batch due to non-retryable send failure: path=%s batch_size=%s",
                oldest,
                len(batch),
            )
            self.spool.ack_delete(oldest)
            metrics.dropped_batches.inc()
            return False

        # Retryable failure -> keep the batch on disk for future retries
        if result == SendResult.FAILED_RETRYABLE:
            logger.warning(
                "keeping batch on disk after retryable send failure: path=%s batch_size=%s",
                oldest,
                len(batch),
            )
            return False
        
        # Log unexpected result
        logger.error(
            "unexpected send result; keeping batch on disk: path=%s batch_size=%s result=%s",
            oldest,
            len(batch),
            result,
        )

        return False