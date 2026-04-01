from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
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

class User(Base):
    __tablename__ = "users"
 
    id             = Column(Integer, primary_key=True, index=True)
    email          = Column(String(200), unique=True, nullable=False, index=True)
    google_id      = Column(String(200), unique=True, nullable=True)
    password_hash  = Column(String(200), nullable=True)     # optional — set after Google login
    dominant_color = Column(String(20),  nullable=True)     # saved quiz result
    secondary_color= Column(String(20),  nullable=True)
    color_scores   = Column(JSON,        nullable=True)
    answer_vector  = Column(JSON,        nullable=True)
    display_name   = Column(String(200), nullable=True)     # from Google profile
    avatar_url     = Column(String(500), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())

class ModelMeta(Base):
    __tablename__ = "model_meta"

    id           = Column(Integer, primary_key=True, index=True)
    version      = Column(Integer, nullable=False)
    model_type   = Column(String(50), nullable=False) # 'primary' or 'stress'
    accuracy     = Column(Float, nullable=True)
    sample_count = Column(Integer, nullable=False)
    trained_at   = Column(DateTime(timezone=True), server_default=func.now())