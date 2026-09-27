from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.profile import (
    PersonalProfileResponse,
    SocialProfileResponse,
    ProfileVisibilitySettings,
    ProfileVisibilityUpdate,
    ProgressCurvePoint,
)
from app.behavior.profile import BehaviorProfileManager
from app.core.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile & Social System"])


@router.get("/me", response_model=PersonalProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the complete Personal Behavior Profile for the authenticated owner.
    Contains internal behavioral intelligence, private scores, level progression,
    detected patterns, strengths, weaknesses, insights, and visibility controls.
    Determines user identity strictly from the authentication token.
    """
    profile_mgr = BehaviorProfileManager(db, current_user.id)
    return profile_mgr.get_personal_profile()


@router.get("/visibility", response_model=ProfileVisibilitySettings)
def get_visibility_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the user's current visibility & privacy settings.
    Controls what metrics friends and connections are permitted to view.
    """
    profile_mgr = BehaviorProfileManager(db, current_user.id)
    profile_obj = profile_mgr.get_or_create_profile()
    return profile_obj.visibility_settings


@router.put("/visibility", response_model=ProfileVisibilitySettings)
@router.patch("/visibility", response_model=ProfileVisibilitySettings)
def update_visibility_settings(
    payload: ProfileVisibilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the user's profile privacy / visibility preferences.
    Each metric can be independently toggled without automatically exposing other private data.
    """
    profile_mgr = BehaviorProfileManager(db, current_user.id)

    # Convert non-None fields to dict
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated_settings = profile_mgr.update_visibility(updates)
    return updated_settings


@router.get("/curve", response_model=List[ProgressCurvePoint])
def get_my_progress_curve(
    days: int = 14,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the continuous behavior progress curve based on real recorded check-in trajectory.
    """
    profile_mgr = BehaviorProfileManager(db, current_user.id)
    return profile_mgr.metrics_calc.compute_behavior_progress_curve(days=days)


@router.get("/users/{user_id}", response_model=SocialProfileResponse)
def get_social_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves the Social Profile for a target user.
    Enforces strict backend privacy rules:
    - Never leaks unshared metrics (returns None for private fields).
    - Excludes sensitive internal diagnoses, weaknesses, and private experiment hypotheses.
    - Exposes progress-oriented metrics (Improvement, Consistency, Effectiveness) by default.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_mgr = BehaviorProfileManager(db, target_user.id)
    return profile_mgr.get_social_profile(viewer_id=current_user.id)
