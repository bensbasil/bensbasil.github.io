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
