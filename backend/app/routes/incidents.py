# Incidents route — detects recurring error events within a rolling time window.
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import client, build_filters
from app.config import INDEX_NAME

router = APIRouter()


# Scans recent error-level logs and groups them by event name.
# An "incident" is any event that occurs at least `threshold` times within the last
# `window_minutes` minutes. Events are marked "open" if they fired recently, or
# "resolved" if the last occurrence was more than half the window ago.
@router.get("/api/incidents")
async def get_incidents(
    window_minutes: int = 5,   # How far back to look for errors.
    threshold: int = 3,        # Minimum occurrences to qualify as an incident.
    service: str = None,       # Optional filter to scope detection to one service.
):
    try:
        now = datetime.now(tz=timezone.utc)
        # Convert the window start time to milliseconds for OpenSearch range comparison.
        window_start_ms = int((now.timestamp() - (window_minutes * 60)) * 1000)

        filters = [
            {"range": {"level": {"gte": 50}}},              # Error-level logs only.
            {"range": {"timestamp": {"gte": window_start_ms}}},  # Within the rolling window.
        ] + build_filters(service=service)

        query = {
            "size": 0,  # Aggregation only — no individual documents needed.
            "query": {"bool": {"filter": filters}},
            "aggs": {
                # Group errors by event name, most frequent first.
                "by_event": {
                    "terms": {
                        "field": "event",
                        "size": 50,
                        "order": {"_count": "desc"},
                    },
                    "aggs": {
                        # Track when the event first and last occurred within the window.
                        "first_seen": {"min": {"field": "timestamp"}},
                        "last_seen":  {"max": {"field": "timestamp"}},
                        # Identify which services produced this event.
                        "by_service": {"terms": {"field": "service", "size": 10}},
                    },
                }
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("by_event", {}).get("buckets", [])

        # An incident is considered "resolved" if no errors were seen in the second half
        # of the window, meaning activity has likely stopped.
        half_window_ms = (window_minutes * 60 * 1000) / 2
        now_ms = now.timestamp() * 1000

        incidents = []
        for bucket in buckets:
            count = bucket["doc_count"]
            # Skip events that did not reach the minimum occurrence threshold.
            if count < threshold:
                continue

            last_seen_ms  = bucket["last_seen"]["value"]
            first_seen_ms = bucket["first_seen"]["value"]
            # Mark as "open" if the last error is recent (within the latter half of the window).
            status = "open" if (now_ms - last_seen_ms) < half_window_ms else "resolved"

            services = [b["key"] for b in bucket.get("by_service", {}).get("buckets", [])]

            incidents.append({
                "event":       bucket["key"],
                "count":       count,
                # Return a single string if only one service is involved, otherwise a list.
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
