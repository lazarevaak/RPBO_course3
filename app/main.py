# app/main.py
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.topic import Topic
from app.schemas.topic import ProgressUpdate, TopicCreate, TopicResponse

# === инициализация приложения ===
app = FastAPI(title="Study Plan App", version="0.1.0")

# создаём таблицы, если их нет
Base.metadata.create_all(bind=engine)

# === настройка логирования (NFR-05) ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("studyplan")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех запросов к /topics."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


# === CRUD эндпоинты ===


@app.post("/topics", response_model=TopicResponse)
def create_topic(data: TopicCreate, db: Session = Depends(get_db)):
    """Создать новую тему."""
    topic = Topic(title=data.title, deadline=data.deadline)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@app.get("/topics", response_model=list[TopicResponse])
def list_topics(db: Session = Depends(get_db)):
    """Получить список всех тем."""
    return db.query(Topic).all()


@app.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Получить одну тему по ID."""
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
