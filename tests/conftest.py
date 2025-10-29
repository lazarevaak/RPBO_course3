"""
Глобальные фикстуры для тестов:
- Перенастраиваем БД на test-экземпляр через ENV (до импорта app.main)
- Перед КАЖДЫМ тестом очищаем таблицу topics (autouse=True)
- Добавляем корень репозитория в sys.path для стабильного импорта
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# --- Настройка окружения и sys.path ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_studyplan.db")

# --- Теперь можно импортировать приложение и БД ---
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import Topic, app  # noqa: E402


# --- Инициализация схемы и очистка данных ---
def _create_schema():
    """Гарантируем схему для тестовой БД (если ещё не создана)."""
    Base.metadata.create_all(bind=engine)


def _truncate_topics():
    """Чистим данные перед каждым тестом."""
    db = SessionLocal()
    try:
        db.query(Topic).delete()
        db.commit()
    finally:
        db.close()


# --- Автофикстура: выполняется перед каждым тестом ---
@pytest.fixture(autouse=True)
def clean_db():
    _create_schema()
    _truncate_topics()
    yield


# --- Клиент FastAPI ---
@pytest.fixture(scope="session")
def client():
    """Общий TestClient на сессию тестов."""
    with TestClient(app) as c:
        yield c
