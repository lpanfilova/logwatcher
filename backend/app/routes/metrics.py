# Metrics routes — aggregation endpoints for dashboard summaries and time-series charts.
from fastapi import APIRouter, HTTPException
from app.db import client, build_filters
from app.config import INDEX_NAME

router = APIRouter()


# Returns a high-level summary of all indexed logs:
# total count, unique services, unique sources, and the timestamp range.
@router.get("/api/summary")
async def get_metrics_summary():
    try:
        # size=0 means we only want aggregation results, not individual documents.
        query = {
            "size": 0,
            "aggs": {
                "total_logs":  {"value_count": {"field": "timestamp"}},  # Count all indexed documents.
                "services":    {"terms": {"field": "service", "size": 50}},  # Top 50 service names.
                "sources":     {"terms": {"field": "source",  "size": 50}},  # Top 50 source names.
                "oldest_log":  {"min": {"field": "timestamp"}},  # Earliest log timestamp.
                "newest_log":  {"max": {"field": "timestamp"}},  # Latest log timestamp.
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        aggs = response.get("aggregations", {})

        return {
            "total_logs": response["hits"]["total"]["value"],
            "services": [
                {"name": b["key"], "count": b["doc_count"]}
                for b in aggs.get("services", {}).get("buckets", [])
            ],
            "sources": [
                {"name": b["key"], "count": b["doc_count"]}
                for b in aggs.get("sources", {}).get("buckets", [])
            ],
            "time_range": {
                "oldest": aggs.get("oldest_log", {}).get("value_as_string"),
                "newest": aggs.get("newest_log", {}).get("value_as_string"),
            },
        }
    except Exception as e:
        print(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


# Returns log counts bucketed by a fixed time interval, optionally filtered by service/source.
# Used to draw the main activity timeline chart.
@router.get("/api/metrics/timeline")
async def get_metrics_timeline(interval: str = "1h", service: str = None, source: str = None):
    try:
        filters = build_filters(service=service, source=source)

        query = {
            "size": 0,
            # Fall back to match_all when no filters are provided so the query remains valid.
            "query": {"bool": {"filter": filters if filters else [{"match_all": {}}]}},
            "aggs": {
                "logs_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,  # Include empty buckets so the chart has no gaps.
                    },
                },
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("logs_over_time", {}).get("buckets", [])

        return {
            "interval": interval,
            "data": [{"timestamp": b["key_as_string"], "count": b["doc_count"]} for b in buckets],
        }
    except Exception as e:
        print(f"Error fetching timeline metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch timeline metrics")


# Returns the total log count grouped by structured event name.
# Useful for identifying which event types are most frequent.
@router.get("/api/metrics/by-event")
async def get_metrics_by_event():
    try:
        query = {
            "size": 0,
            "aggs": {
                # Aggregate across all documents — no date bucketing, just event frequency.
                "by_event": {"terms": {"field": "event", "size": 100}},
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("by_event", {}).get("buckets", [])

        return {
            "events": [{"event": b["key"], "count": b["doc_count"]} for b in buckets],
        }
    except Exception as e:
        print(f"Error fetching event metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch event metrics")


# Returns log volume over time, broken down by numeric log level within each time bucket.
# Allows the frontend to render a stacked chart (e.g. DEBUG vs INFO vs ERROR per hour).
@router.get("/api/metrics/log-volume")
async def get_metrics_log_volume(interval: str = "1h", service: str = None):
    try:
        filters = build_filters(service=service)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters if filters else [{"match_all": {}}]}},
            "aggs": {
                "volume_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,  # Include empty buckets for a continuous time axis.
                    },
                    "aggs": {
                        # Nested aggregation: within each time bucket, count logs per level.
                        "by_level": {"terms": {"field": "level", "size": 10}}
                    },
                },
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("volume_over_time", {}).get("buckets", [])

        return {
            "interval": interval,
            "data": [
                {
                    "timestamp": b["key_as_string"],
                    "total": b["doc_count"],
                    # Convert level keys to strings for consistent JSON serialization.
                    "by_level": {
                        str(lvl["key"]): lvl["doc_count"]
                        for lvl in b.get("by_level", {}).get("buckets", [])
                    },
                }
                for b in buckets
            ],
        }
    except Exception as e:
        print(f"Error fetching log volume: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch log volume")


# Returns error-level logs (level >= 50) bucketed over time, plus a running total.
# Used to power the error-rate chart on the dashboard.
@router.get("/api/metrics/errors")
async def get_metrics_errors(interval: str = "1h", service: str = None):
    try:
        # Prepend the error-level filter before any optional service filter.
        filters = [{"range": {"level": {"gte": 50}}}] + build_filters(service=service)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters}},
            "aggs": {
                "errors_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,
                    },
                },
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("errors_over_time", {}).get("buckets", [])

        return {
            "interval": interval,
            "total_errors": response["hits"]["total"]["value"],  # Overall error count across all time.
            "data": [{"timestamp": b["key_as_string"], "count": b["doc_count"]} for b in buckets],
        }
    except Exception as e:
        print(f"Error fetching error metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch error metrics")


# Returns the most frequent error event types, ordered by occurrence count descending.
# Helps surface recurring failures for triage.
@router.get("/api/metrics/top-errors")
async def get_metrics_top_errors(size: int = 10, service: str = None):
    try:
        # Filter to error-level logs only, then apply any optional service filter.
        filters = [{"range": {"level": {"gte": 50}}}] + build_filters(service=service)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters}},
            "aggs": {
                "top_errors": {
                    "terms": {
                        "field": "event",
                        "size": size,
                        "order": {"_count": "desc"},  # Most frequent events first.
                    }
                }
            },
        }

        response = client.search(index=INDEX_NAME, body=query)
        buckets = response.get("aggregations", {}).get("top_errors", {}).get("buckets", [])

        return {
            "top_errors": [{"event": b["key"], "count": b["doc_count"]} for b in buckets],
        }
    except Exception as e:
        print(f"Error fetching top errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch top errors")
