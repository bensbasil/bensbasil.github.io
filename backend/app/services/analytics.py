from prometheus_client import Histogram, Counter, Gauge, start_http_server
from typing import Dict, List
import time

class AnalyticsService:
    def __init__(self, prometheus_port: int, start_server: bool = True):
        self.port = prometheus_port
        
        self.query_duration = Histogram('rag_query_duration_seconds', 'Duration of RAG queries')
        self.queries_total = Counter('rag_queries_total', 'Total number of RAG queries')
        self.tokens_used_total = Counter('rag_tokens_used_total', 'Total tokens used by LLM')
        
        self.retrieval_quality = Gauge('rag_retrieval_quality', 'Average similarity score of retrieved chunks')
        self.api_errors_total = Counter('rag_api_errors_total', 'Total number of API errors', ['error_type'])
        
        if start_server:
            try:
                start_http_server(self.port)
            except OSError:
                pass # Already started if instantiated multiple times

    def record_query_metric(self, query: str, response_time_ms: float, tokens: int):
        self.query_duration.observe(response_time_ms / 1000.0)
        self.queries_total.inc()
        self.tokens_used_total.inc(tokens)

    def record_retrieval_quality(self, similarity_scores: List[float]):
        if similarity_scores:
            avg_score = sum(similarity_scores) / len(similarity_scores)
            self.retrieval_quality.set(avg_score)

    def record_api_error(self, error_type: str):
        self.api_errors_total.labels(error_type=error_type).inc()

    async def get_query_analytics(self, time_range: str = "24h") -> Dict:
        # Simplified simulation of data aggregation
        return {
            "total_queries": self.queries_total._value.get() if hasattr(self.queries_total, '_value') else 0,
            "avg_response_time": 0.0, # Requires tracking totals
            "avg_retrieval_quality": self.retrieval_quality._value.get() if hasattr(self.retrieval_quality, '_value') else 0.0,
            "top_searched_topics": ["oncology", "neurology", "pediatrics"],
            "error_rate": 0.0
        }
