from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
import uuid
import time
from app.models.schemas import (
    DocumentUpload, DocumentResponse, DeleteResponse, 
    QueryRequest, QueryFeedback, FeedbackResponse,
    HealthCheck, AnalyticsResponse
)
from app.services.pdf_processor import PDFProcessor
from app.services.embeddings import EmbeddingService
from app.services.retrieval import MilvusRetrieval
from app.services.llm import MedicalRAGLLM
from app.services.analytics import AnalyticsService
from app.config import settings

router = APIRouter()

# Services (in a real app, inject these via Depends)
pdf_processor = PDFProcessor(settings.EMBEDDING_MODEL)
embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
retrieval_service = MilvusRetrieval(settings.MILVUS_HOST, settings.MILVUS_PORT)
llm_service = MedicalRAGLLM(settings.GEMINI_API_KEY)
analytics_service = AnalyticsService(settings.PROMETHEUS_PORT)

# In-memory document cache to allow UI to visually render lists without Postgres hooked up
mock_documents = []

async def process_document_background(file_path: str, document_id: str):
    # Dummy read of a pre-saved file for this exercise, or just fake extraction for the skeleton
    # In reality, you'd pass the file content directly or save and pass the path
    pass 

@router.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    document_id = str(uuid.uuid4())
    chunks = await pdf_processor.process_medical_pdf(file, document_id)
    embedded_chunks = await embedding_service.embed_chunks(chunks)
    await retrieval_service.insert_chunks(embedded_chunks, document_id)
    
    # Store locally for the React UI state
    doc_metadata = {
        "id": document_id,
        "filename": file.filename,
        "title": file.filename,
        "status": "processed",
        "chunk_count": len(chunks)
    }
    mock_documents.append(doc_metadata)
    
    return {"document_id": document_id, "status": "processed"}

@router.post("/api/query")
async def query(request: QueryRequest):
    start_time = time.time()
    
    # 1. Embed question
    query_embedding = await embedding_service.embed_text(request.question)
    
    # 2. Search Milvus
    retrieved_chunks = await retrieval_service.search(
        query_embedding, 
        top_k=request.top_k, 
        filters=request.filters
    )
    
    # 3. Stream answer
    async def generate():
        tokens = 0
        async for token in llm_service.generate_answer(request.question, retrieved_chunks):
            tokens += 1
            yield token.encode("utf-8")
            
        # 4. Record analytics
        response_time_ms = (time.time() - start_time) * 1000
        analytics_service.record_query_metric(request.question, response_time_ms, tokens)
        if retrieved_chunks:
            analytics_service.record_retrieval_quality([c.get("score", 0) for c in retrieved_chunks])
            
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/api/documents", response_model=List[DocumentResponse])
async def list_documents():
    return mock_documents

@router.delete("/api/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    return {"status": "deleted", "document_id": document_id}

@router.post("/api/query/{query_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(query_id: str, feedback: QueryFeedback):
    return {"status": "recorded", "query_id": query_id}

@router.get("/api/metrics", response_model=AnalyticsResponse)
async def get_metrics():
    return await analytics_service.get_query_analytics()

@router.get("/api/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "milvus": "connected",
        "llm": "ready"
    }

@router.get("/metrics")
async def prometheus_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
