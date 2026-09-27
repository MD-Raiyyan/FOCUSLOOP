from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_CHECKIN_STATUSES = {"done", "partial", "missed"}


class CheckinBase(BaseModel):
    task_id: str
    date: str = Field(..., description="Date string YYYY-MM-DD")
    status: str = Field(..., description="'done', 'partial', or 'missed'")
    completed_at: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    start_delay_minutes: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_CHECKIN_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed check-in statuses are: 'done', 'partial', 'missed'.")
        return clean

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        clean = v.strip()
        try:
            datetime.strptime(clean, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date '{v}'. Expected format YYYY-MM-DD.")
        return clean


class CheckinCreate(CheckinBase):
    user_id: Optional[str] = None


class CheckinResponse(CheckinBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
