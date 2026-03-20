from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Dict, List, Any, Optional


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

class GoogleAuthRequest(BaseModel):
    google_token: str                          # ID token from Google Sign-In
    quiz_result: Optional[Dict] = None         # attach quiz result on first login
 
class SetPasswordRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=4)
 
class SaveResultRequest(BaseModel):
    email: str
    dominant_color: str
    secondary_color: str
    color_scores: Dict[str, int]
    answer_vector: List[int]
 
class UserProfileResponse(BaseModel):
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    dominant_color: Optional[str] = None
    secondary_color: Optional[str] = None
    color_scores: Optional[Dict] = None
    has_password: bool = False
    is_new_user: bool = False
 
    class Config:
        from_attributes = True