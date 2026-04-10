import pytest
from app.services.retrieval import MilvusRetrieval

@pytest.mark.asyncio
async def test_milvus_init():
    retrieval = MilvusRetrieval("http://localhost:19530")
    assert retrieval.db_path == "http://localhost:19530"
