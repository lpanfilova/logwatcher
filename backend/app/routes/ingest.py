from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from app.db import client, create_index_if_not_exists, parse_log_message
from app.config import INDEX_NAME

router = APIRouter()


@router.post("/api/ingest")
async def ingest_logs(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if isinstance(body, dict) and "events" in body:
        logs = body["events"]
    elif isinstance(body, list):
        logs = body
    else:
        logs = [body]

    if not logs:
        raise HTTPException(status_code=400, detail="No log events provided")

    try:
        create_index_if_not_exists()
    except Exception as e:
        print(f"Warning: Could not ensure index exists: {e}")

    indexed = 0
    errors = []

    for log_data in logs:
        try:
            ts = log_data.get("ts_collected")
            if ts:
                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(tz=timezone.utc).isoformat()

            raw_message = log_data.get("message", "")
            parsed = parse_log_message(raw_message)

            doc = {
                "timestamp": timestamp,
                "message":   raw_message,
                "service":   log_data.get("service"),
                "source":    log_data.get("source"),
                "level":     parsed.get("level"),
                "event":     parsed.get("event"),
                "msg":       parsed.get("msg"),
            }

            client.index(index=INDEX_NAME, body=doc)
            indexed += 1

            event_type = parsed.get("event", "unknown")
            level = parsed.get("level", "?")
            print(f"Indexed [{log_data.get('service')}] level={level} event={event_type}")
        except Exception as e:
            errors.append(str(e))
            print(f"Error indexing log: {e}")

    return {"status": "ok", "indexed": indexed, "errors": errors}
