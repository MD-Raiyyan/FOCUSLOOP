from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class UserGoalSchema(BaseModel):
    id: Optional[str] = None
    category: str
    description: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRoutineContextSchema(BaseModel):
    preferred_time_window: Optional[str] = None
    daily_available_duration: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserChallengeSchema(BaseModel):
    id: Optional[str] = None
    challenge_text: str
    source: str = "self_reported"
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserInterestSchema(BaseModel):
    id: Optional[str] = None
    interest_text: str
    source: str = "self_reported"
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GoalInput(BaseModel):
    category: str
    description: Optional[str] = ""


class RoutineInput(BaseModel):
    preferred_time_window: Optional[str] = None
    daily_available_duration: Optional[str] = None


class OnboardingStatusResponse(BaseModel):
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None
    onboarding_step: str = "1"
    current_step: Optional[str] = None
    has_partial_data: bool = False

    def model_post_init(self, __context):
        if not self.current_step:
            self.current_step = self.onboarding_step


class OnboardingDataResponse(BaseModel):
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None
    onboarding_step: str = "1"
    step: Optional[str] = None
    name: Optional[str] = None
    age_range: Optional[str] = None
    gender: Optional[str] = None
    profile: Optional[dict] = None
    goal: Optional[UserGoalSchema] = None
    routine: Optional[UserRoutineContextSchema] = None
    challenges: List[UserChallengeSchema] = Field(default_factory=list)
    interests: List[UserInterestSchema] = Field(default_factory=list)

    def model_post_init(self, __context):
        if not self.step:
            self.step = self.onboarding_step
        if not self.profile:
            self.profile = {
                "name": self.name,
                "age_range": self.age_range,
                "gender": self.gender,
            }


class OnboardingUpdatePayload(BaseModel):
    onboarding_step: Optional[str] = None
    step: Optional[str] = None
    name: Optional[str] = None
    age_range: Optional[str] = None
    gender: Optional[str] = None
    goal: Optional[GoalInput] = None
    goal_category: Optional[str] = None
    goal_description: Optional[str] = None
    routine: Optional[RoutineInput] = None
    preferred_time_window: Optional[str] = None
    daily_available_duration: Optional[str] = None
    challenges: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class OnboardingCompleteResponse(BaseModel):
    message: str = "Onboarding completed successfully"
    onboarding_completed: bool = True
    onboarding_completed_at: datetime
    completed_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if not self.completed_at:
            self.completed_at = self.onboarding_completed_at
