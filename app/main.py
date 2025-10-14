# app/main.py
import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, constr
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ===================== БД и модели =====================
DATABASE_URL = "sqlite:///./studyplan.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Topic(Base):
    __tablename__ = "topics"
    from sqlalchemy import Column, Date, Integer, String

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    deadline = Column(Date, nullable=True)
    progress = Column(Integer, default=0)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===================== Схемы =====================
class TopicCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)
    deadline: Optional[date] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    deadline: Optional[date] = None
    progress: int

    model_config = ConfigDict(from_attributes=True)


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)


# ===================== Приложение =====================
app = FastAPI(title="Study Plan App", version="0.1.0")
Base.metadata.create_all(bind=engine)

# ---- CORS (R2) — жёсткий allowlist ----
_env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
if _env_origins:
    ALLOWED_ORIGINS = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = [
        "https://example.com",
        "https://app.mycorp.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---- Логирование + X-Request-ID (R8) ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("studyplan")
REQUEST_ID_HEADER = "X-Request-ID"


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    request.state.request_id = rid
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = rid
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        f"{request.method} {request.url.path} "
        f"rid={getattr(request.state, 'request_id', '-')}"
    )
    response = await call_next(request)
    logger.info(
        f"{request.method} {request.url.path} -> "
        f"{response.status_code} rid={getattr(request.state, 'request_id', '-')}"
    )
    return response


# ---- Лимит размера тела (R6) ----
MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB


@app.middleware("http")
async def body_size_limit_middleware(request: Request, call_next):
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
        return JSONResponse(
            status_code=413, content={"detail": "Request body too large"}
        )
    return await call_next(request)


# ---- Простейший rate-limit per-IP (R5-lite, опционально) ----
RATE_LIMIT_RPM = int(os.getenv("APP_RATE_LIMIT_RPM", "0"))  # 0 = выключено
_WINDOW = 60.0
_hits: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if RATE_LIMIT_RPM <= 0:
        return await call_next(request)
    ip = _client_ip(request)
    now = time.time()
    bucket = _hits[ip]
    while bucket and now - bucket[0] > _WINDOW:
        bucket.pop(0)
    if len(bucket) >= RATE_LIMIT_RPM:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    bucket.append(now)
    return await call_next(request)


# ---- Глобальные обработчики ошибок (аккуратный JSON) ----
def problem_json(
    status: int, title: str, detail: str | None = None, type_: str = "about:blank"
):
    return {"type": type_, "title": title, "status": status, "detail": detail}


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_json(
            exc.status_code, title="HTTP Error", detail=str(exc.detail)
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content=problem_json(
            500, title="Internal Server Error", detail="Unexpected error"
        ),
    )


# ===================== CRUD эндпоинты =====================
@app.post("/topics", response_model=TopicResponse)
def create_topic(data: TopicCreate, db: Session = Depends(get_db)):
    """Создать новую тему. Дедуп по (title, deadline) — R4."""
    existing = (
        db.query(Topic)
        .filter(and_(Topic.title == data.title, Topic.deadline == data.deadline))
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Topic duplicate")

    topic = Topic(title=data.title, deadline=data.deadline)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@app.get("/topics", response_model=list[TopicResponse])
def list_topics(db: Session = Depends(get_db)):
    """Список всех тем."""
    return db.query(Topic).all()


@app.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Получить тему по ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@app.put("/topics/{topic_id}/progress")
def update_progress(topic_id: int, data: ProgressUpdate, db: Session = Depends(get_db)):
    """Обновить прогресс темы (0..100)."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.progress = data.progress
    db.commit()
    return {"status": "ok"}


@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Удалить тему по ID."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"status": "deleted"}
