"""
Watcher that computes rolling metrics and emits simple alerts.

This is the "monitoring" part:
- Detect repeated errors or spikes
- Emit alerts with recent sample events for context

Rules:
- If db_connection_failed count in last 60s >= 2 => alert
- If db_query_slow count in last 60s >= 3 => alert

Improvement:
- Alert deduping / cooldown
  Once an alert fires, the same alert type cannot fire again until a cooldown
  period has passed. This prevents /alerts from being flooded.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Deque, List, Dict

from schemas import LogEvent, Alert


@dataclass
class RollingCounter:
    """
    Rolling counter over a time window.

    We store timestamps of interesting events and keep only those that are still
    inside the configured window.
    """
    window_seconds: int
    items: Deque[datetime]

    def __init__(self, window_seconds: int):
        self.window_seconds = window_seconds
        self.items = deque()

    def add(self, t: datetime) -> None:
        """Add a timestamp and trim expired ones."""
        self.items.append(t)
        self._trim()

    def count(self) -> int:
        """Return how many items are currently inside the rolling window."""
        self._trim()
        return len(self.items)

    def _trim(self) -> None:
        """Remove timestamps older than the rolling window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        while self.items and self.items[0] < cutoff:
            self.items.popleft()


class Watcher:
    """
    Watches events and emits alerts based on simple rules.

    Improvements over the basic version:
    - Dedupes repeated alerts using a cooldown timer
    - Still keeps recent interesting logs for context
    """

    def __init__(self):
        # Rolling windows for alert conditions
        self.db_conn_failed = RollingCounter(window_seconds=60)
        self.db_slow = RollingCounter(window_seconds=60)

        # Keep recent "interesting" events for alert context
        self._recent_interesting: Deque[LogEvent] = deque(maxlen=200)

        # Most recent alerts kept in memory
        self.alerts: Deque[Alert] = deque(maxlen=50)

        # Deduping: remember last emit time per alert type
        self._last_alert_time: Dict[str, datetime] = {}

        # Cooldown between repeated alerts of the same type
        self.alert_cooldown_seconds = 60

    def ingest(self, e: LogEvent) -> None:
        """
        Process one new event:
        - update rolling counters
        - store interesting events for context
        - evaluate alert rules
        """
        now = datetime.now(timezone.utc)

        # Keep interesting events for context in alerts
        if e.level >= 40 or e.event in ("db_connection_failed", "db_query_slow"):
            self._recent_interesting.append(e)

        # Update counters
        if e.event == "db_connection_failed":
            self.db_conn_failed.add(now)
        elif e.event == "db_query_slow":
            self.db_slow.add(now)

        # Evaluate rules after ingesting the event
        self._maybe_alert(now)

    def _maybe_alert(self, now: datetime) -> None:
        """
        Check alert thresholds and emit alerts when rules are triggered.
        Cooldown prevents duplicate spam.
        """
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
        """
        Create an alert record unless the same alert type was emitted too recently.
        """
        last_time = self._last_alert_time.get(alert_type)

        # Deduping / cooldown check
        if last_time is not None:
            seconds_since_last = (now - last_time).total_seconds()
            if seconds_since_last < self.alert_cooldown_seconds:
                return

        # Take a sample of recent interesting events for context
        sample = list(self._recent_interesting)[-30:]

        alert = Alert(
            alert_type=alert_type,
            start_time=(now - timedelta(seconds=60)).isoformat(),
            end_time=now.isoformat(),
            summary=summary,
            sample_events=sample,
        )
        self.alerts.append(alert)
        self._last_alert_time[alert_type] = now

    def latest_alerts(self, limit: int = 10) -> List[Alert]:
        """Return the most recent alerts."""
        return list(self.alerts)[-limit:]