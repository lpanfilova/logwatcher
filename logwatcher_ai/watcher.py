"""
Watcher that computes rolling metrics and emits simple alerts.

This is the "monitoring" part:
- Detect repeated errors or spikes
- Emit an Alert containing a summary + a sample of recent interesting events

Rules:
- db_connection_failed count in last 60s >= 2 => alert
- db_query_slow count in last 60s >= 3 => alert
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Deque, List

from schemas import LogEvent, Alert


@dataclass
class RollingCounter:
    """
    Rolling counter over a time window.
    We store timestamps in a deque and trim out old items.
    """
    window_seconds: int
    items: Deque[datetime]

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.items = deque()

    def add(self, t: datetime) -> None:
        self.items.append(t)
        self._trim()

    def count(self) -> int:
        self._trim()
        return len(self.items)

    def _trim(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        while self.items and self.items[0] < cutoff:
            self.items.popleft()


class Watcher:
    """
    Watches events and emits alerts based on simple rules.
    """

    def __init__(self):
        self.db_conn_failed = RollingCounter(window_seconds=60)
        self.db_slow = RollingCounter(window_seconds=60)

        # Keep a sample of recent interesting events for alert context
        self._recent_interesting: Deque[LogEvent] = deque(maxlen=200)

        # Store latest alerts in memory (demo-friendly)
        self.alerts: Deque[Alert] = deque(maxlen=50)

    def ingest(self, e: LogEvent) -> None:
        """
        Ingest one event:
        - update rolling counters
        - keep interesting samples
        - check alert rules
        """
        now = datetime.now(timezone.utc)

        # Keep "interesting" logs for context in alerts
        if e.level >= 40 or e.event in ("db_connection_failed", "db_query_slow"):
            self._recent_interesting.append(e)

        # Update counters
        if e.event == "db_connection_failed":
            self.db_conn_failed.add(now)
        elif e.event == "db_query_slow":
            self.db_slow.add(now)

        # Evaluate alert rules
        self._maybe_alert()

    def _maybe_alert(self) -> None:
        """Check thresholds; if exceeded, emit alert objects."""
        now = datetime.now(timezone.utc)

        if self.db_conn_failed.count() >= 2:
            self._emit_alert(
                alert_type="DB_CONNECTION_FAILURE_SPIKE",
                summary=f"Detected {self.db_conn_failed.count()} db_connection_failed events in the last 60s",
                now=now,
            )

        if self.db_slow.count() >= 3:
            self._emit_alert(
                alert_type="DB_SLOW_QUERY_SPIKE",
                summary=f"Detected {self.db_slow.count()} db_query_slow events in the last 60s",
                now=now,
            )

    def _emit_alert(self, alert_type: str, summary: str, now: datetime) -> None:
        """Create and store an alert with recent sample logs."""
        sample = list(self._recent_interesting)[-30:]

        alert = Alert(
            alert_type=alert_type,
            start_time=(now - timedelta(seconds=60)).isoformat(),
            end_time=now.isoformat(),
            summary=summary,
            sample_events=sample,
        )
        self.alerts.append(alert)

    def latest_alerts(self, limit: int = 10) -> List[Alert]:
        """Return latest N alerts."""
        return list(self.alerts)[-limit:]
