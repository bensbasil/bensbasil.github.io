from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=False)
    source = Column(String, nullable=True)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False)
    text = Column(String, nullable=False)
    page = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    vector_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Query(Base):
    __tablename__ = "queries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    sources_used = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    tokens_used = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    user_feedback = Column(Boolean, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text_hash = Column(String, unique=True, index=True, nullable=False)
    embedding = Column(ARRAY(Float), nullable=False)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
