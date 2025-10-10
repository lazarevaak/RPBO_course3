from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_topic_format():
    """NFR-02: Проверка формата 404 ошибки"""
    response = client.get("/topics/9999")
    assert response.status_code == 404

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert isinstance(body["detail"], str)
    print("404 format OK:", body)


def test_validation_error_format():
    """NFR-02: Проверка формата 422 ошибки"""
    response = client.post("/topics", json={})
    assert response.status_code == 422

    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert isinstance(body["detail"], list)
    for err in body["detail"]:
        assert "loc" in err
        assert "msg" in err
        assert "type" in err
    print("422 format OK:", body["detail"][0])
