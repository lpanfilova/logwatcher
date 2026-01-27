import requests
import time
from typing import List, Dict

def post_batch(server_url: str, batch: List[Dict]) -> None:
    payload = {"events": batch}
    r = requests.post(server_url, json=payload, timeout=5)
    r.raise_for_status()


def send_with_retry(server_url: str, batch: List[Dict], max_attempts: int = 5) -> None:
    backoff = 0.5
    for attempt in range(1, max_attempts + 1):
        try:
            post_batch(server_url, batch)
            return
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2, 5.0)