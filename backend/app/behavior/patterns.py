from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.behavior import BehaviorPattern
from app.behavior.metrics import BehaviorMetricsCalculator


class PatternDetector:
    """
    Deterministic rule-based pattern detection engine.
    Detects recurring behavioral traits and assigns statistical confidence.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.calculator = BehaviorMetricsCalculator(db, user_id)

    def detect_and_update_patterns(self) -> List[BehaviorPattern]:
        """Runs all heuristic pattern detectors and stores results."""
        detected = []

        tod = self.calculator.compute_time_of_day_breakdown()
        delay_stats = self.calculator.compute_start_delay_stats()
        comp_stats = self.calculator.compute_task_completion_stats()
        top_apps = self.calculator.compute_top_distractions()
        proc_stats = self.calculator.compute_procrastination_stats()

        # 1. Afternoon Slump / Time of Day Variance
        afternoon = tod.get("afternoon", {})
        morning = tod.get("morning", {})
        if afternoon.get("total_tasks", 0) >= 2:
            aft_delay = afternoon.get("average_delay_minutes", 0)
            morn_delay = morning.get("average_delay_minutes", 0)
            aft_rate = afternoon.get("completion_rate", 0)
            morn_rate = morning.get("completion_rate", 0)

            if aft_delay > morn_delay + 15 or (aft_rate < morn_rate - 0.25 and aft_rate < 0.6):
                sample = afternoon["total_tasks"]
                confidence = "high" if sample >= 6 else ("moderate" if sample >= 3 else "low")
                p = self._upsert_pattern(
                    pattern_type="afternoon_slump",
                    title="Afternoon Focus Friction",
                    description=(
                        f"Tasks planned in the afternoon (12 PM–5 PM) experience higher start delays "
                        f"(avg {aft_delay} mins) and lower completion ({int(aft_rate*100)}%) compared to mornings."
                    ),
                    confidence=confidence,
                    sample_size=sample,
                    supporting_metrics={
                        "afternoon": afternoon,
                        "morning": morning,
                    },
                )
                detected.append(p)

        # 2. Consistent Start Delay Pattern
        if (
            delay_stats.get("sample_size", 0) >= 3
            and delay_stats.get("average_start_delay_minutes") is not None
            and delay_stats["average_start_delay_minutes"] >= 20
        ):
            sample = delay_stats["sample_size"]
            avg_d = delay_stats["average_start_delay_minutes"]
            confidence = "high" if sample >= 7 else "moderate"
            p = self._upsert_pattern(
                pattern_type="start_delay_resistance",
                title="Initial Task Initiation Friction",
                description=(
                    f"Across {sample} tracked sessions, the transition from planned time to actual work "
                    f"averages a delay of {avg_d} minutes."
                ),
                confidence=confidence,
                sample_size=sample,
                supporting_metrics=delay_stats,
            )
            detected.append(p)

        # 3. Primary Distraction Channel
        if top_apps and top_apps[0]["total_minutes"] >= 15:
            primary_app = top_apps[0]
            p = self._upsert_pattern(
                pattern_type="primary_distraction",
                title=f"Frequent Transition to {primary_app['app_name']}",
                description=(
                    f"{primary_app['app_name']} is currently the primary app visited during delay windows, "
                    f"totaling {primary_app['total_minutes']} minutes over {primary_app['sessions']} sessions."
                ),
                confidence="moderate" if primary_app["sessions"] >= 4 else "low",
                sample_size=primary_app["sessions"],
                supporting_metrics=primary_app,
            )
            detected.append(p)

        # 4. High Morning Momentum (Positive pattern)
        if morning.get("total_tasks", 0) >= 2 and morning.get("completion_rate", 0) >= 0.75:
            sample = morning["total_tasks"]
            confidence = "high" if sample >= 5 else "moderate"
            p = self._upsert_pattern(
                pattern_type="morning_momentum",
                title="Morning Clarity Window",
                description=(
                    f"Mornings (6 AM–12 PM) show your strongest consistency, with a "
                    f"{int(morning['completion_rate']*100)}% completion rate."
                ),
                confidence=confidence,
                sample_size=sample,
                supporting_metrics=morning,
            )
            detected.append(p)

        self.db.commit()
        return detected

    def _upsert_pattern(
        self,
        pattern_type: str,
        title: str,
        description: str,
        confidence: str,
        sample_size: int,
        supporting_metrics: Dict[str, Any],
    ) -> BehaviorPattern:
        """Finds existing active pattern of same type or creates a new one."""
        existing = (
            self.db.query(BehaviorPattern)
            .filter(
                BehaviorPattern.user_id == self.user_id,
                BehaviorPattern.pattern_type == pattern_type,
            )
            .first()
        )

        now = datetime.utcnow()
        if existing:
            existing.title = title
            existing.description = description
            existing.confidence = confidence
            existing.sample_size = sample_size
            existing.last_detected = now
            existing.supporting_metrics = supporting_metrics
            return existing
        else:
            new_p = BehaviorPattern(
                user_id=self.user_id,
                pattern_type=pattern_type,
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                first_detected=now,
                last_detected=now,
                status="active",
                supporting_metrics=supporting_metrics,
            )
            self.db.add(new_p)
            return new_p
