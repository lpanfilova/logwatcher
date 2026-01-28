import docker
from typing import Iterator, Dict
import time

def stream_container_logs(container_name: str) -> Iterator[Dict]:

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    container = client.containers.get(container_name)

    for raw in container.logs(stream=True, follow=True, timestamps=True):
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        yield {
            "service": container_name,
            "source": "stdout",
            "message": line,
            "ts_collected": time.time(),
        }