from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Fallback to local SQLite if Docker Postgres URL is not provided
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")

# If using Postgres, we don't need check_same_thread constraint
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
