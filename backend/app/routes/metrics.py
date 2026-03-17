from fastapi import APIRouter, HTTPException
from app.db import client, build_filters
from app.config import INDEX_NAME

router = APIRouter()


@router.get("/api/summary")
async def get_metrics_summary():
    try:
        query = {
            "size": 0,
            "aggs": {
                "total_logs":  {"value_count": {"field": "timestamp"}},
                "services":    {"terms": {"field": "service", "size": 50}},
                "sources":     {"terms": {"field": "source",  "size": 50}},
                "oldest_log":  {"min": {"field": "timestamp"}},
                "newest_log":  {"max": {"field": "timestamp"}},
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


@router.get("/api/metrics/timeline")
async def get_metrics_timeline(interval: str = "1h", service: str = None, source: str = None):
    try:
        filters = build_filters(service=service, source=source)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters if filters else [{"match_all": {}}]}},
            "aggs": {
                "logs_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,
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


@router.get("/api/metrics/by-event")
async def get_metrics_by_event():
    try:
        query = {
            "size": 0,
            "aggs": {
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
                        "min_doc_count": 0,
                    },
                    "aggs": {
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


@router.get("/api/metrics/errors")
async def get_metrics_errors(interval: str = "1h", service: str = None):
    try:
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
            "total_errors": response["hits"]["total"]["value"],
            "data": [{"timestamp": b["key_as_string"], "count": b["doc_count"]} for b in buckets],
        }
    except Exception as e:
        print(f"Error fetching error metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch error metrics")


@router.get("/api/metrics/top-errors")
async def get_metrics_top_errors(size: int = 10, service: str = None):
    try:
        filters = [{"range": {"level": {"gte": 50}}}] + build_filters(service=service)

        query = {
            "size": 0,
            "query": {"bool": {"filter": filters}},
            "aggs": {
                "top_errors": {
                    "terms": {
                        "field": "event",
                        "size": size,
                        "order": {"_count": "desc"},
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
