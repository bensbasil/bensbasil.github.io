from pydantic import BaseModel, EmailStr
from datetime import datetime

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
