from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.experiment import Experiment
from app.behavior.patterns import PatternDetector
from app.experiments.strategy_selector import StrategySelector


class ExperimentGenerator:
    """Proposes measurable, pattern-driven behavioral micro-experiments using deterministic Strategy Selection."""

    def __init__(self, db: Session, user_id: str, ref_date: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.pattern_detector = PatternDetector(db, user_id, ref_date=ref_date)
        self.strategy_selector = StrategySelector(db, user_id, ref_date=ref_date)

    def suggest_experiments(self) -> List[Experiment]:
        """
        Refreshes persisted patterns from raw evidence and generates an eligible
        candidate experiment matching current user patterns via deterministic Strategy Selection.
        Returns all experiments for the user ordered by creation date descending.
        """
        # 1. Recalculate/refresh persisted pattern state in PostgreSQL
        self.pattern_detector.refresh_patterns()

        # 2. Run deterministic strategy selector
        self.strategy_selector.generate_experiment()

        # 3. Return all user experiments
        return (
            self.db.query(Experiment)
            .filter(Experiment.user_id == self.user_id)
            .order_by(Experiment.created_at.desc())
            .all()
        )
