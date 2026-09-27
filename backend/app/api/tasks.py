from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _enrich_task_response(task: Task, checkin: Optional[TaskCheckin]) -> TaskResponse:
    """Enriches a task entity with occurrence checkin status for the target date."""
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        name=task.name,
        description=task.description,
        category=task.category,
        planned_time=task.planned_time,
        target_duration_minutes=task.target_duration_minutes,
        frequency=task.frequency or "daily",
        active=task.active,
        today_status=checkin.status if checkin else None,
        checkin_id=checkin.id if checkin else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    date: Optional[str] = Query(None, description="Date context YYYY-MM-DD (defaults to UTC today)"),
    active_only: bool = Query(True, description="Filter for active tasks only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists tasks for the authenticated user with date-occurrence context.
    - Daily tasks remain in active list with today's status (pending/done/partial/missed).
    - One-time tasks show today's status if completed today; if completed on a prior date,
      they are excluded from active list.
    """
    target_date = date.strip() if date else datetime.utcnow().strftime("%Y-%m-%d")

    # Base query for user's tasks
    query = db.query(Task).filter(Task.user_id == current_user.id)
    if active_only:
        query = query.filter(Task.active == True)
    tasks = query.order_by(Task.planned_time.asc()).all()

    # Query check-ins on target_date for this user
    checkins_today = (
        db.query(TaskCheckin)
        .filter(TaskCheckin.user_id == current_user.id, TaskCheckin.date == target_date)
        .all()
    )
    checkin_by_task = {c.task_id: c for c in checkins_today}

    # Query task IDs completed on dates strictly prior to target_date
    prior_checkin_task_ids = set(
        row[0] for row in (
            db.query(TaskCheckin.task_id)
            .filter(TaskCheckin.user_id == current_user.id, TaskCheckin.date < target_date)
            .all()
        )
    )

    enriched_tasks: List[TaskResponse] = []
    for task in tasks:
        task_freq = (task.frequency or "daily").lower()
        checkin = checkin_by_task.get(task.id)

        # For one-time tasks: if completed on a prior date and active_only=True, exclude
        if task_freq == "once" and active_only:
            if checkin is None and task.id in prior_checkin_task_ids:
                # Already completed in the past, no active occurrence for target_date
                continue

        enriched_tasks.append(_enrich_task_response(task, checkin))

    return enriched_tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new one-time or daily task for the authenticated user."""
    freq = payload.frequency or "daily"
    task = Task(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        category=payload.category.strip() if payload.category else "Focus",
        planned_time=payload.planned_time.strip() if payload.planned_time else "09:00",
        target_duration_minutes=payload.target_duration_minutes or "30",
        frequency=freq,
        active=payload.active if payload.active is not None else True,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _enrich_task_response(task, None)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    date: Optional[str] = Query(None, description="Date context YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves a single task by ID, enforcing ownership authorization and occurrence status."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    target_date = date.strip() if date else datetime.utcnow().strftime("%Y-%m-%d")
    checkin = (
        db.query(TaskCheckin)
        .filter(TaskCheckin.task_id == task.id, TaskCheckin.date == target_date)
        .first()
    )
    return _enrich_task_response(task, checkin)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates task properties. Changing recurrence affects future occurrences
    without corrupting or rewriting historical check-ins.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "name" and value is not None:
            task.name = value.strip()
        elif field == "description":
            task.description = value.strip() if value else None
        elif field == "category" and value is not None:
            task.category = value.strip()
        elif field == "planned_time" and value is not None:
            task.planned_time = value.strip()
        elif field == "target_duration_minutes" and value is not None:
            task.target_duration_minutes = str(value).strip()
        elif field == "frequency" and value is not None:
            task.frequency = value
        elif field == "active" and value is not None:
            task.active = value

    db.commit()
    db.refresh(task)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    checkin = (
        db.query(TaskCheckin)
        .filter(TaskCheckin.task_id == task.id, TaskCheckin.date == today)
        .first()
    )
    return _enrich_task_response(task, checkin)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes an authenticated user's task and cascades to checkins."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
