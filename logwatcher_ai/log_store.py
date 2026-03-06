"""
In-memory storage for recent logs + simple querying.

- Keeps last max_events in a deque (ring buffer)
- Allows basic filtering (event type, level, route substring, userId, time window, thresholds)
"""

from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Deque, List, Optional, Dict, Any

from schemas import LogEvent


def _parse_iso(ts: str) -> datetime:
    """
    Convert ISO timestamp string to datetime.

    Your logs use a trailing 'Z' (UTC), e.g. '2026-02-06T00:49:06.388Z'.
    Python's fromisoformat expects '+00:00' instead of 'Z'.
    """
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


class LogStore:
    """
    Stores a rolling window of log events in memory.

    """

    def __init__(self, max_events: int = 100000):
        self._events: Deque[LogEvent] = deque(maxlen=max_events)

    def add(self, event: LogEvent) -> None:
        """Add a parsed log event to the store."""
        self._events.append(event)

    def recent(self, limit: int = 200) -> List[LogEvent]:
        """Return the most recent N events."""
        return list(self._events)[-limit:]

    def count(self) -> int:
        """Return how many events are currently stored."""
        return len(self._events)

    def capacity(self) -> int:
        """Return the max number of events the store can hold."""
        return self._events.maxlen or 0

    def query(self, filt: Dict[str, Any], max_scan: int = 2000) -> List[LogEvent]:
        """
        Query recent logs using a simple filter dict.

        Supported keys (all optional):
          - event: exact match (e.g. "db_connection_failed")
          - level_min: include logs with level >= this
          - route_contains: substring match in route
          - userId: exact match
          - since_minutes: only include logs newer than now - since_minutes
          - durationMs_min: numeric threshold
          - latencyMs_min: numeric threshold

        max_scan limits how many of the most recent logs we scan (performance).
        """
        since_minutes = filt.get("since_minutes")
        cutoff: Optional[datetime] = None
        if isinstance(since_minutes, (int, float)) and since_minutes > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=float(since_minutes))

        event_exact = filt.get("event")
        level_min = filt.get("level_min")
        route_contains = filt.get("route_contains")
        user_id = filt.get("userId")
        duration_min = filt.get("durationMs_min")
        latency_min = filt.get("latencyMs_min")

        # Only scan last max_scan logs to keep it fast
        events = list(self._events)[-max_scan:]

        out: List[LogEvent] = []
        for e in events:
            # Time window filter
            if cutoff is not None:
                try:
                    t = _parse_iso(e.time)
                    if t < cutoff:
                        continue
                except Exception:
                    pass

            # Exact event filter
            if event_exact and e.event != event_exact:
                continue

            # Severity filter
            if level_min is not None and e.level < int(level_min):
                continue

            # Route substring filter
            if route_contains:
                if not e.route or route_contains not in e.route:
                    continue

            # userId filter
            if user_id is not None and e.userId != int(user_id):
                continue

            # Duration threshold
            if duration_min is not None:
                if e.durationMs is None or e.durationMs < int(duration_min):
                    continue

            # Latency threshold
            if latency_min is not None:
                if e.latencyMs is None or e.latencyMs < int(latency_min):
                    continue

            out.append(e)

        return out
