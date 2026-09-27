from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class MetricResponse(BaseModel):
    id: str
    user_id: str
    metric_type: str
    metric_value: float
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatternResponse(BaseModel):
    id: str
    user_id: str
    pattern_type: str
    title: str
    description: str
    confidence: str
    sample_size: int
    first_detected: datetime
    last_detected: datetime
    status: str
    supporting_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BehaviorProfileResponse(BaseModel):
    user_id: str
    profile_data: Dict[str, Any]
    model_version: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BehaviorSummary(BaseModel):
    completion_rate: float  # True ratio: 0.0 to 1.0
    total_tasks_tracked: int
    completed_tasks: int
    missed_tasks: int
    partial_tasks: int
    average_start_delay_minutes: Optional[float] = None  # None = no observations; 0.0 = measured zero delay
    best_focus_window: str
    worst_focus_window: str
    procrastination_count: int
    total_procrastination_minutes: float
    top_distraction_apps: List[Dict[str, Any]]
    active_patterns: List[PatternResponse]
    profile: Optional[Dict[str, Any]] = None
    date: Optional[str] = None  # Context date if scoped to a specific day YYYY-MM-DD

