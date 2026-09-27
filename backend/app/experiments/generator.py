from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.experiment import Experiment
from app.models.behavior import BehaviorPattern
from app.behavior.metrics import BehaviorMetricsCalculator


class ExperimentGenerator:
    """Proposes measurable, low-barrier behavioral micro-experiments based on detected patterns."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.metrics_calc = BehaviorMetricsCalculator(db, user_id)

    def suggest_experiments(self) -> List[Experiment]:
        """Generates candidate experiments matching current user patterns."""
        patterns = (
            self.db.query(BehaviorPattern)
            .filter(BehaviorPattern.user_id == self.user_id, BehaviorPattern.status == "active")
            .all()
        )

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        end_str = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")
        delay_stats = self.metrics_calc.compute_start_delay_stats()
        comp_stats = self.metrics_calc.compute_task_completion_stats()

        created_experiments = []

        # Check existing active/suggested experiments
        existing_titles = {
            e.title
            for e in self.db.query(Experiment)
            .filter(Experiment.user_id == self.user_id)
            .all()
        }

        # 1. 5-Minute Gateway experiment
        if "The 5-Minute Gateway" not in existing_titles:
            exp1 = Experiment(
                user_id=self.user_id,
                title="The 5-Minute Gateway",
                description="Work on your task for just 5 minutes with zero expectation of finishing. Stop if you wish.",
                hypothesis="Lowering the initiation barrier will reduce average start delay by at least 30%.",
                intervention_type="initiation_barrier",
                start_date=today_str,
                end_date=end_str,
                target_metric="average_start_delay_minutes",
                baseline_value=float(delay_stats.get("average_start_delay_minutes") or 20.0),
                target_value=max(5.0, float(delay_stats.get("average_start_delay_minutes") or 20.0) * 0.7),
                status="suggested",
            )
            self.db.add(exp1)
            created_experiments.append(exp1)

        # 2. Morning Focus Shift
        if "Morning Focus Alignment" not in existing_titles:
            exp2 = Experiment(
                user_id=self.user_id,
                title="Morning Focus Alignment",
                description="Schedule your most challenging focus session before 11:30 AM rather than the afternoon.",
                hypothesis="Aligning deep work with morning circadian clarity will increase completion rate by 20%.",
                intervention_type="circadian_shift",
                start_date=today_str,
                end_date=end_str,
                target_metric="completion_rate",
                baseline_value=float(comp_stats.get("completion_rate", 0.6)),
                target_value=min(1.0, float(comp_stats.get("completion_rate", 0.6)) + 0.2),
                status="suggested",
            )
            self.db.add(exp2)
            created_experiments.append(exp2)

        self.db.commit()
        return created_experiments
