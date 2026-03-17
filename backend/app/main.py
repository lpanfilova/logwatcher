from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import OPENSEARCH_HOST, OPENSEARCH_PORT
from app.db import create_index_if_not_exists
from app.routes import auth, ingest, logs, metrics, incidents

app = FastAPI(title="LogWatcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(logs.router)
app.include_router(metrics.router)
app.include_router(incidents.router)


@app.on_event("startup")
async def startup():
    print("LogWatcher API starting...")
    print(f"OpenSearch: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
    try:
        create_index_if_not_exists()
        print("OpenSearch index ready")
    except Exception as e:
        print(f"Warning: Could not connect to OpenSearch: {e}")


@app.get("/")
def root():
    return {"status": "ok", "message": "LogWatcher API is running"}
