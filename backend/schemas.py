from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Dict, List, Any


# ── existing contact schemas ────────────────────────────────────────────────

class ContactSubmissionCreate(BaseModel):
    name: str
    email: EmailStr
    message: str


class ContactSubmissionResponse(BaseModel):
    id: int
    name: str
    email: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── quiz schemas ─────────────────────────────────────────────────────────────

class QuizSubmitRequest(BaseModel):
    session_id: str = Field(..., min_length=36, max_length=36)
    answers: List[int] = Field(..., min_length=10, max_length=15)
    color_scores: Dict[str, int]
    dominant_color: str
    secondary_color: str


class QuizSubmitResponse(BaseModel):
    success: bool
    message: str
    session_id: str


class ColorDistribution(BaseModel):
    red: int
    yellow: int
    green: int
    blue: int
    total: int


class ClusterPoint(BaseModel):
    x: float
    y: float
    cluster: int
    dominant_color: str
    is_current_user: bool = False


class CorrelationData(BaseModel):
    question_index: int
    red: float
    yellow: float
    green: float
    blue: float


class AnalyticsResponse(BaseModel):
    total_responses: int
    color_distribution: ColorDistribution
    cluster_points: List[ClusterPoint]
    correlation_data: List[CorrelationData]
    model_trained: bool
    most_common_combination: str
    rarest_color: str