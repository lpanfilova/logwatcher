# =============================================================================
# LogWatcher API
# =============================================================================
# This API receives logs from the log forwarding agent, stores them in
# OpenSearch, and provides endpoints for the frontend dashboard to query
# and display log metrics.
#
# Endpoints:
#   POST /api/ingest         - Receive logs from agent
#   GET  /api/logs           - Search and filter logs
#   GET  /api/metrics/*      - Various aggregation endpoints for dashboard
# =============================================================================

import os
import json
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from opensearchpy import OpenSearch

# =============================================================================
# Configuration
# =============================================================================
# OpenSearch connection settings - can be overridden via environment variables
# Default values work for local development
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))
INDEX_NAME = "logs"  # Name of the OpenSearch index where logs are stored

# =============================================================================
# OpenSearch Client
# =============================================================================
# Create a connection to the OpenSearch database
opensearch_client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)


# =============================================================================
# Helper Functions
# =============================================================================

def create_index_if_not_exists():
    # Creates the logs index with proper field mappings if it doesn't exist
    # This must run BEFORE any documents are indexed, otherwise OpenSearch
    # will auto-create the index with incorrect field types (text vs keyword)
    if not opensearch_client.indices.exists(index=INDEX_NAME):
        index_body = {
            "settings": {
                "number_of_shards": 1,    # Single shard for small deployments
                "number_of_replicas": 0,  # No replicas for development
            },
            "mappings": {
                "properties": {
                    # Field type explanations:
                    # - "date": Enables date range queries and sorting
                    # - "text": Full-text searchable, analyzed into tokens
                    # - "keyword": Exact match only, used for filtering/aggregations
                    # - "integer": Numeric type for level comparisons
                    "timestamp": {"type": "date"},      # When the log was collected
                    "message": {"type": "text"},        # Raw log message (searchable)
                    "service": {"type": "keyword"},     # Service name (e.g., "demo-app")
                    "source": {"type": "keyword"},      # Log source (stdout/stderr)
                    "level": {"type": "integer"},       # Log level (30=INFO, 40=WARN, 50=ERROR)
                    "event": {"type": "keyword"},       # Event type (e.g., "http_request")
                    "msg": {"type": "text"},            # Human-readable message from JSON
                }
            },
        }
        opensearch_client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"Created index: {INDEX_NAME}")


def parse_log_message(message: str) -> dict:
    # Extracts JSON data from a log message string
    # Docker adds a timestamp prefix before the JSON, so we need to strip it
    # Example input: "2026-01-27T22:43:26.506Z {"level":30,"event":"http_request",...}"
    # Returns: {"level": 30, "event": "http_request", ...}
    if not message:
        return {}
    try:
        # Find where the JSON object starts (first '{' character)
        json_start = message.find('{')
        if json_start > 0:
            # Strip everything before the JSON
            message = message[json_start:]
        return json.loads(message)
    except (json.JSONDecodeError, ValueError):
        # Return empty dict if message is not valid JSON
        return {}


# =============================================================================
# FastAPI Application Setup
# =============================================================================

app = FastAPI(title="LogWatcher API")

# CORS middleware allows the frontend dashboard to make requests to this API
# In production, you should restrict allow_origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow requests from any origin
    allow_credentials=True,     # Allow cookies/auth headers
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)


