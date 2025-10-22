import app.main as appmod


def test_limits_payload_and_rate_limit(client, monkeypatch):
    # 413 — большой JSON
    huge = "x" * (2 * 1024 * 1024 + 10)
    r = client.post("/topics", json={"title": huge})
    assert r.status_code == 413
    assert r.headers.get("content-type", "").startswith("application/problem+json")

    # 429 — включаем лимит на лету
    monkeypatch.setattr(appmod, "RATE_LIMIT_RPM", 1)
    assert client.get("/topics").status_code == 200
    too_many = client.get("/topics")
    assert too_many.status_code == 429
    assert too_many.headers.get("content-type", "").startswith(
        "application/problem+json"
    )
    # вернуть обратно
    monkeypatch.setattr(appmod, "RATE_LIMIT_RPM", 0)
