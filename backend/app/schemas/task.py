from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


VALID_FREQUENCIES = {"once", "daily"}


def normalize_frequency(val: Optional[str]) -> Optional[str]:
    if val is None:
        return "daily"
    clean = str(val).strip().lower()
    if clean in ("one_time", "one-time", "single"):
        return "once"
    if clean not in VALID_FREQUENCIES:
        raise ValueError(f"Invalid frequency '{val}'. Allowed values are 'once' (one-time) or 'daily'.")
    return clean


class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = "Focus"
    planned_time: Optional[str] = "09:00"  # HH:MM
    target_duration_minutes: Optional[str] = "30"
    frequency: Optional[str] = "daily"
    active: Optional[bool] = True

    @field_validator("frequency", mode="before")
    @classmethod
    def validate_frequency(cls, v):
        return normalize_frequency(v)


class TaskCreate(TaskBase):
    user_id: Optional[str] = None  # Can be passed in body or extracted from user session


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    planned_time: Optional[str] = None
    target_duration_minutes: Optional[str] = None
    frequency: Optional[str] = None
    active: Optional[bool] = None

    @field_validator("frequency", mode="before")
    @classmethod
    def validate_frequency(cls, v):
        if v is None:
            return None
        return normalize_frequency(v)


class TaskResponse(TaskBase):
    id: str
    user_id: str
    frequency: str = "daily"
    today_status: Optional[str] = None  # "done", "partial", "missed", or None
    checkin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
