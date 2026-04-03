# Main application module — creates and configures the FastAPI app instance.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import OPENSEARCH_HOST, OPENSEARCH_PORT
from app.db import create_index_if_not_exists
from app.routes import auth, ingest, logs, metrics, incidents

# Create the FastAPI application with a human-readable title.
app = FastAPI(title="LogWatcher API")

# Allow all origins, methods, and headers for CORS.
# Credentials (cookies/auth headers) are also permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules for each functional area of the API.
app.include_router(auth.router)
app.include_router(ingest.router)
app.include_router(logs.router)
app.include_router(metrics.router)
app.include_router(incidents.router)


# Runs once when the server starts up.
# Logs the OpenSearch connection target and ensures the required index exists.
@app.on_event("startup")
async def startup():
    print("LogWatcher API starting...")
    print(f"OpenSearch: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
    try:
        create_index_if_not_exists()
        print("OpenSearch index ready")
    except Exception as e:
        # Non-fatal: the API can still start even if OpenSearch is temporarily unavailable.
        print(f"Warning: Could not connect to OpenSearch: {e}")


# Health-check endpoint — returns a simple status payload to confirm the API is running.
@app.get("/")
def root():
    return {"status": "ok", "message": "LogWatcher API is running"}
