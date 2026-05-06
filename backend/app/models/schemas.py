from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from fastapi import UploadFile

class DocumentUpload(BaseModel):
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    filters: Optional[Dict] = None
    conversation_history: Optional[List[Dict]] = []

class ChunkResponse(BaseModel):
    text: str
    source: str
    page: Optional[int] = None
    section: Optional[str] = None
    similarity_score: float
    keywords: Optional[List[str]] = None

class RAGResponse(BaseModel):
    query_id: str
    answer: str
    sources: List[ChunkResponse]
    confidence: float
    response_time_ms: float
    disclaimer: str = "This is not medical advice. Consult healthcare professionals."

class QueryFeedback(BaseModel):
    query_id: str
    helpful: bool
    rating: int
    notes: Optional[str] = None

class HealthCheck(BaseModel):
    status: str
    database: str
    milvus: str
    llm: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    title: str
    status: str
    chunk_count: int
    source: Optional[str] = "manual"
    pmc_id: Optional[str] = None
    paper_title: Optional[str] = None
    pub_year: Optional[int] = None

class DeleteResponse(BaseModel):
    status: str
    document_id: str

class FeedbackResponse(BaseModel):
    status: str
    query_id: str

class AnalyticsResponse(BaseModel):
    total_queries: int
    avg_response_time: float
    avg_retrieval_quality: float
    top_searched_topics: List[str]
    error_rate: float


# ── PubMed Ingestion ──────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    topic: str
    max_papers: int = 10
    user_id: str = "pubmed_corpus"

class IngestPaperResult(BaseModel):
    pmc_id: str
    title: str
    status: str          # "ingested" | "skipped" | "failed"
    chunk_count: int = 0
    reason: Optional[str] = None

class IngestStatusResponse(BaseModel):
    job_id: str
    topic: str
    status: str          # started | running | done | failed
    total: int
    completed: int
    skipped: int
    failed: int
    papers: List[IngestPaperResult] = []
    error: Optional[str] = None
    started_at: str
    finished_at: Optional[str] = None
