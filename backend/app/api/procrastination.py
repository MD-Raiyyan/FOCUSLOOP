from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.procrastination import ProcrastinationEvent
from app.schemas.procrastination import (
    ProcrastinationEventCreate,
    ProcrastinationEventEnd,
    ProcrastinationEventResponse,
)

router = APIRouter(prefix="/procrastination", tags=["Procrastination Mode"])


@router.get("", response_model=List[ProcrastinationEventResponse])
def list_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists procrastination history for authenticated user."""
    return (
        db.query(ProcrastinationEvent)
        .filter(ProcrastinationEvent.user_id == current_user.id)
        .order_by(ProcrastinationEvent.started_at.desc())
        .all()
    )


@router.post("/start", response_model=ProcrastinationEventResponse, status_code=status.HTTP_201_CREATED)
def start_procrastination_mode(
    payload: ProcrastinationEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    User-confirmed procrastination trigger ('I am procrastinating').
    Initializes an observation window.
    """
    event = ProcrastinationEvent(
        user_id=current_user.id,
        task_id=payload.task_id,
        started_at=payload.started_at or datetime.utcnow(),
        user_confirmed=True,
        trigger_reason=payload.trigger_reason,
        context_data=payload.context_data,
        notes=payload.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/end", response_model=ProcrastinationEventResponse)
def end_procrastination_mode(
    event_id: str,
    payload: ProcrastinationEventEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Closes the procrastination window when the user transitions back to their task.
    Enforces user ownership.
    """
    event = (
        db.query(ProcrastinationEvent)
        .filter(ProcrastinationEvent.id == event_id, ProcrastinationEvent.user_id == current_user.id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procrastination event not found or unauthorized")

    end_time = payload.ended_at or datetime.utcnow()
    event.ended_at = end_time

    if event.started_at:
        diff_seconds = int((end_time - event.started_at).total_seconds())
        event.duration_seconds = max(0, diff_seconds)

    if payload.trigger_reason:
        event.trigger_reason = payload.trigger_reason
    if payload.notes:
        event.notes = payload.notes
    if payload.context_data:
        event.context_data = payload.context_data

    db.commit()
    db.refresh(event)
    return event
