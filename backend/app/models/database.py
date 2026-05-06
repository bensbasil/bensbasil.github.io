from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base
import uuid
import datetime

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id     = Column(String, nullable=False, index=True)   # Google sub / anon token / "pubmed_corpus"
    filename    = Column(String, nullable=False)
    title       = Column(String, nullable=False)
    file_path   = Column(String, nullable=True)                # Local disk path to raw PDF
    status      = Column(String, default="processed")
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)

    # ── PubMed / scraper enrichment fields ────────────────────────────────────
    source      = Column(String, default="manual")             # "manual" | "pubmed"
    pmc_id      = Column(String, nullable=True, index=True)    # e.g. "PMC8374210" (unique per paper)
    paper_title = Column(String, nullable=True)                # Full journal title from PubMed
    authors     = Column(Text, nullable=True)                  # JSON-encoded list of author names
    pub_year    = Column(Integer, nullable=True)               # Publication year
