from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.onboarding import UserGoal, UserRoutineContext, UserChallenge, UserInterest
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    OnboardingDataResponse,
    OnboardingUpdatePayload,
    OnboardingCompleteResponse,
    UserGoalSchema,
    UserRoutineContextSchema,
    UserChallengeSchema,
    UserInterestSchema,
)

router = APIRouter(prefix="/onboarding", tags=["Onboarding & User Context"])


def build_onboarding_response(user: User, db: Session) -> OnboardingDataResponse:
    """Helper to assemble the structured onboarding data response."""
    active_goal = (
        db.query(UserGoal)
        .filter(UserGoal.user_id == user.id, UserGoal.is_active == True)
        .order_by(UserGoal.updated_at.desc())
        .first()
    )

    routine = (
        db.query(UserRoutineContext)
        .filter(UserRoutineContext.user_id == user.id)
        .first()
    )

    active_challenges = (
        db.query(UserChallenge)
        .filter(UserChallenge.user_id == user.id, UserChallenge.is_active == True)
        .order_by(UserChallenge.created_at.asc())
        .all()
    )

    active_interests = (
        db.query(UserInterest)
        .filter(UserInterest.user_id == user.id, UserInterest.is_active == True)
        .order_by(UserInterest.created_at.asc())
        .all()
    )

    return OnboardingDataResponse(
        onboarding_completed=user.onboarding_completed,
        onboarding_completed_at=user.onboarding_completed_at,
        onboarding_step=user.onboarding_step or "1",
        name=user.name,
        age_range=user.age_range,
        gender=user.gender,
        goal=UserGoalSchema.model_validate(active_goal) if active_goal else None,
        routine=UserRoutineContextSchema.model_validate(routine) if routine else None,
        challenges=[UserChallengeSchema.model_validate(c) for c in active_challenges],
        interests=[UserInterestSchema.model_validate(i) for i in active_interests],
    )


@router.get("/status", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Checks whether the authenticated user has completed onboarding,
    and returns their last saved step for safe resumption.
    """
    has_partial = (
        (current_user.onboarding_step is not None and current_user.onboarding_step != "1")
        or current_user.age_range is not None
        or current_user.gender is not None
        or db.query(UserGoal).filter(UserGoal.user_id == current_user.id).first() is not None
        or db.query(UserRoutineContext).filter(UserRoutineContext.user_id == current_user.id).first() is not None
        or db.query(UserChallenge).filter(UserChallenge.user_id == current_user.id).first() is not None
    )

    return OnboardingStatusResponse(
        onboarding_completed=current_user.onboarding_completed,
        onboarding_completed_at=current_user.onboarding_completed_at,
        onboarding_step=current_user.onboarding_step or "1",
        has_partial_data=has_partial,
    )


@router.get("", response_model=OnboardingDataResponse)
def get_onboarding_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves all current structured onboarding context for the authenticated user:
    Basic profile info, active goal, routine availability, self-reported challenges, and interests.
    """
    return build_onboarding_response(current_user, db)


@router.put("", response_model=OnboardingDataResponse)
@router.patch("", response_model=OnboardingDataResponse)
def save_onboarding_progress(
    payload: OnboardingUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Incrementally or completely updates structured onboarding context.
    Allows step-by-step saving so users can resume cleanly if interrupted.
    Also used by profile/settings to edit goals, availability, challenges, or interests.
    """
    # 1. Update basic profile context
    step_val = payload.onboarding_step or payload.step
    if step_val is not None:
        current_user.onboarding_step = str(step_val)
    if payload.name is not None:
        current_user.name = payload.name.strip()
    if payload.age_range is not None:
        current_user.age_range = payload.age_range.strip()
    if payload.gender is not None:
        current_user.gender = payload.gender.strip()

    # 2. Update or create active goal (preserving historical goals by deactivating previous)
    goal_cat = (payload.goal.category if payload.goal else None) or payload.goal_category
    goal_desc = (payload.goal.description if payload.goal else None) or payload.goal_description

    if goal_cat is not None or goal_desc is not None:
        # Mark all previous active goals inactive to preserve historical records
        db.query(UserGoal).filter(
            UserGoal.user_id == current_user.id,
            UserGoal.is_active == True,
        ).update({"is_active": False})

        new_goal = UserGoal(
            user_id=current_user.id,
            category=goal_cat.strip() if goal_cat else "General Focus",
            description=goal_desc.strip() if goal_desc else "",
            is_active=True,
        )
        db.add(new_goal)

    # 3. Update routine & availability context (in-place single record)
    routine_window = (payload.routine.preferred_time_window if payload.routine else None) or payload.preferred_time_window
    routine_duration = (payload.routine.daily_available_duration if payload.routine else None) or payload.daily_available_duration

    if routine_window is not None or routine_duration is not None:
        routine = (
            db.query(UserRoutineContext)
            .filter(UserRoutineContext.user_id == current_user.id)
            .first()
        )
        if not routine:
            routine = UserRoutineContext(user_id=current_user.id)
            db.add(routine)
        if routine_window is not None:
            routine.preferred_time_window = routine_window.strip()
        if routine_duration is not None:
            routine.daily_available_duration = routine_duration.strip()
        routine.updated_at = datetime.utcnow()

    # 4. Update self-reported challenges
    if payload.challenges is not None:
        # Mark previous active challenges inactive
        db.query(UserChallenge).filter(
            UserChallenge.user_id == current_user.id,
            UserChallenge.is_active == True,
        ).update({"is_active": False})

        for ch in payload.challenges:
            clean = ch.strip()
            if clean:
                db.add(UserChallenge(
                    user_id=current_user.id,
                    challenge_text=clean,
                    source="self_reported",
                    is_active=True,
                ))

    # 5. Update interests / hobbies
    if payload.interests is not None:
        # Mark previous active interests inactive
        db.query(UserInterest).filter(
            UserInterest.user_id == current_user.id,
            UserInterest.is_active == True,
        ).update({"is_active": False})

        for item in payload.interests:
            clean = item.strip()
            if clean:
                db.add(UserInterest(
                    user_id=current_user.id,
                    interest_text=clean,
                    source="self_reported",
                    is_active=True,
                ))

    db.commit()
    db.refresh(current_user)
    return build_onboarding_response(current_user, db)


@router.post("/complete", response_model=OnboardingCompleteResponse)
def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Idempotently marks onboarding as completed for the authenticated user.
    Records the completion timestamp.
    """
    if not current_user.onboarding_completed:
        current_user.onboarding_completed = True
        current_user.onboarding_completed_at = datetime.utcnow()
        current_user.onboarding_step = "completed"
        db.commit()
        db.refresh(current_user)

    return OnboardingCompleteResponse(
        message="Onboarding completed successfully",
        onboarding_completed=True,
        onboarding_completed_at=current_user.onboarding_completed_at or datetime.utcnow(),
    )
