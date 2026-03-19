"""
Main FastAPI server.

Modes:
- Docker mode:
    Reads logs directly from `docker logs -f <container>`
    Mirrors them into demo.log
    Parses JSON events into the in-memory store + watcher
- File mode:
    Follows an existing log file like `tail -f`

Endpoints:
- GET  /health        -> AI system health status
- GET  /alerts        -> Error messages from machine code
- POST /ask           -> Human to machine code request
- GET  /logs          -> live HTML viewer
- GET  /logs/recent   -> JSON snapshot
- GET  /logs/stream   -> true live SSE stream
"""

import asyncio
import json
import os
from collections import deque
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

from ai_client import build_filter_from_question, explain_results
from log_store import LogStore
from schemas import AskRequest, AskResponse, LogEvent
from watcher import Watcher

load_dotenv()

LOG_PATH = os.environ.get("LOG_PATH", "demo.log")
DOCKER_CONTAINER_NAME = os.environ.get("DOCKER_CONTAINER_NAME", "demo-app")
READ_FROM_DOCKER = os.environ.get("READ_FROM_DOCKER", "true").lower() == "true"
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://backend-api:8000/api/logs")
BACKEND_POLL_INTERVAL = float(os.environ.get("BACKEND_POLL_INTERVAL", "2.0"))
BACKEND_FETCH_SIZE = int(os.environ.get("BACKEND_FETCH_SIZE", "200"))
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "100000"))
MAX_FILE_LINES = int(os.environ.get("MAX_FILE_LINES", "100000"))

store = LogStore(max_events=MAX_EVENTS)
watcher = Watcher()
seen_event_ids: deque[str] = deque(maxlen=MAX_EVENTS)
seen_event_ids_lookup: set[str] = set()

# Small in-memory fanout queue for live browser updates
live_subscribers: list[asyncio.Queue] = []

app = FastAPI(title="LogWatcher + AI")

def handle_event(e):
    """
    Common event handler:
    - add to store
    - feed watcher
    - broadcast to any connected live viewers
    """
    store.add(e)
    watcher.ingest(e)

    payload = e.model_dump()
    dead = []

    for q in live_subscribers:
        try:
            q.put_nowait(payload)
        except Exception:
            dead.append(q)

    for q in dead:
        if q in live_subscribers:
            live_subscribers.remove(q)


def remember_event_id(event_id: str) -> None:
    if event_id in seen_event_ids_lookup:
        return

    if len(seen_event_ids) == seen_event_ids.maxlen:
        oldest_id = seen_event_ids.popleft()
        seen_event_ids_lookup.discard(oldest_id)

    seen_event_ids.append(event_id)
    seen_event_ids_lookup.add(event_id)


def normalize_backend_log(log: dict[str, Any]) -> LogEvent:
    raw_message = log.get("message") or ""
    parsed_message: dict[str, Any] = {}

    if isinstance(raw_message, str):
      try:
          candidate = json.loads(raw_message)
          if isinstance(candidate, dict):
              parsed_message = candidate
      except json.JSONDecodeError:
          parsed_message = {}

    return LogEvent(**{
        "level": log.get("level") if log.get("level") is not None else parsed_message.get("level", 30),
        "time": parsed_message.get("time") or log.get("timestamp"),
        "service": log.get("service") or parsed_message.get("service") or "unknown",
        "event": log.get("event") or parsed_message.get("event") or "unknown",
        "msg": log.get("msg") or parsed_message.get("msg"),
        "userId": parsed_message.get("userId"),
        "route": parsed_message.get("route"),
        "method": parsed_message.get("method"),
        "statusCode": parsed_message.get("statusCode"),
        "latencyMs": parsed_message.get("latencyMs"),
        "component": parsed_message.get("component"),
        "queryName": parsed_message.get("queryName"),
        "durationMs": parsed_message.get("durationMs"),
        "authProvider": parsed_message.get("authProvider"),
        "errorCode": parsed_message.get("errorCode"),
        "dbHost": parsed_message.get("dbHost"),
        "dbPort": parsed_message.get("dbPort"),
        "err": parsed_message.get("err"),
    })


