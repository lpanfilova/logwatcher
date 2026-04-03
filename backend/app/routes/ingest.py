# Ingest route — receives log events from external sources and indexes them into OpenSearch.
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from app.db import client, create_index_if_not_exists, parse_log_message
from app.config import INDEX_NAME

router = APIRouter()


# Accepts log events as JSON and indexes each one into OpenSearch.
@router.post("/api/ingest")
async def ingest_logs(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Normalise the three supported body shapes into a flat list of log objects.
    if isinstance(body, dict) and "events" in body:
        logs = body["events"]
    elif isinstance(body, list):
        logs = body
    else:
        logs = [body]

    if not logs:
        raise HTTPException(status_code=400, detail="No log events provided")

    # Ensure the index exists before writing; log a warning but continue if it fails.
    try:
        create_index_if_not_exists()
    except Exception as e:
        print(f"Warning: Could not ensure index exists: {e}")

    indexed = 0
    errors = []

    for log_data in logs:
        try:
            # Use the collector-assigned Unix timestamp if present; fall back to now.
            ts = log_data.get("ts_collected")
            if ts:
                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(tz=timezone.utc).isoformat()

            # Attempt to extract structured fields from the raw message string.
            raw_message = log_data.get("message", "")
            parsed = parse_log_message(raw_message)

            # Build the document to index, combining top-level fields from the payload
            # with structured fields parsed out of the message body.
            doc = {
                "timestamp": timestamp,
                "message":   raw_message,           # Preserved verbatim for full-text search.
                "service":   log_data.get("service"),
                "source":    log_data.get("source"),
                "level":     parsed.get("level"),   # Numeric severity from structured log.
                "event":     parsed.get("event"),   # Event name from structured log.
                "msg":       parsed.get("msg"),     # Human-readable message from structured log.
            }

            client.index(index=INDEX_NAME, body=doc)
            indexed += 1

            event_type = parsed.get("event", "unknown")
            level = parsed.get("level", "?")
            print(f"Indexed [{log_data.get('service')}] level={level} event={event_type}")
        except Exception as e:
            # Collect per-document errors so a single bad log does not abort the batch.
            errors.append(str(e))
            print(f"Error indexing log: {e}")

    # Return a summary of how many documents were indexed and any per-document errors.
    return {"status": "ok", "indexed": indexed, "errors": errors}
