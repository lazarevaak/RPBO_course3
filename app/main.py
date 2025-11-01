# app/main.py
from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Awaitable, Callable

import sqlalchemy as sa
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.config import mask_sensitive
from app.database import Base, engine, get_db
from app.schemas.topic import ProgressUpdate, TopicCreate, TopicResponse
from app.secure_files import secure_save
from app.utils.errors import problem_json


# ===================== Модель БД =====================
class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        sa.UniqueConstraint("title", "deadline", name="uq_title_deadline"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    deadline: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    progress: Mapped[int] = mapped_column(default=0)


Base.metadata.create_all(bind=engine)


# ===================== Приложение =====================
app = FastAPI(title="Study Plan App", version="0.1.0")

# ---- CORS (ADR-002) ----
_env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS: list[str] = [
    o.strip() for o in _env_origins.split(",") if o.strip()
] or [
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
async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    rid = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    request.state.request_id = rid
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = rid
    return response


# ---- Лимит размера тела (ADR-003) ----
MAX_BODY_BYTES: int = int(os.getenv("APP_MAX_BODY_BYTES", str(2 * 1024 * 1024)))


@app.middleware("http")
async def body_size_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content=problem_json(
                request,
                413,
                "Payload Too Large",
                detail=f"Payload too large: request body exceeds {MAX_BODY_BYTES} bytes",
            ),
            media_type="application/problem+json",
        )
    return await call_next(request)


# ---- Простейший rate-limit per-IP (ADR-003) ----
RATE_LIMIT_RPM: int = int(os.getenv("APP_RATE_LIMIT_RPM", "0"))  # 0 = выключено
_WINDOW = 60.0
_hits: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if RATE_LIMIT_RPM <= 0:
        return await call_next(request)

    ip = _client_ip(request)
    now = time.time()
    bucket = _hits[ip]
    while bucket and now - bucket[0] > _WINDOW:
        bucket.pop(0)

    if len(bucket) >= RATE_LIMIT_RPM:
        return JSONResponse(
            status_code=429,
            content=problem_json(
                request,
                429,
                "Too Many Requests",
                detail=f"Rate limit {RATE_LIMIT_RPM}/min exceeded",
            ),
            media_type="application/problem+json",
        )

    bucket.append(now)
    return await call_next(request)


# ---- Глобальные обработчики ошибок (ADR-001) ----
@app.exception_handler(RequestValidationError)
async def validation_exc_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    def normalize_detail(value: object) -> object:
        if isinstance(value, Exception):
            return str(value)
        if isinstance(value, list):
            return [normalize_detail(v) for v in value]
        if isinstance(value, dict):
            return {k: normalize_detail(v) for k, v in value.items()}
        return value

    safe_errors = normalize_detail(exc.errors())

    content = problem_json(
        request,
        422,
        "Validation Error",
        detail=safe_errors,
        type_="https://example.com/errors/validation",
    )
    content["errors"] = safe_errors
    return JSONResponse(
        status_code=422,
        content=content,
        media_type="application/problem+json",
    )


@app.exception_handler(Exception)
async def unhandled_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")

    def normalize_detail(value: object) -> str | object:
        return str(value) if isinstance(value, Exception) else value

    safe_detail = normalize_detail(exc)
    return JSONResponse(
        status_code=500,
        content=problem_json(request, 500, "Internal Server Error", safe_detail),
        media_type="application/problem+json",
    )


# ===================== CRUD эндпоинты =====================
@app.post("/topics", response_model=TopicResponse)
def create_topic(data: TopicCreate, db: Session = Depends(get_db)) -> TopicResponse:
    # 🔒 Доп. доменная валидация
    if data.deadline and data.deadline < date.today():
        raise HTTPException(status_code=422, detail="Deadline cannot be in the past")

    existing = (
        db.query(Topic)
        .filter(sa.and_(Topic.title == data.title, Topic.deadline == data.deadline))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Topic duplicate")

    topic = Topic(title=data.title, deadline=data.deadline)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicResponse.model_validate(topic)


@app.get("/topics", response_model=list[TopicResponse])
def list_topics(db: Session = Depends(get_db)) -> list[TopicResponse]:
    rows = db.query(Topic).all()
    return [TopicResponse.model_validate(r) for r in rows]


@app.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)) -> TopicResponse:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicResponse.model_validate(topic)


@app.put("/topics/{topic_id}/progress")
def update_progress(
    topic_id: int, data: ProgressUpdate, db: Session = Depends(get_db)
) -> dict[str, str]:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.progress = data.progress
    db.commit()
    return {"status": "ok"}


@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"status": "deleted"}


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 422:
        return JSONResponse(
            status_code=422,
            content=problem_json(
                request,
                422,
                "Validation Error",
                detail=str(exc.detail),
                type_="https://example.com/errors/validation",
            ),
            media_type="application/problem+json",
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem_json(request, exc.status_code, "HTTP Error", str(exc.detail)),
        media_type="application/problem+json",
    )


# ===================== Upload (secure files) =====================
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    data = await file.read()
    try:
        path = secure_save(UPLOAD_DIR, data)
        return {"status": "ok", "path": str(path.name)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---- Логирование запроса/ответа (с маскированием) ----
@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    safe_body = mask_sensitive(body if isinstance(body, dict) else {})
    logger.info("Request %s %s body=%s", request.method, request.url.path, safe_body)
    response = await call_next(request)
    logger.info(
        "Response %s %s -> %s", request.method, request.url.path, response.status_code
    )
    return response
