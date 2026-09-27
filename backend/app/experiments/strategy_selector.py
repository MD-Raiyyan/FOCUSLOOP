from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentResult
from app.models.behavior import BehaviorPattern
from app.models.checkin import TaskCheckin
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.snapshot import build_pattern_snapshot
from app.experiments.strategy_catalog import (
    Strategy,
    STRATEGY_CATALOG,
    get_strategy,
    get_strategies_for_pattern,
    PATTERN_PRIORITY_HIERARCHY,
    COOLDOWN_GRADUATED_POSITIVE_DAYS,
    COOLDOWN_NEGATIVE_DAYS,
    COOLDOWN_INCONCLUSIVE_DAYS,
    COOLDOWN_DISMISSED_DAYS,
)


class StrategySelector:
    """
    Deterministic behavioral Strategy Selector.
    
    Transforms active, evidence-backed BehaviorPattern records into actionable,
    measurable behavioral micro-experiments while enforcing:
    1. Cold-start observation boundaries (>= 3 check-ins required)
    2. Explainable pattern prioritization cascade (Confidence -> Recent N -> Severity Hierarchy)
    3. Pattern-specific strategy cooling (Positive=30d, Negative=14d, Inconclusive=7d, Dismissed=14d)
    4. Anti-duplication (suppresses currently suggested and active strategies)
    5. Baseline contract alignment ([T-7d, T-1d] pre-experiment window)
    """

    def __init__(self, db: Session, user_id: str, ref_date: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.metrics_calc = BehaviorMetricsCalculator(db, user_id)

        if ref_date:
            try:
                self.ref_date_obj = datetime.strptime(ref_date, "%Y-%m-%d").date()
            except Exception:
                self.ref_date_obj = datetime.utcnow().date()
        else:
            self.ref_date_obj = datetime.utcnow().date()

        self.ref_date_str = self.ref_date_obj.strftime("%Y-%m-%d")

    def is_strategy_on_cooldown(self, pattern_id: str, strategy: Strategy) -> bool:
        """
        Determines if a candidate strategy is currently suppressed for a specific pattern.
        Enforces pattern-specific cooling: an intervention that failed for Pattern A
        remains fully eligible for Pattern B.
        """
        experiments = (
            self.db.query(Experiment)
            .filter(
                Experiment.user_id == self.user_id,
                Experiment.pattern_id == pattern_id,
                Experiment.intervention_type == strategy.intervention_type,
            )
            .all()
        )

        for exp in experiments:
            # 1. Active suppression: cannot suggest if already active
            if exp.status == "active":
                return True

            # 2. Duplicate prevention: cannot suggest if already currently suggested
            if exp.status == "suggested":
                return True

            # 3. Dismissed cooling
            if exp.status == "dismissed":
                exp_date = self._extract_date(exp.end_date or exp.start_date, exp.created_at)
                if exp_date and (self.ref_date_obj - exp_date).days < COOLDOWN_DISMISSED_DAYS:
                    return True

            # 4. Completed cooling based on evaluated outcome
            if exp.status == "completed":
                for res in exp.results:
                    res_date = res.created_at.date() if res.created_at else self.ref_date_obj
                    days_elapsed = (self.ref_date_obj - res_date).days

                    if res.conclusion == "positive":
                        if days_elapsed < COOLDOWN_GRADUATED_POSITIVE_DAYS:
                            return True
                    elif res.conclusion == "negative":
                        if days_elapsed < COOLDOWN_NEGATIVE_DAYS:
                            return True
                    elif res.conclusion == "inconclusive":
                        if days_elapsed < COOLDOWN_INCONCLUSIVE_DAYS:
                            return True

        return False

    def select_strategy_for_pattern(self, pattern: BehaviorPattern) -> Optional[Strategy]:
        """
        Selects the first non-cooled candidate strategy for the given pattern.
        """
        candidates = get_strategies_for_pattern(pattern.pattern_type)
        for strategy in candidates:
            if not self.is_strategy_on_cooldown(pattern.id, strategy):
                return strategy
        return None

    def select_eligible_patterns(self) -> List[BehaviorPattern]:
        """
        Retrieves and sorts eligible active patterns using the deterministic cascade:
        1. Eligibility: status == 'active', confidence in ['high', 'moderate'],
           no insufficient evidence flag, no active experiment on this pattern,
           and at least one non-cooled candidate strategy available.
        2. Confidence: 'high' > 'moderate'.
        3. Recent evidence sample size: larger recent N preferred.
        4. Tie-breaking: start_delay_resistance > afternoon_slump > primary_distraction.
        """
        all_active = (
            self.db.query(BehaviorPattern)
            .filter(
                BehaviorPattern.user_id == self.user_id,
                BehaviorPattern.status == "active",
                BehaviorPattern.confidence.in_(["high", "moderate"]),
            )
            .all()
        )

        eligible: List[BehaviorPattern] = []

        for p in all_active:
            sup = p.supporting_metrics or {}
            # Exclude patterns with insufficient current evidence
            if sup.get("insufficient_evidence") or sup.get("insufficient_current_evidence"):
                continue

            # Exclude if this pattern already has an active experiment running
            has_active = (
                self.db.query(Experiment)
                .filter(
                    Experiment.user_id == self.user_id,
                    Experiment.pattern_id == p.id,
                    Experiment.status == "active",
                )
                .first()
            )
            if has_active:
                continue

            # Exclude if all candidate strategies for this pattern are currently on cooldown
            available_strategy = self.select_strategy_for_pattern(p)
            if not available_strategy:
                continue

            eligible.append(p)

        def pattern_sort_key(p: BehaviorPattern):
            # Criterion 1: Confidence
            conf_score = 2 if p.confidence == "high" else 1

            # Criterion 2: Recent sample size (from supporting_metrics or sample_size)
            sup = p.supporting_metrics or {}
            rec_window = sup.get("recent_window") or {}
            recent_sample = rec_window.get("sample_size")
            if recent_sample is None:
                recent_sample = p.sample_size or 0

            # Criterion 3: Hierarchy tie-breaker
            try:
                hier_rank = len(PATTERN_PRIORITY_HIERARCHY) - PATTERN_PRIORITY_HIERARCHY.index(p.pattern_type)
            except ValueError:
                hier_rank = 0

            return (conf_score, recent_sample, hier_rank)

        eligible.sort(key=pattern_sort_key, reverse=True)
        return eligible

    def compute_baseline_for_metric(self, target_metric: str, ref_date_obj: date) -> float:
        """
        Computes the authoritative pre-experiment baseline strictly over [ref_date - 7d, ref_date - 1d].
        Guarantees exact semantic alignment with ExperimentEvaluator.before_value.
        """
        baseline_start = (ref_date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
        baseline_end = (ref_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")

        if target_metric == "average_start_delay_minutes":
            stats = self.metrics_calc.compute_start_delay_stats(
                start_date=baseline_start,
                end_date=baseline_end,
            )
            val = stats.get("average_start_delay_minutes")
            if val is None:
                lifetime = self.metrics_calc.compute_start_delay_stats()
                val = lifetime.get("average_start_delay_minutes") or 20.0
            return float(val)
        else:
            # Default to completion_rate
            stats = self.metrics_calc.compute_task_completion_stats(
                start_date=baseline_start,
                end_date=baseline_end,
            )
            val = stats.get("completion_rate")
            if val is None or stats.get("total", 0) == 0:
                lifetime = self.metrics_calc.compute_task_completion_stats()
                val = lifetime.get("completion_rate") if lifetime.get("total", 0) > 0 else 0.50
            return float(val)

    def generate_experiment(self) -> Optional[Experiment]:
        """
        Executes Strategy Selection to generate at most one new suggested Experiment.
        Returns None if cold-start observation, no eligible patterns, or all strategies cooled.
        """
        # 1. Cold-start check (Requirement 11)
        total_checkins = (
            self.db.query(TaskCheckin)
            .filter(TaskCheckin.user_id == self.user_id)
            .count()
        )
        if total_checkins < 3:
            return None

        # 2. Prioritized pattern selection (Requirement 9)
        eligible_patterns = self.select_eligible_patterns()
        if not eligible_patterns:
            return None

        selected_pattern = eligible_patterns[0]

        # 3. Strategy selection (Requirement 6, 7, 8)
        strategy = self.select_strategy_for_pattern(selected_pattern)
        if not strategy:
            return None

        # 4. Baseline & target computation (Requirement 12, 13)
        baseline_val = self.compute_baseline_for_metric(strategy.target_metric, self.ref_date_obj)
        target_val = strategy.compute_target(baseline_val)

        # 5. Build immutable pattern snapshot (Requirement 15)
        snapshot = build_pattern_snapshot(selected_pattern)

        # 6. Persist experiment with status="suggested"
        start_date_str = self.ref_date_str
        end_date_str = (self.ref_date_obj + timedelta(days=strategy.duration_days)).strftime("%Y-%m-%d")

        exp = Experiment(
            user_id=self.user_id,
            pattern_id=selected_pattern.id,
            pattern_snapshot=snapshot,
            title=strategy.default_title,
            description=strategy.default_description,
            hypothesis=strategy.default_hypothesis,
            intervention_type=strategy.intervention_type,
            start_date=start_date_str,
            end_date=end_date_str,
            target_metric=strategy.target_metric,
            baseline_value=baseline_val,
            target_value=target_val,
            status="suggested",
        )
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)
        return exp

    def _extract_date(self, date_str: Optional[str], fallback_dt: Optional[datetime]) -> Optional[date]:
        """Safely parses string YYYY-MM-DD or datetime to date."""
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                pass
        if fallback_dt:
            return fallback_dt.date()
        return None
