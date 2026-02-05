# collector.py

import docker
from typing import Iterator, Dict
import time

def stream_container_logs(target_container: str) -> Iterator[Dict]:

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