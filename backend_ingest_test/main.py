from fastapi import FastAPI
from typing import Any, Dict, List

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Server has started!")

@app.post("/api/ingest")
async def ingest(payload: Dict[str, Any]):
    events: List[Any] = payload.get("events", [])
    count = len(events)
    print(f"Received {count} events")
    return {"status": "ok", "received": count}