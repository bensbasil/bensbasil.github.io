import pytest
from app.services.llm import MedicalRAGLLM

def test_parse_citations():
    llm = MedicalRAGLLM("test_key")
    response_text = """
    This is an answer.
    SOURCES CITED:
    - Document 1: "quote" (Relevance: 95%, Page: 3)
    CONFIDENCE: 92%
    """
    citations = llm.parse_citations(response_text)
    assert len(citations) > 0
    assert "Document 1" in citations[0]["reference"]
