import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ----------------------------------------
# 1. Determine environment
# ----------------------------------------
env = os.getenv("ENV", "local").lower()
DATABASE_URL = os.getenv("DATABASE_URL")


# ----------------------------------------
# 2. Resolve DATABASE_URL
# ----------------------------------------
if DATABASE_URL:
    print(f"[INFO] Using DATABASE_URL from environment: {DATABASE_URL}")

else:
    if env == "ci":
        # GitHub Actions — всегда SQLite
        sqlite_path = Path("./ci-test.db")

    elif env == "prod":
        # Render Docker Web Service — единственная доступная директория
        sqlite_path = Path("/data/studyplan.db")

    else:
        # Локальная разработка
        sqlite_path = Path("./studyplan.db")

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{sqlite_path}"
    print(f"[INFO] {env.upper()} mode: using SQLite at {sqlite_path}")


# ----------------------------------------
# 3. SQLAlchemy engine + session
# ----------------------------------------
class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ----------------------------------------
# 4. FastAPI dependency
# ----------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
