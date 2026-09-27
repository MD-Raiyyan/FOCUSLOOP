"""Pydantic schemas for request/response validation."""
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.checkin import CheckinCreate, CheckinResponse
from app.schemas.procrastination import (
    ProcrastinationEventCreate,
    ProcrastinationEventEnd,
    ProcrastinationEventResponse,
)
from app.schemas.screen_usage import (
    ScreenUsageCreate,
    ScreenUsageBatchCreate,
    ScreenUsageResponse,
)
from app.schemas.behavior import (
    MetricResponse,
    PatternResponse,
    BehaviorProfileResponse,
    BehaviorSummary,
)
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentResultResponse,
    ExperimentEvaluationRequest,
)
from app.schemas.chat import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    AIExplanationRequest,
    AIExplanationResponse,
)

from app.schemas.profile import (
    UserIdentity,
    ProfileVisibilitySettings,
    ProfileVisibilityUpdate,
    ProgressCurvePoint,
    PersonalMetrics,
    PersonalProfileResponse,
    SocialMetrics,
    SocialProfileResponse,
)
from app.schemas.social import (
    FriendshipCreate,
    FriendshipResponse,
    FriendUserSummary,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    AuthUserResponse,
    TokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    LogoutResponse,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "AuthUserResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "LogoutResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserIdentity",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "CheckinCreate",
    "CheckinResponse",
    "ProcrastinationEventCreate",
    "ProcrastinationEventEnd",
    "ProcrastinationEventResponse",
    "ScreenUsageCreate",
    "ScreenUsageBatchCreate",
    "ScreenUsageResponse",
    "MetricResponse",
    "PatternResponse",
    "BehaviorProfileResponse",
    "BehaviorSummary",
    "ProfileVisibilitySettings",
    "ProfileVisibilityUpdate",
    "ProgressCurvePoint",
    "PersonalMetrics",
    "PersonalProfileResponse",
    "SocialMetrics",
    "SocialProfileResponse",
    "FriendshipCreate",
    "FriendshipResponse",
    "FriendUserSummary",
    "ExperimentCreate",
    "ExperimentUpdate",
    "ExperimentResponse",
    "ExperimentResultResponse",
    "ExperimentEvaluationRequest",
    "MessageCreate",
    "MessageResponse",
    "ConversationResponse",
    "AIExplanationRequest",
    "AIExplanationResponse",
]
