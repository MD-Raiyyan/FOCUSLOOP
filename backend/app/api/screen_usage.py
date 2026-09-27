from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.screen_usage import ScreenUsage
from app.schemas.screen_usage import (
    ScreenUsageCreate,
    ScreenUsageBatchCreate,
    ScreenUsageResponse,
)

router = APIRouter(prefix="/screen-usage", tags=["Screen & App Usage"])


@router.get("", response_model=List[ScreenUsageResponse])
def get_screen_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches device screen usage sessions for the authenticated user."""
    return (
        db.query(ScreenUsage)
        .filter(ScreenUsage.user_id == current_user.id)
        .order_by(ScreenUsage.started_at.desc())
        .limit(100)
        .all()
    )


@router.post("", response_model=ScreenUsageResponse, status_code=status.HTTP_201_CREATED)
def record_screen_usage(
    payload: ScreenUsageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Records an individual screen usage observation for authenticated user."""
    entry = ScreenUsage(
        user_id=current_user.id,
        app_identifier=payload.app_identifier,
        app_name=payload.app_name,
        category=payload.category,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        duration_seconds=payload.duration_seconds,
        source=payload.source or "device_stats",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def record_batch_screen_usage(
    payload: ScreenUsageBatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Syncs a batch of app usage events collected from mobile client for authenticated user."""
    entries = [
        ScreenUsage(
            user_id=current_user.id,
            app_identifier=item.app_identifier,
            app_name=item.app_name,
            category=item.category,
            started_at=item.started_at,
            ended_at=item.ended_at,
            duration_seconds=item.duration_seconds,
            source=item.source or "device_stats",
        )
        for item in payload.items
    ]
    db.add_all(entries)
    db.commit()
    return {"message": f"Successfully ingested {len(entries)} usage records."}
