from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ProcrastinationEventBase(BaseModel):
    task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    user_confirmed: bool = True
    trigger_reason: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ProcrastinationEventCreate(ProcrastinationEventBase):
    user_id: Optional[str] = None


class ProcrastinationEventEnd(BaseModel):
    ended_at: Optional[datetime] = None
    trigger_reason: Optional[str] = None
    notes: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class ProcrastinationEventResponse(ProcrastinationEventBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
