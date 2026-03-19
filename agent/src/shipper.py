# shipper.py

import logging
import random
import time
from typing import List, Dict, Optional

import requests
from observability import metrics

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 422}

def post_batch(server_url: str, batch: List[Dict], timeout_seconds: float) -> None:
    payload = {"events": batch}
    response = requests.post(server_url, json=payload, timeout=timeout_seconds)
    response.raise_for_status()


def get_status_code(exc: requests.exceptions.RequestException) -> Optional[int]:
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        return exc.response.status_code
    return None


def is_retryable_exception(exc: requests.exceptions.RequestException) -> bool:
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    
    status_code = get_status_code(exc)
    
    if status_code in RETRYABLE_STATUS_CODES:
        return True
    if status_code in NON_RETRYABLE_STATUS_CODES:
        return False
    if status_code is None:
        return False

    # If unknown - retry    
    return True


def send_with_retry(
        server_url: str, 
        batch: List[Dict],
        timeout_seconds: float, 
        max_attempts: int,
        backoff_initial: float,
        backoff_max: float,
) -> None:
    backoff = backoff_initial
    
    for attempt in range(1, max_attempts + 1):
        try:
            post_batch(server_url, batch, timeout_seconds)
            metrics.logs_sent.inc(len(batch))
            return
        
        except requests.exceptions.RequestException as exc:
            metrics.send_failures.inc()

            retryable = is_retryable_exception(exc)
            
            status_code = get_status_code(exc)

            logger.warning(
                "send failed attempt=%s batch_size=%s status_code=%s retryable=%s",
                attempt,
                len(batch),
                status_code,
                retryable,
            )

            if not retryable:
                raise

            if attempt == max_attempts:
                raise

            fluct = random.uniform(0.5, 1.0)
            time.sleep(backoff * fluct)
            backoff = min(backoff * 2, backoff_max)