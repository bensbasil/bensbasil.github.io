import pytest
import pytest_asyncio
from app.services.pdf_processor import PDFProcessor

@pytest.fixture
def processor():
    return PDFProcessor(embedding_model="test-model")

@pytest.mark.asyncio
async def test_chunk_text(processor):
    sample_text = "Abstract\nThis study shows X.\nMethods\nWe used Y.\nResults\nWe found Z.\nConclusion\nIt works."
    chunks = await processor.chunk_text(sample_text, "test_doc_id")
    
    # Very small text, probably going to be a single chunk in naive chunking if under token limit
    # But let's check it doesn't crash
    assert len(chunks) > 0
    assert "page" in chunks[0]
