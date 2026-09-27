from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.checkin import TaskCheckin
from app.models.task import Task
from app.schemas.checkin import CheckinCreate, CheckinResponse
from app.behavior.profile import BehaviorProfileManager

router = APIRouter(prefix="/checkins", tags=["Task Check-ins"])


@router.get("", response_model=List[CheckinResponse])
def get_checkins(
    date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves check-in history for the authenticated user."""
    query = db.query(TaskCheckin).filter(TaskCheckin.user_id == current_user.id)
    if date:
        query = query.filter(TaskCheckin.date == date)
    if task_id:
        query = query.filter(TaskCheckin.task_id == task_id)
    return query.order_by(TaskCheckin.created_at.desc()).all()


@router.post("", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
def record_checkin(
    payload: CheckinCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logs or updates a completed, partial, or missed task check-in for the authenticated user.
    - Idempotent: If a check-in already exists for (task_id, date), updates it in-place.
    - Rejects check-ins for inactive or non-existent tasks.
    - Rejects check-ins for one-time tasks that already have a check-in on another date.
    """
    task = db.query(Task).filter(Task.id == payload.task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or unauthorized")

    if not task.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot check in to an inactive task")

    task_freq = (task.frequency or "daily").lower()

    # If one-time task, verify it hasn't already been checked in on a different date
    if task_freq == "once":
        prior_checkin = (
            db.query(TaskCheckin)
            .filter(TaskCheckin.task_id == task.id, TaskCheckin.date != payload.date)
            .first()
        )
        if prior_checkin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"One-time task has already been checked in for date {prior_checkin.date}",
            )

    # Deterministically calculate start delay if actual_start_time is given
    calculated_delay = payload.start_delay_minutes
    if calculated_delay is None and payload.actual_start_time and task.planned_time:
        try:
            planned_h, planned_m = map(int, task.planned_time.split(":"))
            actual_time = payload.actual_start_time
            actual_total_mins = actual_time.hour * 60 + actual_time.minute
            planned_total_mins = planned_h * 60 + planned_m
            calculated_delay = max(0, actual_total_mins - planned_total_mins)
        except Exception:
            calculated_delay = None

    # Check for existing check-in on this occurrence date (Idempotency check)
    existing_checkin = (
        db.query(TaskCheckin)
        .filter(TaskCheckin.task_id == task.id, TaskCheckin.date == payload.date)
        .first()
    )

    if existing_checkin:
        # Idempotent update
        existing_checkin.status = payload.status
        if payload.completed_at is not None:
            existing_checkin.completed_at = payload.completed_at
        elif payload.status == "done" and not existing_checkin.completed_at:
            existing_checkin.completed_at = datetime.utcnow()

        if payload.duration_minutes is not None:
            existing_checkin.duration_minutes = payload.duration_minutes
        if payload.actual_start_time is not None:
            existing_checkin.actual_start_time = payload.actual_start_time
        if calculated_delay is not None:
            existing_checkin.start_delay_minutes = calculated_delay
        if payload.notes is not None:
            existing_checkin.notes = payload.notes

        db.commit()
        db.refresh(existing_checkin)
        response.status_code = status.HTTP_200_OK
        result_checkin = existing_checkin
    else:
        completed_at = payload.completed_at
        if payload.status == "done" and not completed_at:
            completed_at = datetime.utcnow()

        new_checkin = TaskCheckin(
            user_id=current_user.id,
            task_id=payload.task_id,
            date=payload.date,
            status=payload.status,
            completed_at=completed_at,
            actual_start_time=payload.actual_start_time,
            duration_minutes=payload.duration_minutes,
            start_delay_minutes=calculated_delay,
            notes=payload.notes,
        )
        db.add(new_checkin)
        db.commit()
        db.refresh(new_checkin)
        result_checkin = new_checkin

    # Automatically refresh behavioral profile in background
    try:
        profile_mgr = BehaviorProfileManager(db, current_user.id)
        profile_mgr.refresh_profile()
    except Exception:
        pass

    return result_checkin
