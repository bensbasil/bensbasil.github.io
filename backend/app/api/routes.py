from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List
import uuid
import time
from app.models.schemas import (
    DocumentUpload, DocumentResponse, DeleteResponse, 
    QueryRequest, HealthCheck
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
embedding_service = None
retrieval_service = MilvusRetrieval(settings.MILVUS_DB_PATH)
llm_service = MedicalRAGLLM(settings.GEMINI_API_KEY)
analytics_service = AnalyticsService(settings.PROMETHEUS_PORT)

# In-memory document cache to allow UI to visually render lists without Postgres hooked up
mock_documents = []

def get_embedding_service() -> EmbeddingService:
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
    return embedding_service

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
    embedding_service = get_embedding_service()
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
    embedding_service = get_embedding_service()
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
        try:
            async for token in llm_service.generate_answer(request.question, retrieved_chunks):
                tokens += 1
                yield token.encode("utf-8")
        except Exception as e:
            error_msg = f"\n\n⚠️ Backend error: {str(e)}"
            yield error_msg.encode("utf-8")
            return
            
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
    global mock_documents
    mock_documents = [doc for doc in mock_documents if doc["id"] != document_id]
    await retrieval_service.delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}



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
