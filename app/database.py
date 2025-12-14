import logging
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

env = os.getenv("ENV", "local").lower()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

if DATABASE_URL:
    logger.info("Using DATABASE_URL from environment")

else:
    if env in {"ci", "test"}:
        sqlite_path = Path("./test_studyplan.db")

    elif env in {"prod", "production"}:
        sqlite_path = Path("/app/db/studyplan.db")

    else:
        sqlite_path = Path("./studyplan.db")

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    logger.info("Using SQLite database at %s", sqlite_path)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
