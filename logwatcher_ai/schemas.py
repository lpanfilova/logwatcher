"""
Pydantic models (schemas) for:
- Parsed log lines (LogEvent)
- API request/response for /ask
- Alerts emitted by the watcher
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class LogEvent(BaseModel):
    """
    Represents one JSON log line.

    Example:
    {
      "level": 30,
      "time": "2026-02-06T00:49:06.388Z",
      "service": "demo-app",
      "event": "http_request",
      "route": "/api/products",
      "statusCode": 200,
      ...
    }
    """
    level: int
    time: str           # ISO timestamp string
    service: str
    event: str
    msg: Optional[str] = None

    # Common optional fields (vary by event)
    userId: Optional[int] = None
    route: Optional[str] = None
    method: Optional[str] = None
    statusCode: Optional[int] = None
    latencyMs: Optional[int] = None

    # DB-related fields
    component: Optional[str] = None
    queryName: Optional[str] = None
    durationMs: Optional[int] = None

    # Auth-related fields
    authProvider: Optional[str] = None

    # Error-related fields
    errorCode: Optional[str] = None
    dbHost: Optional[str] = None
    dbPort: Optional[int] = None

    # Nested error object if present
    err: Optional[Dict[str, Any]] = None


class AskRequest(BaseModel):
    """
    Request body for POST /ask.

    question:  Something like:
      "Show DB errors in last 5 minutes"
    max_logs: Limits how many recent logs we scan (performance + cost control).
    """
    question: str = Field(..., examples=["Summarize errors in the last 5 minutes"])
    max_logs: int = Field(200, ge=10, le=2000)


class AskResponse(BaseModel):
    """
    Response for POST /ask:
    - filter_used: The structured filter the AI (or fallback) produced
    - matched_count: How many logs matched
    - answer: The AI explanation based ONLY on matched logs
    """
    filter_used: Dict[str, Any]
    matched_count: int
    answer: str


class Alert(BaseModel):
    """
    A simple alert produced by watcher rules.
    Includes a small sample of recent "interesting" events for context.
    """
    alert_type: str
    start_time: str
    end_time: str
    summary: str
    sample_events: List[LogEvent]
