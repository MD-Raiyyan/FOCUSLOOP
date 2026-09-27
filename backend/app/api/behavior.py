from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.behavior import BehaviorPattern, BehaviorProfile
from app.schemas.behavior import (
    BehaviorSummary,
    PatternResponse,
    BehaviorProfileResponse,
)
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.patterns import PatternDetector
from app.behavior.profile import BehaviorProfileManager
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/behavior", tags=["Behavior Engine"])


@router.get("/summary", response_model=BehaviorSummary)
def get_behavior_summary(
    date: Optional[str] = Query(None, description="Date context YYYY-MM-DD. When provided, scopes summary metrics strictly to that day."),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full deterministic behavioral summary.
    All calculations are guaranteed to be mathematically computed by the backend.
    - If date is provided (e.g. today's local date YYYY-MM-DD), metrics represent that specific day only.
    - If date is omitted, metrics represent the lifetime/all-time historical summary.
    """
    metrics_calc = BehaviorMetricsCalculator(db, user.id)
    detector = PatternDetector(db, user.id)
    profile_mgr = BehaviorProfileManager(db, user.id)

    # Refresh patterns and profile
    active_patterns = detector.detect_and_update_patterns()
    profile_data = profile_mgr.refresh_profile()

    comp = metrics_calc.compute_task_completion_stats(date=date)
    delay = metrics_calc.compute_start_delay_stats(date=date)
    proc = metrics_calc.compute_procrastination_stats(date=date)
    top_apps = metrics_calc.compute_top_distractions()

    return BehaviorSummary(
        completion_rate=comp["completion_rate"],
        total_tasks_tracked=comp["total"],
        completed_tasks=comp["done"],
        missed_tasks=comp["missed"],
        partial_tasks=comp["partial"],
        average_start_delay_minutes=delay["average_start_delay_minutes"],
        best_focus_window=profile_data.get("best_focus_window", "Morning"),
        worst_focus_window=profile_data.get("worst_focus_window", "Afternoon"),
        procrastination_count=proc["count"],
        total_procrastination_minutes=proc["total_minutes"],
        top_distraction_apps=top_apps,
        active_patterns=[PatternResponse.model_validate(p) for p in active_patterns],
        profile=profile_data,
        date=date,
    )


@router.get("/patterns", response_model=List[PatternResponse])
def get_patterns(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all detected recurring behavioral patterns."""
    detector = PatternDetector(db, user.id)
    patterns = detector.detect_and_update_patterns()
    return patterns


@router.get("/profile")
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves the dynamic learned behavior profile, ensuring it reflects latest evidence."""
    profile_mgr = BehaviorProfileManager(db, user.id)
    profile_data = profile_mgr.refresh_profile()
    profile = profile_mgr.get_or_create_profile()
    return {
        "user_id": user.id,
        "profile_data": profile_data,
        "model_version": profile.model_version,
        "updated_at": profile.updated_at,
    }


@router.post("/refresh")
def force_refresh_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Forces recalculation of metrics, patterns, and profile."""
    profile_mgr = BehaviorProfileManager(db, user.id)
    new_profile = profile_mgr.refresh_profile()
    return {
        "message": "Behavioral profile recomputed successfully.",
        "profile": new_profile,
    }
