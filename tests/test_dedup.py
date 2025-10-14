from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_deduplicates_by_title_deadline():
    body = {"title": "X", "deadline": "2025-12-31"}
    r1 = client.post("/topics", json=body)
    assert r1.status_code == 200, r1.text
    r2 = client.post("/topics", json=body)
    assert r2.status_code == 409
    assert "duplicate" in r2.json()["detail"].lower()
