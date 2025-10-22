def test_duplicate_conflict(client):
    r1 = client.post("/topics", json={"title": "ADR", "deadline": None})
    assert r1.status_code == 200
    r2 = client.post("/topics", json={"title": "ADR", "deadline": None})
    assert r2.status_code == 409
    assert r2.headers.get("content-type", "").startswith("application/problem+json")
