from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_topic_consistency_after_deletion():
    """NFR-08: После удаления темы её нельзя получить повторно."""
    create_resp = client.post("/topics", json={"title": "Consistency Test"})
    assert create_resp.status_code == 200, "Ошибка при создании темы"
    topic_id = create_resp.json()["id"]

    get_resp = client.get(f"/topics/{topic_id}")
    assert get_resp.status_code == 200, "Созданная тема не найдена"

    del_resp = client.delete(f"/topics/{topic_id}")
    assert del_resp.status_code == 200, "Ошибка при удалении темы"
    assert del_resp.json() == {"status": "deleted"}

    get_deleted = client.get(f"/topics/{topic_id}")
    assert get_deleted.status_code == 404, "Удалённая тема всё ещё доступна"
    body = get_deleted.json()
    assert body.get("detail") in ["Topic not found", "Not Found"]

    print(f" NFR-08: Тема ID={topic_id} корректно удалена и недоступна повторно.")
