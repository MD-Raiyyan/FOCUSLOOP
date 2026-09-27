from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    sender: str  # "user" or "assistant"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AIExplanationRequest(BaseModel):
    pattern_id: Optional[str] = None
    question: Optional[str] = None


class AIExplanationResponse(BaseModel):
    title: str
    explanation: str
    deterministic_context: Dict[str, Any]
    suggested_micro_experiment: Optional[str] = None
    tone: str = "compassionate_analytical"
