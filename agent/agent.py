import time
import os
from collector import stream_container_logs
from shipper import send_with_retry

backend_url = os.getenv("BACKEND_URL")

def run():
    buf = []
    last_flush = time.time()

    for event in stream_container_logs("demo-app"):
        buf.append(event)

        now = time.time()
        should_flush = (len(buf) >= 100) or ((now - last_flush) >= 10.0)

        if should_flush and buf:
            batch = buf
            buf = []
            last_flush = now
            try:
                # SERVER URL!!!
                send_with_retry("http://test-backend:8000/api/ingest", batch)
            except Exception:
                pass

if __name__ == "__main__":
    run()