# shipper.py

import logging
import random
import time
from enum import Enum
from typing import List, Dict, Optional

import requests

from observability import metrics

LOGGER_NAME = "shipper_logger"
logger = logging.getLogger(LOGGER_NAME)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 422}

class SendResult(str, Enum):
    DELIVERED = "delivered"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_NON_RETRYABLE = "failed_non_retryable"

# Sends one batch to backend
# Raises: requests.exceptions.RequestException subclasses
def post_batch(server_url: str, batch: List[Dict], timeout_seconds: float) -> None:
    
    payload = {"events": batch}
    
    start = time.perf_counter()
    try:
        response = requests.post(server_url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
    finally:
        metrics.ship_latency.observe(time.perf_counter() - start)

# Gets exception status code
def get_status_code(exc: requests.exceptions.RequestException) -> Optional[int]:
    
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        return exc.response.status_code
    
    return None


# Determines whether a failed send should be retried
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

    # If unknown HTTP status - retry    
    return True

# Tries to deliver a batch
def send_with_retry(
        server_url: str, 
        batch: List[Dict],
        timeout_seconds: float, 
        max_attempts: int,
        backoff_initial: float,
        backoff_max: float,
) -> SendResult:
    backoff = backoff_initial
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(
                "sending batch: attempt=%s batch_size=%s server_url=%s timeout_seconds=%s",
                attempt,
                len(batch),
                server_url,
                timeout_seconds,
            )

            post_batch(server_url, batch, timeout_seconds)
            
            metrics.logs_sent.inc(len(batch))
            logger.info(
                "batch delivered successfully: attempt=%s batch_size=%s",
                attempt,
                len(batch),
            )

            return SendResult.DELIVERED
        
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
                logger.error(
                    "non-retryable send failure: batch_size=%s status_code=%s",
                    len(batch),
                    status_code,
                )
                return SendResult.FAILED_NON_RETRYABLE

            if attempt == max_attempts:
                logger.error(
                    "retry attempts exhausted: attempts=%s batch_size=%s",
                    max_attempts,
                    len(batch),
                )
                return SendResult.FAILED_RETRYABLE

            # Adding time  fluctuation in retry attempts to avoid synchronization
            fluct = random.uniform(0.5, 1.0)
            time.sleep(backoff * fluct)
            backoff = min(backoff * 2, backoff_max)

    return SendResult.FAILED_RETRYABLE