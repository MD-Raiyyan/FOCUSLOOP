from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ScreenUsageBase(BaseModel):
    app_identifier: str
    app_name: str
    category: Optional[str] = "General"
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    source: Optional[str] = "device_stats"


class ScreenUsageCreate(ScreenUsageBase):
    user_id: Optional[str] = None


class ScreenUsageBatchCreate(BaseModel):
    user_id: Optional[str] = None
    items: List[ScreenUsageBase]


class ScreenUsageResponse(ScreenUsageBase):
    id: str
    user_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
