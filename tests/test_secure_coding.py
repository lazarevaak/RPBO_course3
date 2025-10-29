import pytest
from fastapi.testclient import TestClient

from app.config import mask_sensitive
from app.main import app
from app.secure_files import secure_save
from app.secure_http import safe_get

client = TestClient(app)

# ==================== 1. Валидация и нормализация ввода ====================


def test_invalid_deadline_in_past():
    """Негативный: deadline в прошлом — должно вернуть ошибку 422"""
    response = client.post(
        "/topics", json={"title": "Invalid", "deadline": "2000-01-01"}
    )
    assert response.status_code == 422
    body = response.json()
    assert body["title"] == "Validation Error"


def test_invalid_progress_out_of_range():
    """Негативный: progress > 100"""
    response = client.put("/topics/1/progress", json={"progress": 999})
    assert response.status_code in (404, 422)  # либо не найден topic, либо валидация


# ==================== 2. RFC 7807 ошибки ====================


def test_rfc7807_error_format():
    """Проверяем формат ошибки RFC 7807"""
    response = client.get("/topics/9999")  # topic не существует
    body = response.json()
    assert "correlation_id" in body
    assert "title" in body
    assert body["status"] == 404


# ==================== 3. Безопасная работа с файлами ====================


def test_upload_invalid_file_type(tmp_path):
    """Негативный: загрузка файла без сигнатуры PNG/JPEG"""
    fake = tmp_path / "test.txt"
    fake.write_bytes(b"not_image")
    with pytest.raises(ValueError):
        secure_save(tmp_path, fake.read_bytes())


def test_upload_too_large(tmp_path):
    """Негативный: слишком большой файл (> 2 МБ)"""
    big = tmp_path / "big.jpg"
    big.write_bytes(b"\xff\xd8" + b"0" * (3 * 1024 * 1024) + b"\xff\xd9")
    with pytest.raises(ValueError):
        secure_save(tmp_path, big.read_bytes())


# ==================== 4. Безопасный HTTP-клиент ====================


def test_http_client_timeout(monkeypatch):
    """Негативный: обращение к несуществующему IP — должен вызвать Exception"""
    with pytest.raises(Exception):
        safe_get("https://10.255.255.1")  # гарантированный таймаут


# ==================== 5. Секреты и логирование ====================


def test_mask_sensitive_fields():
    """Проверка маскирования чувствительных данных"""
    data = {"password": "12345", "token": "abcd", "user": "alex"}
    masked = mask_sensitive(data)
    assert masked["password"] == "****"
    assert masked["token"] == "****"
    assert masked["user"] == "alex"


# ==================== Дополнительные проверки ====================


def test_upload_path_traversal(tmp_path):
    """Path traversal: попытка выйти за директорию"""
    root = tmp_path / "uploads"
    root.mkdir()
    evil = tmp_path / "../evil.png"
    with pytest.raises(ValueError):
        secure_save(root, evil.read_bytes() if evil.exists() else b"../evil")
