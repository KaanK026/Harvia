from typing import Optional, List

from pydantic import BaseModel, Field

class StartSessionRequest(BaseModel):
    sauna_type: Optional[str] = Field(default="dry")  # e.g., dry/steam/infrared

class StopSessionRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None


class SaunaRecommendationRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None  # in meters
    weight: Optional[float] = None  # in kg
    goals: Optional[List[str]] = None  # List of goal IDs


#NOT USED
class ChatMessageRequest(BaseModel):
    message: str

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="Client-managed session ID")

class ClearSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1)