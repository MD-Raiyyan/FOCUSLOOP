from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse

from app.core.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_current_user_helper(db: Session) -> User:
    """Helper to ensure a working user exists for immediate development needs."""
    user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
    if not user:
        user = User(
            id=DEFAULT_USER_ID,
            name="FocusLoop Explorer",
            email="user@focusloop.local",
            timezone="UTC",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    """Fetches the authenticated user profile."""
    return current_user


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user."""
    if payload.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")

    if payload.username:
        existing_username = db.query(User).filter(User.username == payload.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="User with this username already exists")

    new_user = User(
        name=payload.name,
        username=payload.username,
        bio=payload.bio,
        avatar_url=payload.avatar_url,
        email=payload.email,
        timezone=payload.timezone,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """Retrieves a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    """Updates user information."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.username is not None and payload.username != user.username:
        existing_username = db.query(User).filter(User.username == payload.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="User with this username already exists")
        user.username = payload.username

    if payload.name is not None:
        user.name = payload.name
    if payload.bio is not None:
        user.bio = payload.bio
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    if payload.email is not None:
        user.email = payload.email
    if payload.timezone is not None:
        user.timezone = payload.timezone

    db.commit()
    db.refresh(user)
    return user
