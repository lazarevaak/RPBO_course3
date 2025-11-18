import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# -----------------------------
# Select DATABASE_URL depending on environment
# -----------------------------
env = os.getenv("ENV", "local")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    print(f"[INFO] Using DATABASE_URL from environment: {DATABASE_URL}")

else:
    # ------------ CI mode ------------
    if env == "ci":
        # GitHub Actions — только локальная SQLite!
        sqlite_path = Path("./ci-test.db")
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        print(f"[INFO] CI mode: using SQLite at {sqlite_path}")

    # ------------ Render production ------------
    elif env == "prod":
        # Render позволяет писать только в /var/data/
        sqlite_path = Path("/var/data/studyplan.db")
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        print(f"[INFO] Render PROD: using SQLite at {sqlite_path}")

    # ------------ Local dev ------------
    else:
        sqlite_path = Path("./studyplan.db")
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        print(f"[INFO] Local DEV: using SQLite at {sqlite_path}")


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
