from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.experiment import Experiment, ExperimentResult
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.profile import BehaviorProfileManager

# Configuration constants for experiment measurement
# Pre-experiment baseline window: 7 days immediately preceding experiment start [start - 7, start - 1]
DEFAULT_EXPERIMENT_BASELINE_DAYS: int = 7

# Minimum valid observations required in both baseline and experiment periods to declare a confident conclusion.
# Initial engineering threshold aligned with pattern detection heuristics (sample_size >= 3).
# When evidence is below this threshold, evaluation concludes 'inconclusive'.
MIN_EXPERIMENT_OBSERVATIONS: int = 3


class ExperimentEvaluator:
    """
    Evaluates the outcome of a behavioral experiment strictly within time-bounded windows.
    - Pre-experiment baseline window: [start_date - baseline_days, start_date - 1 day]
    - Experiment observation window: [start_date, end_date]
    Never uses lifetime data to dilute experiment measurements.
    """

    def __init__(
        self,
        db: Session,
        user_id: str,
        baseline_days: int = DEFAULT_EXPERIMENT_BASELINE_DAYS,
        min_observations: int = MIN_EXPERIMENT_OBSERVATIONS,
    ):
        self.db = db
        self.user_id = user_id
        self.baseline_days = baseline_days
        self.min_observations = min_observations
        self.metrics_calc = BehaviorMetricsCalculator(db, user_id)
        self.profile_mgr = BehaviorProfileManager(db, user_id)

    def evaluate_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """
        Evaluates an active experiment using strictly time-bounded before vs. after metrics.
        Returns None if experiment does not exist or is not in 'active' status.
        """
        exp = (
            self.db.query(Experiment)
            .filter(Experiment.id == experiment_id, Experiment.user_id == self.user_id)
            .first()
        )
        if not exp:
            return None

        # Lifecycle safety: only 'active' experiments can be evaluated
        if exp.status != "active":
            return None

        # 1. Establish non-overlapping time boundaries
        try:
            start_dt = datetime.strptime(exp.start_date, "%Y-%m-%d").date()
        except Exception:
            start_dt = datetime.utcnow().date()

        baseline_start_date = (start_dt - timedelta(days=self.baseline_days)).strftime("%Y-%m-%d")
        baseline_end_date = (start_dt - timedelta(days=1)).strftime("%Y-%m-%d")

        experiment_start_date = exp.start_date
        experiment_end_date = exp.end_date or datetime.utcnow().strftime("%Y-%m-%d")

        # 2. Compute time-bounded metrics for baseline and experiment windows
        if exp.target_metric == "average_start_delay_minutes":
            baseline_stats = self.metrics_calc.compute_start_delay_stats(
                start_date=baseline_start_date,
                end_date=baseline_end_date,
            )
            experiment_stats = self.metrics_calc.compute_start_delay_stats(
                start_date=experiment_start_date,
                end_date=experiment_end_date,
            )

            baseline_sample = baseline_stats.get("sample_size", 0)
            experiment_sample = experiment_stats.get("sample_size", 0)

            before_value = baseline_stats.get("average_start_delay_minutes")
            after_value = experiment_stats.get("average_start_delay_minutes")
            is_lower_better = True
        else:
            # Default to completion_rate
            baseline_stats = self.metrics_calc.compute_task_completion_stats(
                start_date=baseline_start_date,
                end_date=baseline_end_date,
            )
            experiment_stats = self.metrics_calc.compute_task_completion_stats(
                start_date=experiment_start_date,
                end_date=experiment_end_date,
            )

            baseline_sample = baseline_stats.get("sample_size", 0)
            experiment_sample = experiment_stats.get("sample_size", 0)

            before_value = baseline_stats.get("completion_rate")
            after_value = experiment_stats.get("completion_rate")
            is_lower_better = False

        # 3. Check for zero data / insufficient observations
        if (
            before_value is None
            or after_value is None
            or baseline_sample < self.min_observations
            or experiment_sample < self.min_observations
        ):
            conclusion = "inconclusive"
            change_value = round(after_value - before_value, 2) if (before_value is not None and after_value is not None) else None
            percent_change = None

            reasons = []
            if baseline_sample < self.min_observations:
                reasons.append(f"baseline observations ({baseline_sample}) < {self.min_observations}")
            if experiment_sample < self.min_observations:
                reasons.append(f"experiment observations ({experiment_sample}) < {self.min_observations}")
            if after_value is None:
                reasons.append("no valid observations in experiment window")
            if before_value is None:
                reasons.append("no valid observations in baseline window")

            summary = (
                f"Experiment '{exp.title}' evaluated. Insufficient data: {', '.join(reasons)}. "
                f"Baseline: {before_value if before_value is not None else 'N/A'}, "
                f"Observed: {after_value if after_value is not None else 'N/A'}. "
                f"Outcome: inconclusive (no causality claimed)."
            )
        else:
            # 4. Sufficient evidence on both sides - calculate change
            change = round(after_value - before_value, 2)
            change_value = change

            if before_value != 0.0:
                percent_change = round(((after_value - before_value) / before_value) * 100, 1)
            else:
                # Baseline is zero: relative percentage is mathematically undefined
                percent_change = None

            # 5. Evaluate outcome based on metric directionality
            if is_lower_better:
                # Lower delay is better
                if change < -3.0:
                    conclusion = "positive"
                elif change > 5.0:
                    conclusion = "negative"
                else:
                    conclusion = "neutral"
            else:
                # Higher completion rate is better
                if change > 0.10:
                    conclusion = "positive"
                elif change < -0.10:
                    conclusion = "negative"
                else:
                    conclusion = "neutral"

            pct_str = f" ({'+' if percent_change > 0 else ''}{percent_change}% shift)" if percent_change is not None else ""
            summary = (
                f"Experiment '{exp.title}' evaluated. Baseline was {before_value}, observed experiment value was {after_value}{pct_str}. "
                f"Outcome: {conclusion}. (Observational before/after comparison; does not prove causality)."
            )

        # 6. Record result and mark experiment completed
        result = ExperimentResult(
            experiment_id=exp.id,
            metric_name=exp.target_metric,
            before_value=before_value,
            after_value=after_value,
            change_value=change_value,
            percent_change=percent_change,
            conclusion=conclusion,
            result_summary=summary,
        )
        self.db.add(result)
        exp.status = "completed"

        self.db.commit()
        self.db.refresh(result)

        # Refresh profile to incorporate learned experience
        self.profile_mgr.refresh_profile()

        return result
