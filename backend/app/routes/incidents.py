from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import client, build_filters
from app.config import INDEX_NAME

router = APIRouter()


@router.get("/api/incidents")
async def get_incidents(
    window_minutes: int = 5,
    threshold: int = 3,
    service: str = None,
):
    try:
        now = datetime.now(tz=timezone.utc)
        window_start_ms = int((now.timestamp() - (window_minutes * 60)) * 1000)

        filters = [
            {"range": {"level": {"gte": 50}}},
            {"range": {"timestamp": {"gte": window_start_ms}}},
        ] + build_filters(service=service)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters}},
            "aggs": {
                "by_event": {
                    "terms": {
                        "field": "event",
                        "size": 50,
                        "order": {"_count": "desc"},
                    },
                    "aggs": {
                        "first_seen": {"min": {"field": "timestamp"}},
                        "last_seen":  {"max": {"field": "timestamp"}},
                        "by_service": {"terms": {"field": "service", "size": 10}},
                    },
                }
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("by_event", {}).get("buckets", [])

        half_window_ms = (window_minutes * 60 * 1000) / 2
        now_ms = now.timestamp() * 1000

        incidents = []
        for bucket in buckets:
            count = bucket["doc_count"]
            if count < threshold:
                continue

            last_seen_ms  = bucket["last_seen"]["value"]
            first_seen_ms = bucket["first_seen"]["value"]
            status = "open" if (now_ms - last_seen_ms) < half_window_ms else "resolved"

            services = [b["key"] for b in bucket.get("by_service", {}).get("buckets", [])]

            incidents.append({
                "event":       bucket["key"],
                "count":       count,
                "service":     services[0] if len(services) == 1 else services,
                "first_seen":  datetime.fromtimestamp(first_seen_ms / 1000, tz=timezone.utc).isoformat(),
                "last_seen":   datetime.fromtimestamp(last_seen_ms  / 1000, tz=timezone.utc).isoformat(),
                "status":      status,
            })

        return {
            "window_minutes": window_minutes,
            "threshold":      threshold,
            "incidents":      incidents,
        }
    except Exception as e:
        print(f"Error detecting incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect incidents")
