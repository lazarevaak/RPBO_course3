from sqlalchemy import Column, Date, Integer, String

from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    deadline = Column(Date, nullable=True)
    progress = Column(Integer, default=0)
