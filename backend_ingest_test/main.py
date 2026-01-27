from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Server has started!")

@app.post("/api/ingest")
async def ingest(events: List[dict]):
    count = len(events)
    print(f"Received {count} events")
    return {"status": "ok", "received": count}