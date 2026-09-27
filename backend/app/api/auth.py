from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
)
from app.core.deps import get_current_user, get_optional_current_user
from app.models.user import User
from app.models.auth import RefreshSession
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
from app.behavior.profile import BehaviorProfileManager

router = APIRouter(prefix="/auth", tags=["Authentication & Accounts"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new user account:
    1. Validates and normalizes email/username.
    2. Hashes password securely using Argon2id.
    3. Creates user and initializes default behavioral profile & privacy settings.
    4. Issues short-lived access token and establishes persistent refresh session.
    """
    normalized_email = payload.email.lower().strip()
    existing_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    normalized_username = payload.username.lower().strip() if payload.username else None
    if normalized_username:
        existing_username = db.query(User).filter(func.lower(User.username) == normalized_username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this username already exists",
            )

    pwd_hash = hash_password(payload.password)

    new_user = User(
        email=normalized_email,
        username=normalized_username or normalized_email.split("@")[0],
        name=payload.name or "FocusLoop Explorer",
        password_hash=pwd_hash,
        timezone=payload.timezone or "UTC",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize default behavior profile and agreed privacy defaults
    profile_mgr = BehaviorProfileManager(db, new_user.id)
    profile_mgr.get_or_create_profile()

    # Issue access token and create persistent refresh session
    access_token = create_access_token(user_id=new_user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token()

    session_entry = RefreshSession(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session_entry)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthUserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user with email and password:
    1. Verifies credentials against stored Argon2id password hash.
    2. Issues new access token and creates persistent refresh session.
    3. Never returns passwords or private behavioral intelligence.
    """
    identifier = payload.email.lower().strip()
    user = (
        db.query(User)
        .filter((func.lower(User.email) == identifier) | (func.lower(User.username) == identifier))
        .first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is currently inactive",
        )

    access_token = create_access_token(user_id=user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token()

    session_entry = RefreshSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(session_entry)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthUserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Renews an expired access token using a valid, persistent refresh token.
    Allows users to remain authenticated across app restarts without re-entering credentials.
    """
    tok_hash = hash_token(payload.refresh_token)
    session_entry = (
        db.query(RefreshSession)
        .filter(
            RefreshSession.token_hash == tok_hash,
            RefreshSession.revoked_at.is_(None),
        )
        .first()
    )

    if not session_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if session_entry.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session has expired; please sign in again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == session_entry.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is invalid or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(user_id=user.id)

    return RefreshTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicitly logs out the user:
    Revokes the specific refresh session (or all active sessions for current user) in the database.
    """
    revoked_count = 0
    now = datetime.utcnow()

    if payload.refresh_token:
        tok_hash = hash_token(payload.refresh_token)
        session_entry = (
            db.query(RefreshSession)
            .filter(
                RefreshSession.token_hash == tok_hash,
                RefreshSession.revoked_at.is_(None),
            )
            .first()
        )
        if session_entry:
            session_entry.revoked_at = now
            revoked_count += 1

    if current_user and not payload.refresh_token:
        # Revoke all active sessions for this authenticated user
        sessions = (
            db.query(RefreshSession)
            .filter(
                RefreshSession.user_id == current_user.id,
                RefreshSession.revoked_at.is_(None),
            )
            .all()
        )
        for s in sessions:
            s.revoked_at = now
            revoked_count += 1

    db.commit()
    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=AuthUserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    """
    Returns basic identity of the currently authenticated user.
    """
    return current_user
