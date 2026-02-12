from dataclasses import dataclass
from typing import Any, Dict
import os
import yaml

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
    mode: str
    local_test_interval_seconds: float

def load_config() -> Config:
    path = os.getenv("CONFIG_PATH", "/etc/agent/config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f) or {}

    batch = data.get("batch", {})
    shipper = data.get("shipper", {})
    log_cfg = data.get("logging", {})
    run_cfg = data.get("run", {})

    return Config(
        backend_url = data["backend_url"],
        target_container= data.get("target_container", "demo-app"),
        batch_max_events = int(batch.get("max_events", 100)),
        batch_flush_seconds = float(batch.get("flush_seconds", 10)),
        shipper_timeout_seconds=float(shipper.get("timeout_seconds", 5)),
        shipper_max_attempts=int(shipper.get("max_attempts", 5)),
        shipper_backoff_initial_seconds=float(shipper.get("backoff_initial_seconds", 0.5)),
        shipper_backoff_max_seconds=float(shipper.get("backoff_max_seconds", 5)),
        log_level=str(log_cfg.get("level", "INFO")).upper(),
        mode=str(run_cfg.get("mode", "docker")),
        local_test_interval_seconds=float(run_cfg.get("local_test_interval_seconds", 2))
    )