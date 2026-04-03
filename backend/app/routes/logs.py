# Logs routes — endpoints for searching and retrieving individual log documents.
from fastapi import APIRouter, HTTPException
from opensearchpy import NotFoundError
from app.db import client
from app.config import INDEX_NAME

router = APIRouter()


# Searches logs with optional full-text query and field-level filters.
# All active filters are combined with AND logic via OpenSearch bool/must.
# Results are sorted newest-first and capped at `size` documents.
@router.get("/api/logs")
async def search_logs(
    q: str = "*",         # Full-text query string; "*" matches all documents.
    size: int = 100,      # Maximum number of results to return.
    service: str = None,
    source: str = None,
    level: int = None,    # Exact numeric log level match.
    min_level: int = None,  # Minimum numeric log level (inclusive).
    event: str = None,
):
    try:
        must_clauses = []

        # Only apply the full-text query when it is not the catch-all wildcard.
        if q and q != "*":
            must_clauses.append({"query_string": {"query": q}})

        # Case-insensitive substring match on service name using a wildcard query.
        if service and service.strip():
            must_clauses.append({
                "wildcard": {
                    "service": {
                        "value": f"*{service.strip()}*",
                        "case_insensitive": True,
                    }
                }
            })

        # Exact keyword match on source — no partial matching.
        if source:
            must_clauses.append({"term": {"source": source}})

        # Exact match on a specific numeric log level.
        if level is not None:
            must_clauses.append({"term": {"level": level}})

        # Range filter to include logs at or above a minimum severity level.
        if min_level is not None:
            must_clauses.append({"range": {"level": {"gte": min_level}}})

        # Exact keyword match on the structured event name.
        if event:
            must_clauses.append({"term": {"event": event}})

        query = {
            "query": {
                "bool": {
                    # Fall back to match_all when no filters are specified.
                    "must": must_clauses if must_clauses else [{"match_all": {}}]
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}],  # Newest logs first.
        }

        response = client.search(index=INDEX_NAME, body=query)

        return {
            "total": response["hits"]["total"]["value"],
            # Merge the OpenSearch document ID into each log source object.
            "logs": [
                {"id": hit["_id"], **hit["_source"]}
                for hit in response["hits"]["hits"]
            ],
        }
    except Exception as e:
        print(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search logs")


# Fetches a single log document by its OpenSearch document ID.
# Returns 404 if no document with that ID exists in the index.
@router.get("/api/logs/{log_id}")
async def get_log_by_id(log_id: str):
    try:
        response = client.get(index=INDEX_NAME, id=log_id)
        return {"id": response["_id"], "log": response["_source"]}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Log not found")
    except Exception as e:
        print(f"Error retrieving log {log_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve log")
