# agent.py
import time
import logging

from spool import DiskSpool, SpoolSender, SpoolConfig
from collector import iter_events
from shipper import send_with_retry
from config import load_config


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

def run():
    cfg = load_config()
    spool = DiskSpool(
        SpoolConfig(
            max_spool_files=cfg.spool_max_files,
            max_spool_bytes=cfg.spool_max_bytes,
        )
    )
    sender = SpoolSender(spool, cfg.backend_url)
    setup_logging(cfg.log_level)
    logger = logging.getLogger("log-agent")

    logger.info("agent started", extra={"backend_url": cfg.backend_url, "container": cfg.target_container})
    
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