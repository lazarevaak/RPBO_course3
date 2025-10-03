from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, constr
from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

app = FastAPI(title="Study Plan App", version="0.1.0")

# --- Database setup ---
DATABASE_URL = "sqlite:///./studyplan.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    deadline = Column(Date, nullable=True)
    progress = Column(Integer, default=0)  # 0..100


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Schemas ---


class TopicCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=1)  # нельзя пустую строку
    deadline: Optional[date] = None


class TopicResponse(BaseModel):
    id: int
    title: str
    deadline: Optional[date] = None
    progress: int

    class Config:
        orm_mode = True


class ProgressUpdate(BaseModel):
    progress: int = Field(..., ge=0, le=100)  # проверка диапазона 0..100


# --- Endpoints ---


@app.post("/topics", response_model=TopicResponse)
def create_topic(data: TopicCreate, db: Session = Depends(get_db)):
    topic = Topic(title=data.title, deadline=data.deadline)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@app.get("/topics", response_model=list[TopicResponse])
def list_topics(db: Session = Depends(get_db)):
    return db.query(Topic).all()


@app.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@app.put("/topics/{topic_id}/progress")
def update_progress(topic_id: int, data: ProgressUpdate, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    topic.progress = data.progress
    db.commit()
    return {"status": "ok"}


@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return {"status": "deleted."}
