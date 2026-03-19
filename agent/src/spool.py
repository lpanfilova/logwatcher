# spool.py

import os
import json
import time
import glob
import uuid
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging

from shipper import send_with_retry, SendResult
from observability import metrics

logger = logging.getLogger(__name__)

@dataclass
class SpoolConfig:
    spool_dir: str = "./spool"
    max_spool_files: int = 10_000
    max_spool_bytes: int = 512 * 1024 * 1024 #512mb
    fsync_on_write: bool = True

class DiskSpool:

    def __init__(self, cfg: SpoolConfig):
        self.cfg = cfg
        os.makedirs(self.cfg.spool_dir, exist_ok=True)
        self._counter = 0
        num_files,total_bytes = self._dir_usage()
        metrics.spool_bytes.set(total_bytes)
        metrics.spool_files.set(num_files)

    
    def _now_ms(self) -> int:
        return int(time.time() * 1000)
    
    # constructs batch file name
    def _batch_filename(self) -> str:
        self._counter += 1
        return f"batch_{self._now_ms()}_{self._counter}_{uuid.uuid4().hex[:8]}.jsonl"
    
    # constructs temporary file path adding .tmp_
    def _tmp_path(self, final_name: str) -> str:
        return os.path.join(self.cfg.spool_dir, f".tmp_{final_name}")
    
    
    def _final_path(self, final_name: str) -> str:
        return os.path.join(self.cfg.spool_dir, final_name)
    
    def list_batches_oldest_first(self) -> List[str]:
        pattern = os.path.join(self.cfg.spool_dir, "batch_*.jsonl")
        files = glob.glob(pattern)
        files.sort()
        return files
    
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
    
    def _enforce_limits_drop_oldest(self) -> None:
        files = self.list_batches_oldest_first()
        num_files, total_bytes = self._dir_usage()

        i = 0
        while (num_files > self.cfg.max_spool_files) or (total_bytes > self.cfg.max_spool_bytes):
            # stop if all files checked
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
            except FileNotFoundError:
                continue
        
        metrics.spool_files.set(num_files)
        metrics.spool_bytes.set(total_bytes)

    def persist_batch(self, batch: List[Dict]) -> str:
        self._enforce_limits_drop_oldest()

        name = self._batch_filename()
        
        tmp_path = self._tmp_path(name)
        final_path = self._final_path(name)

        with open(tmp_path, "w", encoding="utf-8") as f:
            for event in batch:
                f.write(json.dumps(event, separators=(",",":"), ensure_ascii=False))
                f.write("\n")
            f.flush()
            if self.cfg.fsync_on_write:
                os.fsync(f.fileno())
        
        # atomic write
        os.replace(tmp_path, final_path)
        file_size = os.path.getsize(final_path)
        metrics.spool_files.inc()
        metrics.spool_bytes.inc(file_size)
        
        return final_path

    def load_batch(self, path: str) -> List[Dict]:
        batch: List[Dict] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                batch.append(json.loads(line))
        
        return batch
    
    def ack_delete(self, path: str) -> None:
        try:
            file_size = os.path.getsize(path)
            os.remove(path)
            metrics.spool_files.dec()
            metrics.spool_bytes.dec(file_size)
        except FileNotFoundError:
            pass

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

    def flush_once(self) -> bool:
        files = self.spool.list_batches_oldest_first()
        if not files:
            return False
        
        oldest = files[0]

        try:
            batch = self.spool.load_batch(oldest)
        except Exception:
            bad_path = oldest + ".bad"
            logger.exception("failed to load batch from spool; moving to .bad", extra={"path": oldest})
            try:
                os.replace(oldest, bad_path)
            except FileNotFoundError:
                pass
            return False
        
        result = send_with_retry(
            server_url=self.server_url,
            batch=batch,
            timeout_seconds=self.timeout_seconds,
            max_attempts=self.max_attempts,
            backoff_initial=self.backoff_initial,
            backoff_max=self.backoff_max,
        )

        if result == SendResult.DELIVERED:
            self.spool.ack_delete(oldest)
            return True

        if result == SendResult.FAILED_NON_RETRYABLE:
            logger.error(
                "dropping batch due to non-retryable send failure",
                extra={"path": oldest, "batch_size": len(batch)},
            )
            self.spool.ack_delete(oldest)
            metrics.dropped_batches.inc()
            return False

        if result == SendResult.FAILED_RETRYABLE:
            logger.warning(
            "keeping batch on disk after retryable send failure",
            extra={"path": oldest, "batch_size": len(batch)},
            )
            return False
        
        logger.error(
        "unexpected send result; keeping batch on disk",
        extra={"path": oldest, "batch_size": len(batch), "result": str(result)},
        )

        return False