from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import time
import os
import shutil

from app.models.schemas import (
    DocumentUpload, DocumentResponse, DeleteResponse,
    QueryRequest, HealthCheck
)
from app.models.database import Document
from app.models.db_session import get_db, init_db
from app.services.pdf_processor import PDFProcessor
from app.services.embeddings import EmbeddingService
from app.services.retrieval import MilvusRetrieval
from app.services.llm import MedicalRAGLLM
from app.services.analytics import AnalyticsService
from app.config import settings

router = APIRouter()

# ── Service singletons ─────────────────────────────────────────────────────────
pdf_processor = PDFProcessor(settings.EMBEDDING_MODEL)
embedding_service = None
retrieval_service = MilvusRetrieval(settings.MILVUS_DB_PATH)
llm_service = MedicalRAGLLM(settings.GEMINI_API_KEY)
analytics_service = AnalyticsService(settings.PROMETHEUS_PORT)

# Local uploads directory (alternative to S3)
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initialise the SQLite database on first import
init_db()


def get_embedding_service() -> EmbeddingService:
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService(settings.EMBEDDING_MODEL)
    return embedding_service


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default="anonymous"),
):
    document_id = str(uuid.uuid4())

    # 1. Save raw PDF to local disk
    file_bytes = await file.read()
    file_path = os.path.join(UPLOADS_DIR, f"{document_id}.pdf")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 2. Process PDF: chunk + embed + store in ChromaDB
    from io import BytesIO
    from fastapi import UploadFile as FU
    import tempfile

    tmp_path = os.path.join(UPLOADS_DIR, f"tmp_{document_id}.pdf")
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        # Re-open as UploadFile-compatible object for the processor
        with open(tmp_path, "rb") as f:
            class _FakeUpload:
                filename = file.filename
                async def read(self_inner):
                    return f.read()
            fake_file = _FakeUpload()
            chunks = await pdf_processor.process_medical_pdf(fake_file, document_id)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    emb_service = get_embedding_service()
    embedded_chunks = await emb_service.embed_chunks(chunks)
    await retrieval_service.insert_chunks(embedded_chunks, document_id, user_id=x_user_id)

    # 3. Persist metadata to SQLite
    doc = Document(
        id=document_id,
        user_id=x_user_id,
        filename=file.filename,
        title=file.filename,
        file_path=file_path,
        status="processed",
        chunk_count=len(chunks),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"document_id": document_id, "status": "processed", "chunk_count": len(chunks)}


# ── List ───────────────────────────────────────────────────────────────────────

@router.get("/api/documents", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default="anonymous"),
):
    docs = db.query(Document).filter(Document.user_id == x_user_id).all()
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "title": d.title,
            "status": d.status,
            "chunk_count": d.chunk_count,
        }
        for d in docs
    ]


# ── Delete ─────────────────────────────────────────────────────────────────────

@router.delete("/api/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default="anonymous"),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == x_user_id,
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove raw file from disk
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Remove chunks from ChromaDB
    await retrieval_service.delete_document(document_id)

    # Remove row from SQLite
    db.delete(doc)
    db.commit()

    return {"status": "deleted", "document_id": document_id}


# ── Query ──────────────────────────────────────────────────────────────────────

@router.post("/api/query")
async def query(
    request: QueryRequest,
    x_user_id: Optional[str] = Header(default="anonymous"),
):
    start_time = time.time()

    emb_service = get_embedding_service()
    query_embedding = await emb_service.embed_text(request.question)

    retrieved_chunks = await retrieval_service.search(
        query_embedding,
        top_k=request.top_k,
        filters=request.filters,
        user_id=x_user_id,
    )

    async def generate():
        tokens = 0
        try:
            async for token in llm_service.generate_answer(request.question, retrieved_chunks):
                tokens += 1
                yield token.encode("utf-8")
        except Exception as e:
            yield f"\n\n⚠️ Backend error: {str(e)}".encode("utf-8")
            return

        response_time_ms = (time.time() - start_time) * 1000
        analytics_service.record_query_metric(request.question, response_time_ms, tokens)
        if retrieved_chunks:
            analytics_service.record_retrieval_quality([c.get("score", 0) for c in retrieved_chunks])

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/api/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "milvus": "connected",
        "llm": "ready",
    }


@router.get("/metrics")
async def prometheus_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
