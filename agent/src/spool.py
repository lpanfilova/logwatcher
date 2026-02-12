import os
import json
import time
import glob
import uuid
from dataclasses import dataclass
from typing import Dict, List, Tuple

from shipper import send_with_retry

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
    
    def _dir_usage(self) -> Tuple[int, int]:
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
            except FileNotFoundError:
                continue

    def persist_batch(self, batch: List[Dict]) -> str:
        self._enforce_limits_drop_oldest()

        name = self._batch_filename()
        # atomic write
        tmp_path = self._tmp_path(name)
        final_path = self._final_path(name)

        with open(tmp_path, "w", encoding="utf-8") as f:
            for event in batch:
                f.write(json.dumps(event, separators=(",",":"), ensure_ascii=False))
                f.write("\n")
            f.flush()
            if self.cfg.fsync_on_write:
                os.fsync(f.fileno())
        
        os.replace(tmp_path, final_path)
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
            os.remove(path)
        except FileNotFoundError:
            pass

class SpoolSender:

    def __init__(self, spool: DiskSpool, server_url: str):
        self.spool = spool
        self.server_url = server_url

    def flush_once(self) -> bool:
        files = self.spool.list_batches_oldest_first()
        if not files:
            return False
        
        oldest = files[0]

        try:
            batch = self.spool.load_batch(oldest)
        except Exception:
            bad_path = oldest + ".bad"
            try:
                os.replace(oldest, bad_path)
            except FileNotFoundError:
                pass
            return False
        
        try:
            send_with_retry(self.server_url, batch)
            self.spool.ack_delete(oldest)
            return True
        except Exception:
            return False