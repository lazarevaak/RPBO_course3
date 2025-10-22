"""
Глобальные фикстуры для тестов:
- Перенастраиваем БД на test-экземпляр через ENV (до импорта app.main)
- Перед КАЖДЫМ тестом очищаем таблицу topics (autouse=True)
- Добавляем корень репозитория в sys.path для стабильного импорта
"""

import os
import sys
from pathlib import Path

# 1) sys.path на корень, чтобы `import app.main` работал одинаково из любых тестов
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 2) Тестовая БД — ВАЖНО: выставляем до импорта app.main
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_studyplan.db")

# Теперь можно импортировать объекты из приложения
from app.main import Base, SessionLocal, Topic, engine  # noqa: E402


def _create_schema():
    """Гарантируем схему для тестовой БД (если ещё не создана)."""
    Base.metadata.create_all(bind=engine)


def _truncate_topics():
    """Чистим данные перед каждым тестом (чтобы не ловить дубликаты из прошлых тестов)."""
    db = SessionLocal()
    try:
        db.query(Topic).delete()
        db.commit()
    finally:
        db.close()


# 3) Авто-фикстура: выполняется перед КАЖДЫМ тестом
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    _create_schema()
    _truncate_topics()
    yield


# 4) Клиент FastAPI для тестов
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Общий TestClient на сессию тестов."""
    with TestClient(app) as c:
        yield c
