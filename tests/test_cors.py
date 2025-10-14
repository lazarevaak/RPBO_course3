# tests/test_cors.py
from fastapi.testclient import TestClient

from app.main import ALLOWED_ORIGINS, app

client = TestClient(app)


def test_preflight_rejects_unlisted_origin():
    """
    Для неподдерживаемого Origin preflight может вернуться 400 (Starlette) или 200 без ACAO.
    Важно: в ответе НЕ должно быть заголовка access-control-allow-origin.
    """
    headers = {
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/topics", headers=headers)
    assert r.status_code in (200, 400)
    # Проверяем, что браузеру нельзя будет открыть ответ — нет CORS заголовка
    assert r.headers.get("access-control-allow-origin") is None


def test_preflight_allows_listed_origin():
    """Разрешённый Origin должен получить CORS-заголовок."""
    allowed = ALLOWED_ORIGINS[0]
    headers = {
        "Origin": allowed,
        "Access-Control-Request-Method": "GET",
    }
    r = client.options("/topics", headers=headers)
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == allowed


def test_simple_get_includes_cors_header_for_allowed_origin():
    """Обычный GET с разрешённого Origin возвращает ACAO."""
    allowed = ALLOWED_ORIGINS[0]
    r = client.get("/topics", headers={"Origin": allowed})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == allowed
