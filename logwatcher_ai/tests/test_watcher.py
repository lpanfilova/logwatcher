from datetime import datetime, timezone, timedelta
from schemas import LogEvent
from watcher import Watcher


def make_event(event: str, level: int = 40) -> LogEvent:
    return LogEvent(
        level=level,
        time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        service="demo-app",
        event=event,
        msg="test event",
    )


def test_no_alert_before_threshold():
    watcher = Watcher()

    watcher.ingest(make_event("db_connection_failed"))

    alerts = watcher.latest_alerts()
    assert alerts == []


def test_db_connection_failure_spike_alert():
    watcher = Watcher()

    watcher.ingest(make_event("db_connection_failed"))
    watcher.ingest(make_event("db_connection_failed"))

    alerts = watcher.latest_alerts()
    assert len(alerts) == 1
    assert alerts[0].alert_type == "DB_CONNECTION_FAILURE_SPIKE"


def test_db_slow_query_spike_alert():
    watcher = Watcher()

    watcher.ingest(make_event("db_query_slow"))
    watcher.ingest(make_event("db_query_slow"))
    watcher.ingest(make_event("db_query_slow"))

    alerts = watcher.latest_alerts()
    assert len(alerts) == 1
    assert alerts[0].alert_type == "DB_SLOW_QUERY_SPIKE"


def test_alert_cooldown_prevents_duplicates():
    watcher = Watcher()

    watcher.ingest(make_event("db_connection_failed"))
    watcher.ingest(make_event("db_connection_failed"))
    first_alert_count = len(watcher.latest_alerts())

    watcher.ingest(make_event("db_connection_failed"))
    watcher.ingest(make_event("db_connection_failed"))
    second_alert_count = len(watcher.latest_alerts())

    assert first_alert_count == 1
    assert second_alert_count == 1


def test_alert_can_fire_again_after_cooldown():
    watcher = Watcher()

    watcher.ingest(make_event("db_connection_failed"))
    watcher.ingest(make_event("db_connection_failed"))
    assert len(watcher.latest_alerts()) == 1

    watcher._last_alert_time["DB_CONNECTION_FAILURE_SPIKE"] = (
        datetime.now(timezone.utc) - timedelta(seconds=watcher.alert_cooldown_seconds + 1)
    )

    watcher.ingest(make_event("db_connection_failed"))
    watcher.ingest(make_event("db_connection_failed"))

    assert len(watcher.latest_alerts()) == 2


def test_interesting_events_are_kept_for_alert_context():
    watcher = Watcher()

    watcher.ingest(make_event("db_query_slow"))
    watcher.ingest(make_event("db_query_slow"))
    watcher.ingest(make_event("db_query_slow"))

    alert = watcher.latest_alerts()[0]
    assert len(alert.sample_events) >= 3
    assert all(e.event == "db_query_slow" for e in alert.sample_events[-3:])