# agent.py
import time
import logging

from spool import DiskSpool, SpoolSender, SpoolConfig
from collector import iter_events
from shipper import send_with_retry
from config import load_config


def setup_logging(level: str) -> None:
    root = logging.getLogger()

    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

def run():
    setup_logging("DEBUG")
    cfg = load_config()
    spool = DiskSpool(
        SpoolConfig(
            max_spool_files=cfg.spool_max_files,
            max_spool_bytes=cfg.spool_max_bytes,
        )
    )
    sender = SpoolSender(
        spool=spool,
        server_url=cfg.backend_url,
        timeout_seconds=cfg.shipper_timeout_seconds,
        max_attempts=cfg.shipper_max_attempts,
        backoff_initial=cfg.shipper_backoff_initial_seconds,
        backoff_max=cfg.shipper_backoff_max_seconds,
    )
    setup_logging(cfg.log_level)
    logger = logging.getLogger("log-agent")
    logger.debug("final log level applied: %s", cfg.log_level)

    logger.info("agent started backend_url=%s container=%s", cfg.backend_url, cfg.target_container)
    
    buf = []
    last_flush = time.time()

    for event in iter_events(cfg):
        buf.append(event)

        now = time.time()
        should_flush = (len(buf) >= cfg.batch_max_events) or ((now - last_flush) >= cfg.batch_flush_seconds)

        if should_flush and buf:
            batch = buf
            buf = []
            last_flush = now
            
            spool.persist_batch(batch)
        
        sender.flush_once()

if __name__ == "__main__":
    run()