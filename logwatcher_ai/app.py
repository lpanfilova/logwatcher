"""
Main FastAPI server.

What it does:
- Tails a JSON log file continuously (LOG_PATH)
- Stores recent logs in memory (LogStore)
- Runs watcher rules (Watcher) to generate alerts
- Exposes endpoints:
    GET  /health
    GET  /alerts
    POST /ask
"""

import os
import asyncio

from fastapi import FastAPI
from dotenv import load_dotenv

from schemas import AskRequest, AskResponse
from log_store import LogStore
from log_tail import tail_file
from watcher import Watcher
from ai_client import build_filter_from_question, explain_results


load_dotenv()

# Which log file to tail (default: demo.log in current directory)
LOG_PATH = os.environ.get("LOG_PATH", "demo.log")

# In-memory state for demo
store = LogStore(max_events=5000)
watcher = Watcher()

app = FastAPI(title="LogWatcher + AI (Python)")


@app.on_event("startup")
async def startup() -> None:
    """
    Start a background task that tails the log file forever.
    Every new log event updates:
      - the LogStore (for querying)
      - the Watcher (for alerts)
    """

    async def _run_tailer() -> None:
        await tail_file(
            path=LOG_PATH,
            on_event=lambda e: (store.add(e), watcher.ingest(e)),
        )

    # Fire-and-forget background task
    asyncio.create_task(_run_tailer())


@app.get("/health")
def health():
    """Simple health check."""
    return {"status": "ok", "log_path": LOG_PATH}


@app.get("/alerts")
def alerts():
    """Return latest alerts produced by watcher rules."""
    return watcher.latest_alerts(limit=10)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """
    Natural-language question endpoint.

    Flow:
      1) AI converts question -> structured filter JSON
      2) LogStore is queried using that filter
      3) AI explains ONLY the matched logs
    """
    filt = build_filter_from_question(req.question)
    matched = store.query(filt=filt, max_scan=req.max_logs)
    answer = explain_results(req.question, filt, matched)

    return AskResponse(
        filter_used=filt,
        matched_count=len(matched),
        answer=answer,
    )
