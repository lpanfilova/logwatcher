from datetime import datetime, timezone
from log_store import LogStore
from schemas import LogEvent


def make_event(
    *,
    event: str = "http_request",
    level: int = 30,
    time: str | None = None,
    route: str | None = "/api/products",
    user_id: int | None = 1,
    latency_ms: int | None = None,
    duration_ms: int | None = None,
) -> LogEvent:
    if time is None:
        time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return LogEvent(
        level=level,
        time=time,
        service="demo-app",
        event=event,
        msg="test event",
        route=route,
        userId=user_id,
        latencyMs=latency_ms,
        durationMs=duration_ms,
    )


def test_add_and_count():
    store = LogStore(max_events=3)

    store.add(make_event())
    store.add(make_event(event="user_login"))

    assert store.count() == 2
    assert store.capacity() == 3


def test_recent_returns_latest_items():
    store = LogStore(max_events=5)

    store.add(make_event(event="a"))
    store.add(make_event(event="b"))
    store.add(make_event(event="c"))

    recent = store.recent(limit=2)

    assert len(recent) == 2
    assert [e.event for e in recent] == ["b", "c"]


def test_ring_buffer_keeps_only_max_events():
    store = LogStore(max_events=2)

    store.add(make_event(event="first"))
    store.add(make_event(event="second"))
    store.add(make_event(event="third"))

    recent = store.recent(limit=10)

    assert store.count() == 2
    assert [e.event for e in recent] == ["second", "third"]


def test_query_by_exact_event():
    store = LogStore()
    store.add(make_event(event="http_request"))
    store.add(make_event(event="db_query_slow", duration_ms=1500))

    result = store.query({"event": "db_query_slow"}, max_scan=100)

    assert len(result) == 1
    assert result[0].event == "db_query_slow"


def test_query_by_level_min():
    store = LogStore()
    store.add(make_event(level=30))
    store.add(make_event(level=50, event="db_connection_failed"))

    result = store.query({"level_min": 40}, max_scan=100)

    assert len(result) == 1
    assert result[0].level == 50


def test_query_by_route_contains():
    store = LogStore()
    store.add(make_event(route="/api/products"))
    store.add(make_event(route="/api/login"))

    result = store.query({"route_contains": "/login"}, max_scan=100)

    assert len(result) == 1
    assert result[0].route == "/api/login"


def test_query_by_user_id():
    store = LogStore()
    store.add(make_event(user_id=10))
    store.add(make_event(user_id=99))

    result = store.query({"userId": 99}, max_scan=100)

    assert len(result) == 1
    assert result[0].userId == 99


def test_query_by_duration_threshold():
    store = LogStore()
    store.add(make_event(event="db_query_slow", duration_ms=800))
    store.add(make_event(event="db_query_slow", duration_ms=2500))

    result = store.query({"durationMs_min": 1000}, max_scan=100)

    assert len(result) == 1
    assert result[0].durationMs == 2500


def test_query_by_latency_threshold():
    store = LogStore()
    store.add(make_event(latency_ms=100))
    store.add(make_event(latency_ms=900))

    result = store.query({"latencyMs_min": 500}, max_scan=100)

    assert len(result) == 1
    assert result[0].latencyMs == 900