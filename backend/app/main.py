from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import routes
from app.services.retrieval import MilvusRetrieval
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database, Milvus, embeddings model
    retrieval_service = MilvusRetrieval(settings.MILVUS_DB_PATH)
    await retrieval_service.connect()
    await retrieval_service.create_collection()
    yield
    # Shutdown logic

app = FastAPI(
    title="Medical RAG System",
    description="Ask questions about medical literature",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
