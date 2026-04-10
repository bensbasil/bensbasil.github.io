import pytest
from app.services.retrieval import MilvusRetrieval

@pytest.mark.asyncio
async def test_milvus_init():
    retrieval = MilvusRetrieval("localhost", 19530)
    assert retrieval.host == "localhost"
    assert retrieval.port == "19530"
