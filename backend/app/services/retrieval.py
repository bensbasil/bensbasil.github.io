from pymilvus import MilvusClient
from typing import List, Dict, Optional
from app.utils.logger import logger
import json

class MilvusRetrieval:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.collection_name = "medical_documents"
        self.client = None

    async def connect(self) -> bool:
        try:
            # MilvusClient naturally binds to local .db files to bypass docker
            self.client = MilvusClient(uri=self.db_path)
            logger.info("Successfully connected to Milvus Lite.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus Lite: {str(e)}")
            return False

    async def create_collection(self):
        if self.client.has_collection(collection_name=self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists.")
            return
            
        self.client.create_collection(
            collection_name=self.collection_name,
            dimension=384,
            metric_type="COSINE",
            auto_id=True
        )
        logger.info(f"Created collection {self.collection_name} with Cosine similarity index.")

    async def insert_chunks(self, chunks_with_embeddings: List[Dict], document_id: str) -> List[str]:
        data = []
        for c in chunks_with_embeddings:
            data.append({
                "document_id": document_id,
                "text": c["text"],
                "vector": c["embedding"],
                "metadata": json.dumps({"page": c.get("page"), "section": c.get("section"), "keywords": c.get("keywords")})
            })
            
        res = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        return []

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[str] = None
    ) -> List[Dict]:
        
        search_res = self.client.search(
            collection_name=self.collection_name,
            data=[query_embedding],
            limit=top_k,
            filter=filters,
            output_fields=["document_id", "text", "metadata"],
            search_params={"metric_type": "COSINE"}
        )
        
        parsed_results = []
        # PyMilvus MilvusClient returns a list of results per query
        for hit in search_res[0]:
            entity = hit.get("entity", {})
            metadata_str = entity.get("metadata", "{}")
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            parsed_results.append({
                "text": entity.get("text"),
                "document_id": entity.get("document_id"),
                "score": hit.get("distance"),
                "section": metadata.get("section"),
                "page": metadata.get("page"),
                "keywords": metadata.get("keywords")
            })
                
        return parsed_results
