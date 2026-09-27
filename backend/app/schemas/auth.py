from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: Optional[str] = "FocusLoop Explorer"
    username: Optional[str] = None
    timezone: Optional[str] = "UTC"


class UserLogin(BaseModel):
    email: str = Field(..., description="Email address or username")
    password: str


class AuthUserResponse(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    timezone: Optional[str] = "UTC"
    is_active: bool = True
    onboarding_completed: bool = False
    onboarding_completed_at: Optional[datetime] = None
    onboarding_step: Optional[str] = "1"
    age_range: Optional[str] = None
    gender: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds
    user: AuthUserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"
