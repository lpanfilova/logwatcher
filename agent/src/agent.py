# agent.py
import time
import logging

from collector import stream_container_logs
from shipper import send_with_retry
from config import load_config


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

def run():
    cfg = load_config()
    setup_logging(cfg.log_level)
    logger = logging.getLogger("log-agent")

    logger.info("agent started", extra={"backend_url": cfg.backend_url, "container": cfg.target_container})
    
    buf = []
    last_flush = time.time()
    dropped_batches = 0

    for event in stream_container_logs(cfg.target_container):
        buf.append(event)

        now = time.time()
        should_flush = (len(buf) >= cfg.batch_max_events) or ((now - last_flush) >= cfg.batch_flush_seconds)

        if should_flush and buf:
            batch = buf
            buf = []
            last_flush = now
            try:
                send_with_retry(
                    cfg.backend_url,
                    batch,
                    timeout_seconds=cfg.shipper_timeout_seconds,
                    max_attempts=cfg.shipper_max_attempts,
                    backoff_initial=cfg.shipper_backoff_initial_seconds,
                    backoff_max=cfg.shipper_backoff_max_seconds,
                )
                logger.info("shipped batch", extra={"batch_size": len(batch)})
            except Exception as e:
                dropped_batches += 1
                logger.error(
                    "failed to ship batch",
                    exc_info=e,
                    extra={
                        "batch_size": len(batch),
                        "dropped_batches": dropped_batches,
                    },
                )

if __name__ == "__main__":
    run()