# shipper.py

import requests
import time
from typing import List, Dict

def post_batch(server_url: str, batch: List[Dict], timeout_seconds: float) -> None:
    payload = {"events": batch}
    r = requests.post(server_url, json=payload, timeout=timeout_seconds)
    r.raise_for_status()


def send_with_retry(
        server_url: str, 
        batch: List[Dict],
        timeout_seconds: float = 5, 
        max_attempts: int = 5,
        backoff_initial: float = 0.5,
        backoff_max: float = 5.0,
) -> None:
    backoff = backoff_initial
    for attempt in range(1, max_attempts + 1):
        try:
            post_batch(server_url, batch, timeout_seconds)
            return
        except Exception:
            if attempt == max_attempts:
                raise
            time.sleep(backoff)
            backoff = min(backoff * 2, backoff_max)