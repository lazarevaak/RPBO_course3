import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_logging_of_requests(caplog):
    """NFR-05: Проверка логирования всех операций /topics с уровнем INFO."""
    caplog.set_level(logging.INFO, logger="studyplan")

    client.get("/topics")
    client.post("/topics", json={"title": "Physics"})
    client.get("/topics/1")
    client.put("/topics/1/progress", json={"progress": 50})
    client.delete("/topics/1")

    logs = [record.message for record in caplog.records]

    assert any("/topics" in log for log in logs), "Нет логов для /topics"
    assert all(record.levelname == "INFO" for record in caplog.records)
    assert any("POST /topics" in log for log in logs)
    assert any("DELETE /topics/1" in log for log in logs)

    print("\n Логи INFO зафиксированы:")
    for log in logs:
        print(" ", log)
