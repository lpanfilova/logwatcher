from fastapi import FastAPI
from typing import Any, Dict, List
from contextlib import asynccontextmanager

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server has started!")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/api/ingest")
async def ingest(payload: Dict[str, Any]):
    events: List[Any] = payload.get("events", [])
    count = len(events)
    print(f"Received {count} events")
    return {"status": "ok", "received": count}