def fetch_backend_logs() -> list[dict[str, Any]]:
    params = urlencode({"size": BACKEND_FETCH_SIZE})
    with urlopen(f"{BACKEND_API_URL}?{params}", timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    logs = payload.get("logs", [])
    return logs if isinstance(logs, list) else []


async def poll_backend_logs() -> None:
    while True:
        try:
            logs = await asyncio.to_thread(fetch_backend_logs)
            new_events = 0

            for log in reversed(logs):
                event_id = log.get("id")
                if not event_id or event_id in seen_event_ids_lookup:
                    continue

                handle_event(normalize_backend_log(log))
                remember_event_id(event_id)
                new_events += 1

            if new_events:
                print(f"[backend] ingested {new_events} new logs from {BACKEND_API_URL}")
        except URLError as error:
            print(f"[backend] ERROR: {error}")
        except Exception as error:
            print(f"[backend] ERROR: {error}")

        await asyncio.sleep(BACKEND_POLL_INTERVAL)


@app.on_event("startup")
async def startup() -> None:
    """Start either Docker ingestion or file tailing."""
    async def _run_ingestion() -> None:
        print(
            f"[startup] mode={'docker' if READ_FROM_DOCKER else 'backend'} "
            f"log_path={LOG_PATH} container={DOCKER_CONTAINER_NAME if READ_FROM_DOCKER else 'N/A'} "
            f"backend_api_url={BACKEND_API_URL if not READ_FROM_DOCKER else 'N/A'}"
        )

        if READ_FROM_DOCKER:
            raise RuntimeError("Docker log mode is no longer supported in this deployment.")
        else:
            await poll_backend_logs()

    asyncio.create_task(_run_ingestion())


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "docker" if READ_FROM_DOCKER else "backend",
        "docker_container_name": DOCKER_CONTAINER_NAME if READ_FROM_DOCKER else None,
        "backend_api_url": BACKEND_API_URL if not READ_FROM_DOCKER else None,
        "log_path": LOG_PATH,
        "stored_events": store.count(),
        "store_capacity": store.capacity(),
        "max_file_lines": MAX_FILE_LINES,
        "live_subscribers": len(live_subscribers),
    }


@app.get("/alerts")
def alerts():
    return watcher.latest_alerts(limit=10)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    filt = build_filter_from_question(req.question)
    matched = store.query(filt=filt, max_scan=req.max_logs)
    answer = explain_results(req.question, filt, matched)

    return AskResponse(
        filter_used=filt,
        matched_count=len(matched),
        answer=answer,
    )


@app.get("/logs/recent")
def recent_logs(limit: int = 100):
    return store.recent(limit=limit)


@app.get("/logs/stream")
async def logs_stream():
    """
    True live stream using Server-Sent Events (SSE).
    Browser gets each log event as soon as it arrives.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    live_subscribers.append(queue)

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                yield f"data: {json.dumps(item)}\n\n"
        finally:
            if queue in live_subscribers:
                live_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/logs", response_class=HTMLResponse)
def logs_page():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>Live Logs</title>
  <style>
    body {
      background: #0f172a;
      color: #e5e7eb;
      font-family: monospace;
      padding: 10px;
    }
    .log {
      padding: 4px 0;
      border-bottom: 1px solid #1e293b;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .lvl-30 { color: #9ca3af; }
    .lvl-40 { color: #fbbf24; }
    .lvl-50 { color: #f87171; }
  </style>
</head>
<body>
  <h2>Live Logs (streaming)</h2>
  <div id="status">Connecting...</div>
  <div id="logs"></div>

  <script>
    const container = document.getElementById('logs');
    const status = document.getElementById('status');

    function appendLog(l) {
      const div = document.createElement('div');
      div.className = 'log lvl-' + (l.level || 30);
      div.textContent = `[${l.time}] level=${l.level} event=${l.event} msg=${l.msg || ''}`;
      container.appendChild(div);

      // keep browser page light too
      while (container.children.length > 300) {
        container.removeChild(container.firstChild);
      }

      window.scrollTo(0, document.body.scrollHeight);
    }

    // Load recent logs first
    fetch('/logs/recent?limit=100')
      .then(r => r.json())
      .then(logs => {
        logs.forEach(appendLog);
      });

    // Then switch to true live streaming
    const evt = new EventSource('/logs/stream');

    evt.onopen = () => {
      status.textContent = 'Connected';
    };

    evt.onmessage = (event) => {
      const log = JSON.parse(event.data);
      appendLog(log);
    };

    evt.onerror = () => {
      status.textContent = 'Disconnected - retrying...';
    };
  </script>
</body>
</html>
"""
