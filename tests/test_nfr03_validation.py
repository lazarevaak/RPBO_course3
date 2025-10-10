from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_topic_without_title():
    """NFR-03: title обязателен (должна быть 422 ошибка)."""
    response = client.post("/topics", json={})
    assert response.status_code == 422

    body = response.json()
    assert "detail" in body
    assert any(
        "title" in str(err.get("loc", [])) for err in body["detail"]
    ), "Ошибка должна указывать на отсутствующее поле title"


def test_progress_out_of_range():
    """NFR-03: progress должен быть в диапазоне 0..100."""
    topic = client.post("/topics", json={"title": "Math"}).json()
    topic_id = topic["id"]

    bad_values = [-1, 150]

    for value in bad_values:
        r = client.put(f"/topics/{topic_id}/progress", json={"progress": value})
        assert r.status_code == 422, f"Ожидалась ошибка при progress={value}"

        body = r.json()
        assert "detail" in body
        assert any(
            any(
                kw in err["msg"].lower()
                for kw in ["ensure", "greater", "less", "between"]
            )
            for err in body["detail"]
        ), f"Текст ошибки не соответствует ожиданию при progress={value}"
