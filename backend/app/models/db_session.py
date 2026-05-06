"""
SQLAlchemy engine and session factory for the Medical RAG SQLite database.
The database file (rag.db) is created automatically on first startup.
"""
from sqlalchemy import create_engine, text
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
    """Create all tables if they don't exist, and auto-migrate new columns."""
    Base.metadata.create_all(bind=engine)
    
    # ── Auto-Migration ────────────────────────────────────────────────────────
    # SQLite create_all() ignores existing tables, so we must add new columns manually.
    # We wrap each in a try/except because it will fail gracefully if the column already exists.
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN source VARCHAR DEFAULT 'manual'"))
            conn.commit()
    except Exception: pass

    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN pmc_id VARCHAR"))
            conn.commit()
    except Exception: pass

    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN paper_title VARCHAR"))
            conn.commit()
    except Exception: pass

    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN authors TEXT"))
            conn.commit()
    except Exception: pass

    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN pub_year INTEGER"))
            conn.commit()
    except Exception: pass


def get_db():
    """FastAPI dependency — yields a database session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
