import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from app.utils.logger import logger
import json
import os


class MilvusRetrieval:
    """
    Vector store retrieval service backed by ChromaDB (persisted on disk).
    This is a drop-in replacement for Milvus that works on Windows, macOS, and Linux
    without Docker or any native dependencies.
    """

    def __init__(self, db_path: str):
        # db_path was originally meant for Milvus Lite; we repurpose it as the
        # directory where ChromaDB will persist its data.
        self.db_path = db_path if not db_path.endswith(".db") else os.path.splitext(db_path)[0]
        self.collection_name = "medical_documents"
        self.client = None
        self.collection = None

    async def connect(self) -> bool:
        try:
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"Successfully connected to ChromaDB at '{self.db_path}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {str(e)}")
            return False

    def _get_client(self):
        if self.client is None:
            os.makedirs(self.db_path, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self.client

    def _get_collection(self):
        if self.collection is None:
            client = self._get_client()
            # get_or_create handles both first-run and subsequent runs
            self.collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self.collection

    async def create_collection(self):
        col = self._get_collection()
        logger.info(
            f"Collection '{self.collection_name}' ready "
            f"(count={col.count()})."
        )

    async def insert_chunks(
        self, chunks_with_embeddings: List[Dict], document_id: str, user_id: str = "anonymous"
    ) -> List[str]:
        col = self._get_collection()

        ids, embeddings, documents, metadatas = [], [], [], []
        for i, c in enumerate(chunks_with_embeddings):
            chunk_id = f"{document_id}_{i}"
            ids.append(chunk_id)
            embeddings.append(c["embedding"])
            documents.append(c["text"])
            metadatas.append(
                {
                    "document_id": document_id,
                    "user_id": user_id,
                    "page": str(c.get("page") or ""),
                    "section": str(c.get("section") or ""),
                    "keywords": json.dumps(c.get("keywords") or []),
                }
            )

        col.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Inserted {len(ids)} chunks for document '{document_id}' (user: {user_id}).")
        return ids

    async def delete_document(self, document_id: str):
        col = self._get_collection()
        col.delete(where={"document_id": document_id})
        logger.info(f"Deleted document '{document_id}' from vector store.")

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        col = self._get_collection()

        # Always scope to the requesting user if provided
        where = None
        if user_id and user_id != "anonymous":
            where = {"user_id": user_id}
        elif filters:
            try:
                where = json.loads(filters)
            except Exception:
                where = None

        query_kwargs = dict(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if where:
            query_kwargs["where"] = where

        results = col.query(**query_kwargs)

        parsed_results = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            keywords_raw = meta.get("keywords", "[]")
            try:
                keywords = json.loads(keywords_raw)
            except Exception:
                keywords = []

            parsed_results.append(
                {
                    "text": doc,
                    "document_id": meta.get("document_id"),
                    "score": 1.0 - dist,
                    "section": meta.get("section") or None,
                    "page": meta.get("page") or None,
                    "keywords": keywords,
                }
            )

        return parsed_results