@app.on_event("startup")
async def startup():
    # Runs when the API server starts
    # Attempts to create the OpenSearch index if it doesn't exist
    print(f"LogWatcher API starting...")
    print(f"OpenSearch: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
    try:
        create_index_if_not_exists()
        print("OpenSearch index ready")
    except Exception as e:
        # Don't crash if OpenSearch isn't ready yet - we'll try again on first ingest
        print(f"Warning: Could not connect to OpenSearch: {e}")


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/")
def root():
    # Simple health check endpoint to verify the API is running
    return {"status": "ok", "message": "LogWatcher API is running"}


# =============================================================================
# Log Ingestion Endpoint
# =============================================================================

@app.post("/api/ingest")
async def ingest_logs(request: Request):
    # Receives logs from the log forwarding agent and stores them in OpenSearch
    #
    # Expected input format from agent:
    # {
    #   "events": [
    #     {"service": "demo-app", "source": "stdout", "message": "...", "ts_collected": 1234567890.123},
    #     ...
    #   ]
    # }
    #
    # Returns: {"status": "ok", "indexed": 5, "errors": []}

    body = await request.json()

    # The agent wraps logs in {"events": [...]} - unwrap it
    # Also handle if someone sends a raw list or single log object
    if isinstance(body, dict) and "events" in body:
        logs = body["events"]
    elif isinstance(body, list):
        logs = body
    else:
        logs = [body]

    # Ensure index exists with correct mapping before indexing any documents
    # This prevents OpenSearch from auto-creating with wrong field types
    try:
        create_index_if_not_exists()
    except Exception as e:
        print(f"Warning: Could not ensure index exists: {e}")

    indexed = 0  # Counter for successfully indexed logs
    errors = []  # List of error messages

    # Process each log entry
    for log_data in logs:
        try:
            # Convert Unix timestamp to ISO format for OpenSearch
            ts = log_data.get("ts_collected")
            if ts:
                timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(tz=timezone.utc).isoformat()

            # Parse the JSON log message to extract structured fields
            raw_message = log_data.get("message", "")
            parsed = parse_log_message(raw_message)

            # Build the document to store in OpenSearch
            doc = {
                "timestamp": timestamp,              # When the log was collected
                "message": raw_message,              # Original raw message
                "service": log_data.get("service"),  # Service name from agent
                "source": log_data.get("source"),    # stdout or stderr
                "level": parsed.get("level"),        # Parsed log level (30, 40, 50, etc.)
                "event": parsed.get("event"),        # Parsed event type
                "msg": parsed.get("msg"),            # Parsed human-readable message
            }

            # Index the document in OpenSearch
            opensearch_client.index(index=INDEX_NAME, body=doc)
            indexed += 1

            # Log what we indexed for debugging
            event_type = parsed.get("event", "unknown")
            level = parsed.get("level", "?")
            print(f"Indexed [{log_data.get('service')}] level={level} event={event_type}")
        except Exception as e:
            errors.append(str(e))
            print(f"Error indexing log: {e}")

    return {"status": "ok", "indexed": indexed, "errors": errors}


# =============================================================================
# Log Search Endpoint
# =============================================================================

@app.get("/api/logs")
async def search_logs(
    q: str = "*",           # Search query (supports OpenSearch query syntax)
    size: int = 100,        # Max number of logs to return
    service: str = None,    # Filter by service name
    source: str = None,     # Filter by source (stdout/stderr)
    level: int = None,      # Filter by exact log level
    min_level: int = None,  # Filter by minimum log level (e.g., 40 = WARN and above)
    event: str = None,      # Filter by event type
):
    # Search and filter logs from OpenSearch
    # All filters are optional and can be combined
    #
    # Example: /api/logs?service=demo-app&min_level=40&size=50
    # Returns logs from demo-app with level >= 40 (WARN, ERROR, FATAL)

    # Build list of filter clauses for the OpenSearch query
    must_clauses = []

    # Free-text search across all fields
    if q and q != "*":
        must_clauses.append({"query_string": {"query": q}})

    # Exact match filters for keyword fields
    if service:
        must_clauses.append({"term": {"service": service}})

    if source:
        must_clauses.append({"term": {"source": source}})

    if level is not None:
        must_clauses.append({"term": {"level": level}})

    # Range filter for minimum log level
    if min_level is not None:
        must_clauses.append({"range": {"level": {"gte": min_level}}})

    if event:
        must_clauses.append({"term": {"event": event}})

    # Build the OpenSearch query
    query = {
        "query": {
            "bool": {
                # If no filters, match all documents
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        },
        "size": size,
        "sort": [{"timestamp": {"order": "desc"}}],  # Newest logs first
    }

    response = opensearch_client.search(index=INDEX_NAME, body=query)

    return {
        "total": response["hits"]["total"]["value"],  # Total matching logs
        "logs": [
            {"id": hit["_id"], **hit["_source"]}
            for hit in response["hits"]["hits"]
        ],  # Log documents with IDs
    }


@app.get("/api/logs/{log_id}")
async def get_log_by_id(log_id: str):
    # Retrieve a single log entry by its OpenSearch document ID
    # Returns 404 if the log is not found
    try:
        response = opensearch_client.get(index=INDEX_NAME, id=log_id)
        return {
            "id": response["_id"],
            "log": response["_source"],
        }
    except Exception:
        raise HTTPException(status_code=404, detail="Log not found")


# =============================================================================
# Metrics Endpoints - Used by Dashboard
# =============================================================================

@app.get("/api/summary")
async def get_metrics_summary():
    # Get overall summary statistics for the dashboard
    # Returns: total log count, list of services, list of sources, time range

    query = {
        "size": 0,  # Don't return actual documents, just aggregations
        "aggs": {
            "total_logs": {"value_count": {"field": "timestamp"}},   # Count all logs
            "services": {"terms": {"field": "service", "size": 50}}, # Group by service
            "sources": {"terms": {"field": "source", "size": 50}},   # Group by source
            "oldest_log": {"min": {"field": "timestamp"}},           # Earliest timestamp
            "newest_log": {"max": {"field": "timestamp"}},           # Latest timestamp
        },
    }

    response = opensearch_client.search(index=INDEX_NAME, body=query)
    aggs = response.get("aggregations", {})

    return {
        "total_logs": response["hits"]["total"]["value"],
        "services": [
            {"name": bucket["key"], "count": bucket["doc_count"]}
            for bucket in aggs.get("services", {}).get("buckets", [])
        ],
        "sources": [
            {"name": bucket["key"], "count": bucket["doc_count"]}
            for bucket in aggs.get("sources", {}).get("buckets", [])
        ],
        "time_range": {
            "oldest": aggs.get("oldest_log", {}).get("value_as_string"),
            "newest": aggs.get("newest_log", {}).get("value_as_string"),
        },
    }


@app.get("/api/metrics/timeline")
async def get_metrics_timeline(
    interval: str = "1h",    # Time bucket size (e.g., "1m", "1h", "1d")
    service: str = None,     # Optional filter by service
    source: str = None,      # Optional filter by source
):
    # Get log counts over time for timeline charts
    # Returns data points with timestamp and count for each time bucket
    #
    # Example: /api/metrics/timeline?interval=1h
    # Returns: {"interval": "1h", "data": [{"timestamp": "...", "count": 42}, ...]}

    # Build optional filters
    filters = []
    if service:
        filters.append({"term": {"service": service}})
    if source:
        filters.append({"term": {"source": source}})

    query = {
        "size": 0,  # Only return aggregations
        "query": {
            "bool": {
                "filter": filters if filters else [{"match_all": {}}]
            }
        },
        "aggs": {
            "logs_over_time": {
                "date_histogram": {
                    "field": "timestamp",
                    "fixed_interval": interval,  # Group logs into time buckets
                    "min_doc_count": 0,          # Include empty buckets
                },
            },
        },
    }

    response = opensearch_client.search(index=INDEX_NAME, body=query)
    buckets = response.get("aggregations", {}).get("logs_over_time", {}).get("buckets", [])

    return {
        "interval": interval,
        "data": [
            {"timestamp": bucket["key_as_string"], "count": bucket["doc_count"]}
            for bucket in buckets
        ],
    }


@app.get("/api/metrics/by-event")
async def get_metrics_by_event():
    # Get log counts grouped by event type
    # Used by the dashboard to show event type breakdown (e.g., http_request: 150)

    query = {
        "size": 0,
        "aggs": {
            "by_event": {
                "terms": {"field": "event", "size": 100},  # Group by event type
            },
        },
    }

    response = opensearch_client.search(index=INDEX_NAME, body=query)
    buckets = response.get("aggregations", {}).get("by_event", {}).get("buckets", [])

    return {
        "events": [
            {"event": bucket["key"], "count": bucket["doc_count"]}
            for bucket in buckets
        ],
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run the API server directly with: python logwatcher_api.py
    # In production, use: uvicorn logwatcher_api:app --host 0.0.0.0 --port 8000
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
