from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(100), nullable=False)
    message    = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id             = Column(Integer, primary_key=True, index=True)
    session_id     = Column(String(36), nullable=False)
    answers        = Column(JSON, nullable=False)
    color_scores   = Column(JSON, nullable=False)
    dominant_color = Column(String(20), nullable=False)
    secondary_color= Column(String(20), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())