# agent.py

import logging
import time

from collector import iter_events
from config import load_config
from spool import DiskSpool, SpoolSender, SpoolConfig

LOGGER_NAME = "agent_logger"

# Configures application logging at startup
# Format: timestamp, log level, logger name (agent/collector/shipper/spool modules), message
def setup_logging(level: str) -> None:
    root = logging.getLogger()

    # Checks if logging was configured before (so that level can be reset later)
    # logging.basicConfig runs only once, so setup_logging(cfg.log_level)  won't update configuration
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    
    # Update log level
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

# MAIN agent loop
# Loads configuration, initializes disk storage and log sender
# Continuously: collects logs, batches logs in memory, persists batches to disk, tries sending persisted batches
def run() -> None:

    # Log before config loads (makes config-loading logs visible)
    setup_logging("DEBUG")

    # Load runtime configuration (YAML)
    cfg = load_config()
    
    # Spool disk storage configuration (stores logs on disk when backend server is down)
    spool = DiskSpool(
        SpoolConfig(
            max_spool_files=cfg.spool_max_files,
            max_spool_bytes=cfg.spool_max_bytes,
        )
    )

    # Send from disk configuration (takes batches from disk and sends them to backend)
    # Includes retry and backoff logic
    sender = SpoolSender(
        spool=spool,
        server_url=cfg.backend_url,
        timeout_seconds=cfg.shipper_timeout_seconds,
        max_attempts=cfg.shipper_max_attempts,
        backoff_initial=cfg.shipper_backoff_initial_seconds,
        backoff_max=cfg.shipper_backoff_max_seconds,
    )

    # Final logging setup after config loads
    setup_logging(cfg.log_level)
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("final log level applied: %s", cfg.log_level)

    # Startup log
    logger.info(
        "agent started backend_url=%s container=%s", 
        cfg.backend_url, 
        cfg.target_container
    )
    
    # In-memory buffer for batching events before writing to disk
    # Logs from this buffer can be lost if agent crashes
    buf = []

    # Timestamp of last flush to disk
    last_flush = time.time()

    # Main processing loop
    for event in iter_events(cfg):
        # Collect event to buffer
        buf.append(event)

        now = time.time()

        # Flush conditions: batch size reached & max time since last flush exceeded
        flush_due_to_size = len(buf) >= cfg.batch_max_events
        flush_due_to_time = (now - last_flush) >= cfg.batch_flush_seconds
        
        should_flush = flush_due_to_size or flush_due_to_time

        # If flush condition in met - persist batch to disk
        if should_flush and buf:
            batch = buf
            buf = [] # reset buffer
            last_flush = now

            # Save flush reason for debugging/observability
            reason = "size" if flush_due_to_size else "time"
            logger.info(
                "flushing batch to spool: reason=%s batch_size=%s",
                reason,
                len(batch),
            )
            
            # Persist batch to disk
            # Logs persisted cannot be lost
            path = spool.persist_batch(batch)
            
            logger.info(
                "batch persisted to spool: path=%s batch_size=%s",
                path,
                len(batch),
            )
        
        # Try sending one batch from disk
        flushed = sender.flush_once()
        
        if flushed:
            logger.info("flushed one batch from spool to backend")

if __name__ == "__main__":
    run()