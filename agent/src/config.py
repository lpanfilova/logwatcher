from dataclasses import dataclass
from typing import Any, Dict
import os
import logging
import yaml

logger = logging.getLogger(__name__)

# configuration data: startup, batching, shipping, logging, run, spooling
@dataclass(frozen=True)
class Config:
    backend_url: str
    target_container: str

    batch_max_events: int
    batch_flush_seconds: float

    shipper_timeout_seconds: float
    shipper_max_attempts: int
    shipper_backoff_initial_seconds: float
    shipper_backoff_max_seconds: float

    log_level: str

    run_mode: str
    run_local_test_interval_seconds: float

    spool_dir: str
    spool_max_files: int
    spool_max_bytes: int

# Loads agent configuration from YAML
def load_config() -> Config:

    # CONFIG_PATH may override the default location: /etc/agent/config.yaml
    path = os.getenv("CONFIG_PATH", "/etc/agent/config.yaml")
    
    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f) or {}

    batch = data.get("batch", {})
    shipper = data.get("shipper", {})
    log_cfg = data.get("log", {})
    run_cfg = data.get("run", {})
    spool_cfg = data.get("spool", {})

    cfg = Config(
        backend_url = data.get("backend_url", "http://backend-api:8000/api/ingest"),
        target_container= data.get("target_container", "demo-app"),
        batch_max_events = int(batch.get("max_events", 100)),
        batch_flush_seconds = float(batch.get("flush_seconds", 10)),
        shipper_timeout_seconds=float(shipper.get("timeout_seconds", 5)),
        shipper_max_attempts=int(shipper.get("max_attempts", 5)),
        shipper_backoff_initial_seconds=float(shipper.get("backoff_initial_seconds", 0.5)),
        shipper_backoff_max_seconds=float(shipper.get("backoff_max_seconds", 5)),
        log_level=str(log_cfg.get("level", "INFO")).upper(),
        run_mode=str(run_cfg.get("mode", "docker")),
        run_local_test_interval_seconds=float(run_cfg.get("local_test_interval_seconds", 2)),
        spool_dir=str(spool_cfg.get("dir")),
        spool_max_files=int(spool_cfg.get("max_files")),
        spool_max_bytes=int(spool_cfg.get("max_bytes")),
    )

    logger.debug(
        "configuration loaded successfully: run_mode=%s target_container=%s batch_max_events=%s batch_flush_seconds=%s spool_dir=%s",
        cfg.run_mode,
        cfg.target_container,
        cfg.batch_max_events,
        cfg.batch_flush_seconds,
        cfg.spool_dir,
    )


    return cfg