from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ExperimentBase(BaseModel):
    title: str
    description: str
    hypothesis: str
    intervention_type: Optional[str] = "environmental"
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None
    target_metric: str
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    pattern_id: Optional[str] = None


class ExperimentCreate(ExperimentBase):
    user_id: Optional[str] = None


class ExperimentUpdate(BaseModel):
    status: Optional[str] = None  # active, completed, dismissed
    end_date: Optional[str] = None


class ExperimentResultResponse(BaseModel):
    id: str
    experiment_id: str
    metric_name: str
    before_value: Optional[float] = None
    after_value: Optional[float] = None
    change_value: Optional[float] = None
    percent_change: Optional[float] = None
    conclusion: str
    result_summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentResponse(ExperimentBase):
    id: str
    user_id: str
    status: str
    created_at: datetime
    results: List[ExperimentResultResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ExperimentEvaluationRequest(BaseModel):
    experiment_id: str
