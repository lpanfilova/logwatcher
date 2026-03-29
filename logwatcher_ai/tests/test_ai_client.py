import ai_client


def test_build_filter_from_question_fallback_on_bad_json(monkeypatch):
    monkeypatch.setattr(ai_client, "_chat", lambda *args, **kwargs: "not-json")

    result = ai_client.build_filter_from_question("show me errors")

    assert result == {"since_minutes": 10, "level_min": 40}


def test_build_filter_from_question_adds_default_since_minutes(monkeypatch):
    monkeypatch.setattr(
        ai_client,
        "_chat",
        lambda *args, **kwargs: '{"event": "db_query_slow"}',
    )

    result = ai_client.build_filter_from_question("show slow queries")

    assert result["event"] == "db_query_slow"
    assert result["since_minutes"] == 10


def test_explain_results_uses_chat(monkeypatch):
    monkeypatch.setattr(ai_client, "_chat", lambda *args, **kwargs: "Mocked explanation")

    result = ai_client.explain_results(
        "what happened?",
        {"since_minutes": 10},
        [],
    )

    assert result == "Mocked explanation"