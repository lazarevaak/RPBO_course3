import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_topics_response_time_manual():
    durations = []
    for _ in range(50):
        start = time.perf_counter()
        response = client.get("/topics")
        elapsed = time.perf_counter() - start
        durations.append(elapsed)
        assert response.status_code == 200

    durations.sort()
    p95 = durations[int(len(durations) * 0.95) - 1]
    print(f"p95 = {p95 * 1000:.1f} ms")
    assert p95 * 1000 <= 400
