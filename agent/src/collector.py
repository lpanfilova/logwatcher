# collector.py

import docker
from typing import Iterator, Dict
import time

def iter_events(cfg) -> Iterator[Dict]:
    mode = getattr(cfg, "run_mode")
    if mode == "local_test":
        yield from _iter_local_test_events(cfg)
    else:
        yield from _iter_stream_container_logs(cfg.target_container)

def _iter_stream_container_logs(target_container: str) -> Iterator[Dict]:

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    container = client.containers.get(target_container)

    for raw in container.logs(stream=True, follow=True, timestamps=True):
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        yield {
            "service": target_container,
            "source": "stdout",
            "message": line,
            "ts_collected": time.time(),
        }

def _iter_local_test_events(cfg) -> Iterator[Dict]:
    interval = float(getattr(cfg, "run_local_test_interval_seconds", 2))
    i = 0
    while True:
        i += 1
        yield {
            "service": "local_test",
            "source": "stdout",
            "message": f"test log {i}",
            "ts_collected": time.time(),
        }
        time.sleep(interval)