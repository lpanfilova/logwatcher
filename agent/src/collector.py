# collector.py

import logging
import time
from typing import Dict, Iterator

import docker
from docker.errors import DockerException, NotFound

from observability import metrics

# Set logging with LOGGER_NAME
LOGGER_NAME = "collector_logger"
logger = logging.getLogger(LOGGER_NAME)

# Log iterator
# Streams logs from:
# - target container
# - local test service
def iter_events(cfg) -> Iterator[Dict]:
    
    mode = getattr(cfg, "run_mode")

    logger.info("collector starting in mode=%s", mode)
    
    if mode == "local_test":
        yield from _iter_local_test_events(cfg)
    else:
        yield from _iter_stream_container_logs(cfg.target_container)

# Stream logs from a Docker container and convert them into structured logs
def _iter_stream_container_logs(target_container: str) -> Iterator[Dict]:

    logger.info("connecting to docker for target_container=%s", target_container)

    try:
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")
        container = client.containers.get(target_container)
    except NotFound:
        logger.exception("target container not found: target_container=%s", target_container)
        raise
    except DockerException:
        logger.exception("failed to connect to docker or container=%s", target_container)
        raise

    logger.info("docker log stream established for target_container=%s", target_container)

    for raw in container.logs(stream=True, follow=True, timestamps=True):
        line = raw.decode("utf-8", errors="replace").rstrip("\n")

        event = {
            "service": target_container,
            "source": "stdout",
            "message": line,
            "ts_collected": time.time(),
        }

        metrics.logs_collected.inc()
        
        yield event

# Generates test logs for local testing
def _iter_local_test_events(cfg) -> Iterator[Dict]:
    
    interval = float(getattr(cfg, "run_local_test_interval_seconds", 2))
    i = 0

    logger.info("local_test log generator started: interval_seconds=%s", interval)

    while True:
        i += 1
        
        event = {
            "service": "local_test",
            "source": "stdout",
            "message": f"test log {i}",
            "ts_collected": time.time(),
        }
        
        metrics.logs_collected.inc()
        yield event
        time.sleep(interval)