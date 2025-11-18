import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# -----------------------------
# DATABASE URL selection logic
# -----------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Render позволяет писать только в /var/data
    data_dir = Path("/var/data")
    data_dir.mkdir(parents=True, exist_ok=True)

    sqlite_path = data_dir / "studyplan.db"
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    print(f"[INFO] Falling back to SQLite at {sqlite_path}")


# -----------------------------
# SQLAlchemy base + engine
# -----------------------------
class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# -----------------------------
# Dependency for FastAPI
# -----------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
