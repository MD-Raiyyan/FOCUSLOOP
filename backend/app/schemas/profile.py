"""
Pydantic schemas for Personal and Social Profiles, Visibility Settings, and Behavior Curves.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class UserIdentity(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = "UTC"

    model_config = ConfigDict(from_attributes=True)


class ProfileVisibilitySettings(BaseModel):
    current_level: bool = Field(default=False, description="Whether current level is visible to friends")
    behavior_score: bool = Field(default=False, description="Whether behavior score is visible to friends")
    improvement_score: bool = Field(default=True, description="Whether improvement score is visible to friends")
    experiment_effectiveness: bool = Field(default=True, description="Whether experiment effectiveness is visible to friends")
    consistency: bool = Field(default=True, description="Whether consistency rating is visible to friends")
    behavioral_patterns: bool = Field(default=False, description="Whether detailed patterns are visible to friends")


class ProfileVisibilityUpdate(BaseModel):
    current_level: Optional[bool] = None
    behavior_score: Optional[bool] = None
    improvement_score: Optional[bool] = None
    experiment_effectiveness: Optional[bool] = None
    consistency: Optional[bool] = None
    behavioral_patterns: Optional[bool] = None


class ProgressCurvePoint(BaseModel):
    date: str
    progress_score: float
    trend: str  # "improving", "stable", "setback", "recovery"
    metric_context: Optional[str] = None


class PersonalMetrics(BaseModel):
    current_level: str
    level_info: Dict[str, Any]
    behavior_score: float
    improvement_score: float
    experiment_effectiveness: float
    consistency: float


class PersonalProfileResponse(BaseModel):
    """
    Owner's complete Behavior Profile.
    Contains internal behavioral intelligence, private scores, patterns, and full diagnostic details.
    """
    identity: UserIdentity
    visibility_settings: ProfileVisibilitySettings
    metrics: PersonalMetrics
    progress_curve: List[ProgressCurvePoint]
    behavioral_intelligence: Dict[str, Any]
    milestones: List[str]
    updated_at: str


class SocialMetrics(BaseModel):
    """
    Social metrics filtered by user privacy preferences.
    Private metrics will be omitted (None) unless explicitly made public by the user.
    """
    improvement_score: Optional[float] = None
    experiment_effectiveness: Optional[float] = None
    consistency: Optional[float] = None
    current_level: Optional[str] = None
    behavior_score: Optional[float] = None


class SocialProfileResponse(BaseModel):
    """
    Social Progress Profile shown to friends and connections.
    Focuses on positive change, growth, and consistency rather than sensitive behavioral diagnoses.
    Sensitive internal behavioral intelligence is NEVER included in this response.
    """
    identity: UserIdentity
    is_friend: bool
    metrics: SocialMetrics
    progress_curve: List[ProgressCurvePoint]
    milestones: List[str]
    behavioral_patterns: Optional[List[Dict[str, Any]]] = None
