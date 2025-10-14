from fastapi.testclient import TestClient

from app.main import MAX_BODY_BYTES, app

client = TestClient(app)


def test_body_too_large_returns_413():
    payload = "x" * (MAX_BODY_BYTES + 1)
    r = client.post(
        "/topics",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
        },
    )
    assert r.status_code == 413
    assert "too large" in r.json()["detail"].lower()
