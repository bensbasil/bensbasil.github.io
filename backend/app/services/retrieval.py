from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from typing import List, Dict, Optional
from app.utils.logger import logger
import json

class MilvusRetrieval:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = str(port)
        self.collection_name = "medical_documents"

    async def connect(self) -> bool:
        try:
            connections.connect("default", host=self.host, port=self.port)
            logger.info("Successfully connected to Milvus.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            return False

    async def create_collection(self):
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists.")
            return

        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
        ]
        
        schema = CollectionSchema(fields, description="Medical RAG chunks collection")
        collection = Collection(name=self.collection_name, schema=schema)
        
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        logger.info(f"Created collection {self.collection_name} with Cosine similarity index.")

    async def insert_chunks(self, chunks_with_embeddings: List[Dict], document_id: str) -> List[str]:
        collection = Collection(self.collection_name)
        
        entities = [
            [document_id] * len(chunks_with_embeddings),  # document_id
            [c["text"] for c in chunks_with_embeddings],  # text
            [c["embedding"] for c in chunks_with_embeddings], # embedding
            [json.dumps({"page": c.get("page"), "section": c.get("section"), "keywords": c.get("keywords")}) for c in chunks_with_embeddings] # metadata
        ]
        
        insert_result = collection.insert(entities)
        collection.flush()
        return [str(pk) for pk in insert_result.primary_keys]

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[str] = None # Assuming Milvus boolean expression for filter
    ) -> List[Dict]:
        collection = Collection(self.collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filters,
            output_fields=["document_id", "text", "metadata"]
        )
        
        parsed_results = []
        for hits in results:
            for hit in hits:
                metadata = json.loads(hit.entity.get("metadata"))
                parsed_results.append({
                    "text": hit.entity.get("text"),
                    "document_id": hit.entity.get("document_id"),
                    "score": hit.distance,
                    "section": metadata.get("section"),
                    "page": metadata.get("page"),
                    "keywords": metadata.get("keywords")
                })
        return parsed_results
