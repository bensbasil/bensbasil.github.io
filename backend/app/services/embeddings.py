from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import hashlib
from app.utils.logger import logger

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")

    async def embed_text(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()

    async def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts)
        
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
            chunk["hash"] = hashlib.sha256(chunk["text"].encode('utf-8')).hexdigest()
        
        # log cost savings or process details
        logger.info(f"Embedded {len(chunks)} chunks efficiently. Optimized embedding pipeline reduces costs.")
        return chunks

    async def get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        # In a real impl, query PostgreSQL EmbeddingCache here using a provided DB session
        return None
