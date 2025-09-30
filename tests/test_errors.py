from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_topic():
    # id заведомо несуществующий
    r = client.get("/topics/9999")
    assert r.status_code == 404
    body = r.json()
    # fastapi по умолчанию возвращает {"detail": "..."}
    assert "detail" in body
    assert body["detail"] in ["Not Found", "Topic not found"]


def test_validation_error():
    # title обязательный -> если не передать, будет 422
    r = client.post("/topics")
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body
    # в detail должен быть список ошибок валидации
    assert isinstance(body["detail"], list)
    assert any(
        err["type"] == "missing" or "field required" in err["msg"].lower()
        for err in body["detail"]
    )
