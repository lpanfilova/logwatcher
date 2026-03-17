from fastapi import APIRouter, HTTPException
from opensearchpy import NotFoundError
from app.db import client
from app.config import INDEX_NAME

router = APIRouter()


@router.get("/api/logs")
async def search_logs(
    q: str = "*",
    size: int = 100,
    service: str = None,
    source: str = None,
    level: int = None,
    min_level: int = None,
    event: str = None,
):
    try:
        must_clauses = []

        if q and q != "*":
            must_clauses.append({"query_string": {"query": q}})

        if service and service.strip():
            must_clauses.append({
                "wildcard": {
                    "service": {
                        "value": f"*{service.strip()}*",
                        "case_insensitive": True,
                    }
                }
            })

        if source:
            must_clauses.append({"term": {"source": source}})

        if level is not None:
            must_clauses.append({"term": {"level": level}})

        if min_level is not None:
            must_clauses.append({"range": {"level": {"gte": min_level}}})

        if event:
            must_clauses.append({"term": {"event": event}})

        query = {
            "query": {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}]
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}],
        }

        response = client.search(index=INDEX_NAME, body=query)

        return {
            "total": response["hits"]["total"]["value"],
            "logs": [
                {"id": hit["_id"], **hit["_source"]}
                for hit in response["hits"]["hits"]
            ],
        }
    except Exception as e:
        print(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to search logs")


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
