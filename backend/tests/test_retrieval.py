import pytest
from app.services.retrieval import MilvusRetrieval

@pytest.mark.asyncio
async def test_milvus_init():
    retrieval = MilvusRetrieval("./test_milvus.db")
    assert retrieval.db_path == "./test_milvus.db"
