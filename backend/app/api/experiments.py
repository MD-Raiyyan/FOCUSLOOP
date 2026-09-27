from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.experiment import Experiment
from app.models.behavior import BehaviorPattern
from app.behavior.snapshot import build_pattern_snapshot
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentResultResponse,
)
from app.experiments.generator import ExperimentGenerator
from app.experiments.evaluator import ExperimentEvaluator
from app.experiments.strategy_catalog import get_strategy
from app.experiments.strategy_selector import StrategySelector

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("", response_model=List[ExperimentResponse])
def get_experiments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches all experiments (suggested, active, completed) for authenticated user."""
    return (
        db.query(Experiment)
        .filter(Experiment.user_id == current_user.id)
        .order_by(Experiment.created_at.desc())
        .all()
    )


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a custom micro-experiment for authenticated user with immutable historical pattern context."""
    pattern_snapshot = None
    if payload.pattern_snapshot:
        pattern_snapshot = payload.pattern_snapshot
    elif payload.pattern_id:
        pat = (
            db.query(BehaviorPattern)
            .filter(
                BehaviorPattern.id == payload.pattern_id,
                BehaviorPattern.user_id == current_user.id,
            )
            .first()
        )
        if pat:
            pattern_snapshot = build_pattern_snapshot(pat)

    # Concurrency enforcement: exactly one active experiment per user
    active_existing = (
        db.query(Experiment)
        .filter(Experiment.user_id == current_user.id, Experiment.status == "active")
        .first()
    )
    if active_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active experiment. Complete or dismiss it before activating a new one.",
        )

    exp = Experiment(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        hypothesis=payload.hypothesis,
        intervention_type=payload.intervention_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        target_metric=payload.target_metric,
        baseline_value=payload.baseline_value,
        target_value=payload.target_value,
        pattern_id=payload.pattern_id,
        pattern_snapshot=pattern_snapshot,
        status="active",
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.post("/suggest", response_model=List[ExperimentResponse])
def suggest_experiments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates personalized micro-experiments tailored to detected patterns."""
    generator = ExperimentGenerator(db, current_user.id)
    generator.suggest_experiments()
    return (
        db.query(Experiment)
        .filter(Experiment.user_id == current_user.id)
        .order_by(Experiment.created_at.desc())
        .all()
    )


@router.post("/{experiment_id}/evaluate", response_model=ExperimentResultResponse)
def evaluate_experiment(
    experiment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Measures the results of an experiment against its baseline.
    Updates the user's learned profile to close the behavioral loop.
    Enforces user authorization.
    """
    exp = (
        db.query(Experiment)
        .filter(Experiment.id == experiment_id, Experiment.user_id == current_user.id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found or unauthorized")

    if exp.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Experiment cannot be evaluated with status '{exp.status}'. Only 'active' experiments can be evaluated.",
        )

    evaluator = ExperimentEvaluator(db, current_user.id)
    result = evaluator.evaluate_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment could not be evaluated")
    return result


@router.put("/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(
    experiment_id: str,
    payload: ExperimentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates experiment status or duration, enforcing single-active concurrency and baseline locking."""
    exp = (
        db.query(Experiment)
        .filter(Experiment.id == experiment_id, Experiment.user_id == current_user.id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found or unauthorized")

    if payload.status == "active" and exp.status != "active":
        # Concurrency enforcement: exactly one active experiment per user
        active_existing = (
            db.query(Experiment)
            .filter(
                Experiment.user_id == current_user.id,
                Experiment.status == "active",
                Experiment.id != exp.id,
            )
            .first()
        )
        if active_existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active experiment. Complete or dismiss it before activating a new one.",
            )

        # Baseline Contract: recalculate authoritative baseline over [start_date - 7d, start_date - 1d]
        today_date = datetime.utcnow().date()
        today_str = today_date.strftime("%Y-%m-%d")
        exp.start_date = today_str

        strategy = get_strategy(exp.intervention_type)
        duration_days = strategy.duration_days if strategy else 5
        exp.end_date = (today_date + timedelta(days=duration_days)).strftime("%Y-%m-%d")

        selector = StrategySelector(db, current_user.id, ref_date=today_str)
        auth_baseline = selector.compute_baseline_for_metric(exp.target_metric, today_date)
        exp.baseline_value = auth_baseline
        if strategy:
            exp.target_value = strategy.compute_target(auth_baseline)

        exp.status = "active"
    elif payload.status:
        exp.status = payload.status

    if payload.end_date:
        exp.end_date = payload.end_date

    db.commit()
    db.refresh(exp)
    return exp
