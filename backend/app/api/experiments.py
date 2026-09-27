from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.experiment import Experiment
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentResultResponse,
)
from app.experiments.generator import ExperimentGenerator
from app.experiments.evaluator import ExperimentEvaluator

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
    """Creates a custom micro-experiment for authenticated user."""
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
    """Updates experiment status or duration, enforcing ownership authorization."""
    exp = (
        db.query(Experiment)
        .filter(Experiment.id == experiment_id, Experiment.user_id == current_user.id)
        .first()
    )
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found or unauthorized")

    if payload.status:
        exp.status = payload.status
    if payload.end_date:
        exp.end_date = payload.end_date

    db.commit()
    db.refresh(exp)
    return exp
