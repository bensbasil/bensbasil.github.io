"""
SQLAlchemy engine and session factory for the Medical RAG SQLite database.
The database file (rag.db) is created automatically on first startup.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base

# SQLite file stored next to wherever uvicorn is launched from (the backend/ dir)
DATABASE_URL = "sqlite:///./rag.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables if they don't exist. Called at application startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a database session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
