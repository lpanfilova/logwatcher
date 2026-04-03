# Entry point for the LogWatcher API server.
# Imports the FastAPI app instance from the main application module.
from app.main import app

# Run the server directly with uvicorn when this script is executed.
# Listens on all interfaces (0.0.0.0) at port 8000.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
