from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.topic import Topic
from app.schemas.topic import ProgressUpdate, TopicCreate, TopicResponse

app = FastAPI(title="Study Plan App", version="0.1.0")

Base.metadata.create_all(bind=engine)


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
    return {"status": "deleted"}
