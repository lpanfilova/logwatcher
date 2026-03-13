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
- GET  /alerts        -> Latest alerts from the Watcher
- POST /ask           -> Ask a natural-language question about recent logs, get an AI-generated answer
- GET  /logs          -> live HTML viewer
- GET  /logs/recent   -> JSON snapshot
- GET  /logs/stream   -> true live SSE stream
- GET  /logs/export   -> Export logs as CSV or JSON
"""

import asyncio
import json
import os
import subprocess
import csv
import io

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from ai_client import build_filter_from_question, explain_results
from log_store import LogStore
from log_tail import tail_docker_logs, tail_file
from schemas import AskRequest, AskResponse
from watcher import Watcher
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse, Response


load_dotenv()

LOG_PATH = os.environ.get("LOG_PATH", "demo.log")
DOCKER_CONTAINER_NAME = os.environ.get("DOCKER_CONTAINER_NAME")
READ_FROM_DOCKER = os.environ.get("READ_FROM_DOCKER", "true").lower() == "true"
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "100000"))
MAX_FILE_LINES = int(os.environ.get("MAX_FILE_LINES", "100000"))

store = LogStore(max_events=MAX_EVENTS)
watcher = Watcher()

def detect_running_container() -> str | None:
    """
    Detect the first running Docker container.
    Returns the container name or None if nothing is running.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )

        containers = result.stdout.strip().splitlines()

        if containers:
            print(f"[docker] auto-detected container: {containers[0]}")
            return containers[0]

        print("[docker] no running containers found")
        return None

    except Exception as e:
        print(f"[docker] detection failed: {e}")
        return None


if not DOCKER_CONTAINER_NAME:
    DOCKER_CONTAINER_NAME = detect_running_container()

if not DOCKER_CONTAINER_NAME:
    raise RuntimeError("No Docker container found. Start a container or set DOCKER_CONTAINER_NAME.")

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

@app.on_event("startup")
async def startup() -> None:
    """Start either Docker ingestion or file tailing."""
    async def _run_ingestion() -> None:
        print(
            f"[startup] mode={'docker' if READ_FROM_DOCKER else 'file'} "
            f"log_path={LOG_PATH} container={DOCKER_CONTAINER_NAME if READ_FROM_DOCKER else 'N/A'}"
        )

        if READ_FROM_DOCKER:
            await tail_docker_logs(
                container_name=DOCKER_CONTAINER_NAME,
                output_path=LOG_PATH,
                on_event=handle_event,
                max_file_lines=MAX_FILE_LINES,
            )
        else:
            await tail_file(
                path=LOG_PATH,
                on_event=handle_event,
            )

    asyncio.create_task(_run_ingestion())


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "docker" if READ_FROM_DOCKER else "file",
        "docker_container_name": DOCKER_CONTAINER_NAME if READ_FROM_DOCKER else None,
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

@app.get("/logs/export")
def export_logs(
    format: str = Query("json", pattern="^(json|csv)$"),
    limit: int = Query(500, ge=1, le=10000),
):
    logs = store.recent(limit=limit)

    if format == "json":
        payload = [log.model_dump() for log in logs]
        return Response(
            content=json.dumps(payload, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="logs_export.json"'
            },
        )

    # CSV export
    output = io.StringIO()

    fieldnames = [
        "level",
        "time",
        "service",
        "event",
        "msg",
        "userId",
        "route",
        "method",
        "statusCode",
        "latencyMs",
        "component",
        "queryName",
        "durationMs",
        "authProvider",
        "errorCode",
        "dbHost",
        "dbPort",
        "err",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for log in logs:
        row = log.model_dump()
        if row.get("err") is not None:
            row["err"] = json.dumps(row["err"])
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="logs_export.csv"'
        },
    )

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