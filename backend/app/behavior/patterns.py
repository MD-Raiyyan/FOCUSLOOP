import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.behavior import BehaviorPattern
from app.models.checkin import TaskCheckin
from app.models.task import Task
from app.behavior.metrics import BehaviorMetricsCalculator


class PatternDetector:
    """
    Deterministic rule-based behavioral pattern detection engine (V2).
    
    Understands:
    1. Evidence Sufficiency (Event != Pattern)
    2. Recency Weighting & Continuous Decay
    3. Historical Baseline vs Current Behavior
    4. Contradiction & Improvement Detection
    5. Real Pattern Lifecycle State Transitions (active, improving, weakening, resolved, relapse/recovery)
    6. Contextual Comparison (Morning vs Afternoon vs Evening)
    7. Structured Supporting Evidence for Insights Graphs (Real Points Only)
    8. Deterministic Current Confidence (Distinguishes raw lifetime volume from current evidence)
    9. Truthful Inactive / Insufficient Evidence Transitions
    """

    RECENT_WINDOW_DAYS = 7
    RECENCY_HALF_LIFE_DAYS = 7.0

    def __init__(self, db: Session, user_id: str, ref_date: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.calculator = BehaviorMetricsCalculator(db, user_id)
        
        # Reference date for deterministic time-window evaluation
        if ref_date:
            try:
                self.ref_date_obj = datetime.strptime(ref_date, "%Y-%m-%d").date()
            except Exception:
                self.ref_date_obj = datetime.utcnow().date()
        else:
            self.ref_date_obj = datetime.utcnow().date()
            
        self.ref_date_str = self.ref_date_obj.strftime("%Y-%m-%d")
        self.recent_start_str = (self.ref_date_obj - timedelta(days=self.RECENT_WINDOW_DAYS)).strftime("%Y-%m-%d")
        self.historical_end_str = (self.ref_date_obj - timedelta(days=self.RECENT_WINDOW_DAYS + 1)).strftime("%Y-%m-%d")

    def detect_and_update_patterns(self) -> List[BehaviorPattern]:
        """
        Runs all pattern evaluators.
        Evaluates existing patterns in the database for state transitions,
        evaluates new candidate patterns, and persists results deterministically.
        """
        detected: List[BehaviorPattern] = []

        # 1. Afternoon Focus Friction / Afternoon Slump
        p_afternoon = self._evaluate_afternoon_slump()
        if p_afternoon:
            detected.append(p_afternoon)

        # 2. Consistent Start Delay Resistance
        p_delay = self._evaluate_start_delay_resistance()
        if p_delay:
            detected.append(p_delay)

        # 3. High Morning Momentum (Positive Pattern)
        p_morning = self._evaluate_morning_momentum()
        if p_morning:
            detected.append(p_morning)

        # 4. Primary Distraction Channel
        p_distract = self._evaluate_primary_distraction()
        if p_distract:
            detected.append(p_distract)

        self.db.commit()
        return detected

    def _get_existing_pattern(self, pattern_type: str) -> Optional[BehaviorPattern]:
        """Retrieves existing persisted pattern for this user and type."""
        return (
            self.db.query(BehaviorPattern)
            .filter(
                BehaviorPattern.user_id == self.user_id,
                BehaviorPattern.pattern_type == pattern_type,
            )
            .first()
        )

    def _calculate_current_confidence(
        self,
        total_sample_size: int,
        total_distinct_days: int,
        recent_sample_size: int,
        recent_distinct_days: int,
        status: str,
        contradiction_detected: bool = False,
    ) -> str:
        """
        Deterministic current confidence calculation rule:
        Distinguishes raw historical sample volume from strength of CURRENT evidence.
        Lifetime sample_size alone NEVER inflates current confidence to 'high'
        if current/recent evidence is sparse or developing.
        """
        # If no recent observations exist at all or status is inactive, current interpretation has zero recent support
        if recent_sample_size == 0 or status == "inactive":
            return "low"

        # In transition / improving / weakening states:
        # Confidence reflects how solidly the recent transition is supported by current evidence
        if status in ("improving", "weakening") or contradiction_detected:
            if recent_sample_size >= 8 and recent_distinct_days >= 4:
                return "high"
            elif recent_sample_size >= 3:
                return "moderate"
            else:
                return "low"

        # In resolved state:
        # High confidence requires both substantial lifetime evidence and sustained recent resolution
        if status == "resolved":
            if total_sample_size >= 12 and recent_sample_size >= 7 and recent_distinct_days >= 4:
                return "high"
            elif recent_sample_size >= 4:
                return "moderate"
            else:
                return "low"

        # In active state:
        # High confidence requires substantial lifetime evidence AND active recent confirmation
        if status == "active":
            # Both historical baseline and recent evidence are substantial and consistent
            if (
                total_sample_size >= 12
                and total_distinct_days >= 5
                and recent_sample_size >= 4
                and recent_distinct_days >= 2
            ):
                return "high"
            # Or purely recent intensive habit (e.g., new user with high frequency in recent window)
            elif recent_sample_size >= 8 and recent_distinct_days >= 4:
                return "high"
            elif (total_sample_size >= 6 and recent_sample_size >= 2) or (recent_sample_size >= 4):
                return "moderate"
            else:
                return "low"

        return "low"

    def _evaluate_afternoon_slump(self) -> Optional[BehaviorPattern]:
        """
        Evaluates Afternoon Focus Friction:
        Compares afternoon (12 PM–5 PM) performance to morning (6 AM–12 PM) and evening.
        Distinguishes historical slump from recent improvement, resolution, or inactivity.
        """
        existing = self._get_existing_pattern("afternoon_slump")
        
        # 1. Gather contextual evidence
        tod_all = self.calculator.compute_time_of_day_breakdown()
        tod_hist = self.calculator.compute_time_of_day_breakdown(end_date=self.historical_end_str)
        tod_recent = self.calculator.compute_time_of_day_breakdown(
            start_date=self.recent_start_str,
            end_date=self.ref_date_str,
        )

        afternoon_all = tod_all.get("afternoon", {})
        morning_all = tod_all.get("morning", {})
        evening_all = tod_all.get("evening", {})

        afternoon_hist = tod_hist.get("afternoon", {})
        morning_hist = tod_hist.get("morning", {})

        afternoon_rec = tod_recent.get("afternoon", {})
        morning_rec = tod_recent.get("morning", {})

        # Daily series for afternoon delay and completion (real points only)
        daily_delay_series = self.calculator.compute_daily_behavior_series(
            metric="start_delay",
            time_of_day="afternoon",
        )
        daily_comp_series = self.calculator.compute_daily_behavior_series(
            metric="completion_rate",
            time_of_day="afternoon",
        )

        total_aft_tasks = afternoon_all.get("total_tasks", 0)
        sample_size = total_aft_tasks

        # Count distinct dates with afternoon checkins
        distinct_dates = set(pt["date"] for pt in daily_delay_series).union(
            pt["date"] for pt in daily_comp_series
        )
        rec_distinct_dates = set(
            pt["date"] for pt in daily_delay_series if pt["date"] >= self.recent_start_str
        ).union(
            pt["date"] for pt in daily_comp_series if pt["date"] >= self.recent_start_str
        )

        # 2. Evidence Sufficiency Check
        # Requires at least 4 afternoon tasks across at least 2 distinct days
        is_sufficient = total_aft_tasks >= 4 and len(distinct_dates) >= 2

        if not is_sufficient:
            if existing is None:
                return None
            # If an existing pattern had been recorded, but total evidence is low,
            # maintain with low confidence and clear honest status
            confidence = "low"
            status = existing.status or "active"
            title = "Afternoon Focus Friction (Insufficient Evidence)"
            description = (
                f"Currently tracking afternoon sessions ({total_aft_tasks} recorded across {len(distinct_dates)} days). "
                "More sessions needed to confirm a persistent behavioral pattern."
            )
            return self._upsert_pattern(
                pattern_type="afternoon_slump",
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                status=status,
                supporting_metrics={
                    "pattern_id": existing.id,
                    "pattern_type": "afternoon_slump",
                    "status": status,
                    "confidence": confidence,
                    "sample_size": sample_size,
                    "insufficient_evidence": True,
                    "time_series": daily_delay_series,
                    "context_comparison": self._build_tod_context_comparison(morning_all, afternoon_all, evening_all),
                },
            )

        # 3. Metrics Extraction
        aft_delay_all = afternoon_all.get("average_delay_minutes", 0.0)
        morn_delay_all = morning_all.get("average_delay_minutes", 0.0)
        aft_rate_all = afternoon_all.get("completion_rate", 0.0)
        morn_rate_all = morning_all.get("completion_rate", 0.0)

        aft_delay_hist = afternoon_hist.get("average_delay_minutes", 0.0)
        morn_delay_hist = morning_hist.get("average_delay_minutes", 0.0)
        aft_tasks_hist = afternoon_hist.get("total_tasks", 0)

        aft_delay_rec = afternoon_rec.get("average_delay_minutes", 0.0)
        morn_delay_rec = morning_rec.get("average_delay_minutes", 0.0)
        aft_tasks_rec = afternoon_rec.get("total_tasks", 0)
        aft_rate_rec = afternoon_rec.get("completion_rate", 0.0)

        # Recency-weighted delay calculation
        delay_obs_tuples = [(pt["date"], pt["value"]) for pt in daily_delay_series]
        weighted_delay = self.calculator.calculate_recency_weighted_average(
            delay_obs_tuples,
            half_life_days=self.RECENCY_HALF_LIFE_DAYS,
            ref_date=self.ref_date_str,
        )

        # Overall/all-time slump condition
        all_time_slump = (
            aft_delay_all > morn_delay_all + 15
            or aft_delay_all >= 20.0
            or (aft_rate_all < morn_rate_all - 0.25 and aft_rate_all < 0.60)
        )

        # Recent slump condition
        recent_slump = aft_tasks_rec >= 2 and (
            aft_delay_rec > morn_delay_rec + 12
            or aft_delay_rec >= 20.0
            or (aft_rate_rec < morning_rec.get("completion_rate", 1.0) - 0.20 and aft_rate_rec < 0.60)
        )

        # 4. State Lifecycle Transitions & Contradiction Analysis
        prev_status = existing.status if existing else None
        new_status = "active"
        trend = "active"
        contradiction = False

        if existing is None:
            # New Pattern: must meet all-time friction AND not already contradicted recently
            if not all_time_slump:
                return None
            if aft_tasks_rec >= 3 and not recent_slump and aft_delay_rec < 15.0:
                # User already improved recently before first pattern creation
                new_status = "improving"
                trend = "improving"
                contradiction = True
            else:
                new_status = "active"
                trend = "active"
        else:
            # Existing Pattern: apply state machine
            if prev_status in ("active", None):
                # Insufficient current evidence: if no afternoon tasks exist in recent window
                if aft_tasks_rec == 0 and aft_tasks_hist >= 4:
                    new_status = "inactive"
                    trend = "inactive"
                # Contradiction check: recent window has >= 3 observations and no slump
                elif aft_tasks_rec >= 3 and not recent_slump:
                    contradiction = True
                    # If sustained across >= 5 recent tasks and delay is prompt (< 15 min)
                    if aft_tasks_rec >= 5 and aft_delay_rec < 15.0 and aft_rate_rec >= 0.65:
                        new_status = "resolved"
                        trend = "resolved"
                    else:
                        new_status = "improving"
                        trend = "improving"
                elif recent_slump or (weighted_delay is not None and weighted_delay >= 20.0):
                    new_status = "active"
                    trend = "active"
                else:
                    # Sparse recent data (< 3 tasks): keep previous status
                    new_status = prev_status or "active"
                    trend = "stable"
            elif prev_status == "improving":
                if aft_tasks_rec >= 3 and recent_slump:
                    # Relapse back to active
                    new_status = "active"
                    trend = "relapse"
                elif aft_tasks_rec >= 5 and aft_delay_rec < 15.0 and not recent_slump:
                    new_status = "resolved"
                    trend = "resolved"
                elif aft_tasks_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "improving"
                    trend = "improving"
            elif prev_status == "inactive":
                # Scenario D: Inactive pattern gets new evidence
                if aft_tasks_rec >= 3 and (recent_slump or aft_delay_rec >= 20.0):
                    new_status = "active"
                    trend = "active"
                elif aft_tasks_rec >= 5 and aft_delay_rec < 15.0 and aft_rate_rec >= 0.65 and not recent_slump:
                    new_status = "resolved"
                    trend = "resolved"
                elif aft_tasks_rec >= 3 and not recent_slump:
                    new_status = "improving"
                    trend = "improving"
                elif aft_tasks_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    # Sparse observations (1-2 tasks): remains inactive
                    new_status = "inactive"
                    trend = "inactive"
            elif prev_status == "resolved":
                if aft_tasks_rec >= 3 and recent_slump:
                    # Friction returned
                    new_status = "active"
                    trend = "relapse"
                else:
                    new_status = "resolved"
                    trend = "resolved"

        # Deterministic Current Confidence
        confidence = self._calculate_current_confidence(
            total_sample_size=sample_size,
            total_distinct_days=len(distinct_dates),
            recent_sample_size=aft_tasks_rec,
            recent_distinct_days=len(rec_distinct_dates),
            status=new_status,
            contradiction_detected=contradiction,
        )

        # 5. Descriptive Content Tailored to State
        first_date = min(distinct_dates) if distinct_dates else self.ref_date_str
        last_date = max(distinct_dates) if distinct_dates else self.ref_date_str

        if new_status == "inactive":
            title = "Afternoon Focus Friction (Inactive)"
            description = (
                f"Afternoon focus friction was observed historically across {sample_size} sessions, "
                "but no recent afternoon sessions were tracked in the last 7 days. "
                "More recent observations are needed to determine if this pattern persists."
            )
        elif new_status == "resolved":
            title = "Afternoon Focus Friction (Resolved)"
            description = (
                f"Recent afternoon sessions show consistent initiation promptness (avg {aft_delay_rec} mins delay, "
                f"{int(aft_rate_rec*100)}% completion), successfully resolving the earlier friction."
            )
        elif new_status == "improving":
            title = "Afternoon Focus Friction (Improving)"
            description = (
                f"Your recent afternoon start delays have improved to avg {aft_delay_rec} mins (down from "
                f"historical avg {aft_delay_hist} mins across {aft_tasks_hist} earlier sessions)."
            )
        else:
            title = "Afternoon Focus Friction"
            effective_delay = round(weighted_delay, 1) if weighted_delay is not None else aft_delay_all
            description = (
                f"Tasks planned in the afternoon (12 PM–5 PM) experience higher start delays "
                f"(recency-weighted avg {effective_delay} mins) and lower completion ({int(aft_rate_all*100)}%) compared to mornings."
            )

        # 6. Structured Evidence & Graph Payload
        context_comparison = self._build_tod_context_comparison(morning_all, afternoon_all, evening_all)

        supporting_metrics = {
            "pattern_type": "afternoon_slump",
            "status": new_status,
            "confidence": confidence,
            "sample_size": sample_size,
            "effective_recent_sample_size": aft_tasks_rec,
            "distinct_days": len(distinct_dates),
            "recent_distinct_days": len(rec_distinct_dates),
            "first_observed_date": first_date,
            "last_observed_date": last_date,
            "trend": trend,
            "metric_name": "average_start_delay_minutes",
            "unit": "min",
            "contradiction_detected": contradiction,
            "insufficient_evidence": False,
            "insufficient_current_evidence": (new_status == "inactive" or trend == "inactive"),
            "lifecycle_category": "insufficient_current_evidence" if (new_status == "inactive" or trend == "inactive") else ("historical_resolved" if new_status in ("resolved", "archived") else "current_pattern"),
            "explanation": description,
            "context_comparison": context_comparison,
            "time_series": daily_delay_series,
            "historical_window": {
                "label": "Historical Baseline (>7d ago)",
                "value": aft_delay_hist if aft_tasks_hist > 0 else None,
                "sample_size": aft_tasks_hist,
                "unit": "min",
            },
            "recent_window": {
                "label": "Recent (Last 7d)",
                "value": aft_delay_rec if aft_tasks_rec > 0 else None,
                "sample_size": aft_tasks_rec,
                "weighted_value": weighted_delay,
                "unit": "min",
            },
            "afternoon_completion_series": daily_comp_series,
        }

        pattern = self._upsert_pattern(
            pattern_type="afternoon_slump",
            title=title,
            description=description,
            confidence=confidence,
            sample_size=sample_size,
            status=new_status,
            supporting_metrics=supporting_metrics,
        )
        supporting_metrics["pattern_id"] = pattern.id
        pattern.supporting_metrics = supporting_metrics
        return pattern

    def _evaluate_start_delay_resistance(self) -> Optional[BehaviorPattern]:
        """
        Evaluates Initial Task Initiation Friction:
        Analyzes start delay across all tasks over time, with recency weighting,
        historical vs recent comparison, and state transitions (active, improving, resolved, inactive).
        """
        existing = self._get_existing_pattern("start_delay_resistance")

        delay_all = self.calculator.compute_start_delay_stats()
        delay_hist = self.calculator.compute_start_delay_stats(end_date=self.historical_end_str)
        delay_rec = self.calculator.compute_start_delay_stats(
            start_date=self.recent_start_str,
            end_date=self.ref_date_str,
        )

        daily_series = self.calculator.compute_daily_behavior_series(metric="start_delay")
        sample_size = delay_all.get("sample_size", 0)
        distinct_dates = set(pt["date"] for pt in daily_series)
        rec_distinct_dates = set(pt["date"] for pt in daily_series if pt["date"] >= self.recent_start_str)

        # Evidence Sufficiency: at least 5 delay observations across at least 3 distinct days
        is_sufficient = sample_size >= 5 and len(distinct_dates) >= 3

        if not is_sufficient:
            if existing is None:
                return None
            confidence = "low"
            status = existing.status or "active"
            title = "Initial Task Initiation Friction (Insufficient Evidence)"
            description = (
                f"Currently tracking start delays ({sample_size} observations across {len(distinct_dates)} days). "
                "At least 5 sessions across 3+ days are required to confirm this habit."
            )
            return self._upsert_pattern(
                pattern_type="start_delay_resistance",
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                status=status,
                supporting_metrics={
                    "pattern_id": existing.id,
                    "pattern_type": "start_delay_resistance",
                    "status": status,
                    "confidence": confidence,
                    "sample_size": sample_size,
                    "insufficient_evidence": True,
                    "time_series": daily_series,
                },
            )

        avg_delay_all = delay_all.get("average_start_delay_minutes", 0.0)
        avg_delay_hist = delay_hist.get("average_start_delay_minutes")
        sample_hist = delay_hist.get("sample_size", 0)

        avg_delay_rec = delay_rec.get("average_start_delay_minutes")
        sample_rec = delay_rec.get("sample_size", 0)

        # Recency-weighted average delay
        delay_obs_tuples = [(pt["date"], pt["value"]) for pt in daily_series]
        weighted_delay = self.calculator.calculate_recency_weighted_average(
            delay_obs_tuples,
            half_life_days=self.RECENCY_HALF_LIFE_DAYS,
            ref_date=self.ref_date_str,
        )

        # Lifecycle state transitions
        prev_status = existing.status if existing else None
        new_status = "active"
        trend = "active"
        contradiction = False

        hist_baseline = avg_delay_hist if avg_delay_hist is not None else avg_delay_all

        if existing is None:
            effective_start_delay = weighted_delay if weighted_delay is not None else avg_delay_all
            if effective_start_delay < 20.0 and avg_delay_all < 20.0:
                return None
            if sample_rec >= 3 and avg_delay_rec is not None and avg_delay_rec < 15.0:
                new_status = "improving"
                trend = "improving"
                contradiction = True
            else:
                new_status = "active"
                trend = "active"
        else:
            if prev_status in ("active", None):
                # Insufficient current evidence: if no tasks tracked in recent window
                if sample_rec == 0 and sample_hist >= 5:
                    new_status = "inactive"
                    trend = "inactive"
                elif sample_rec >= 3 and avg_delay_rec is not None:
                    # Improvement criteria: >= 25% lower than historical baseline or < 18 min
                    if avg_delay_rec <= 0.75 * hist_baseline or avg_delay_rec < 18.0:
                        contradiction = True
                        if sample_rec >= 5 and avg_delay_rec < 15.0:
                            new_status = "resolved"
                            trend = "resolved"
                        else:
                            new_status = "improving"
                            trend = "improving"
                    elif avg_delay_rec >= 20.0 or (weighted_delay is not None and weighted_delay >= 20.0):
                        new_status = "active"
                        trend = "active"
                    else:
                        new_status = prev_status or "active"
                        trend = "stable"
                else:
                    new_status = prev_status or "active"
                    trend = "stable"
            elif prev_status == "improving":
                if sample_rec >= 3 and avg_delay_rec is not None and avg_delay_rec >= 20.0:
                    new_status = "active"
                    trend = "relapse"
                elif sample_rec >= 5 and avg_delay_rec is not None and avg_delay_rec < 15.0:
                    new_status = "resolved"
                    trend = "resolved"
                elif sample_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "improving"
                    trend = "improving"
            elif prev_status == "inactive":
                # Scenario D: Inactive pattern gets new evidence
                if sample_rec >= 3 and avg_delay_rec is not None and (avg_delay_rec >= 20.0 or (weighted_delay is not None and weighted_delay >= 20.0)):
                    new_status = "active"
                    trend = "active"
                elif sample_rec >= 5 and avg_delay_rec is not None and avg_delay_rec < 15.0:
                    new_status = "resolved"
                    trend = "resolved"
                elif sample_rec >= 3 and avg_delay_rec is not None and (avg_delay_rec <= 0.75 * hist_baseline or avg_delay_rec < 18.0):
                    new_status = "improving"
                    trend = "improving"
                elif sample_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    # Sparse observations (1-2 tasks): remains inactive
                    new_status = "inactive"
                    trend = "inactive"
            elif prev_status == "resolved":
                if sample_rec >= 3 and avg_delay_rec is not None and avg_delay_rec >= 20.0:
                    new_status = "active"
                    trend = "relapse"
                else:
                    new_status = "resolved"
                    trend = "resolved"

        # Deterministic Current Confidence
        confidence = self._calculate_current_confidence(
            total_sample_size=sample_size,
            total_distinct_days=len(distinct_dates),
            recent_sample_size=sample_rec,
            recent_distinct_days=len(rec_distinct_dates),
            status=new_status,
            contradiction_detected=contradiction,
        )

        first_date = min(distinct_dates) if distinct_dates else self.ref_date_str
        last_date = max(distinct_dates) if distinct_dates else self.ref_date_str

        if new_status == "inactive":
            title = "Task Initiation Friction (Inactive)"
            description = (
                f"Initial hesitation was observed historically across {sample_size} sessions, "
                "but no task start delays were recorded in the recent 7-day window. "
                "More recent observations are needed to determine if this pattern persists."
            )
        elif new_status == "resolved":
            title = "Task Initiation Friction (Resolved)"
            description = (
                f"Across recent sessions (avg delay {avg_delay_rec} mins across {sample_rec} sessions), "
                "task initiation promptness has normalized, resolving the earlier hesitation pattern."
            )
        elif new_status == "improving":
            title = "Task Initiation Friction (Improving)"
            description = (
                f"Your recent task start delay averages {avg_delay_rec} mins (down from "
                f"historical baseline of {hist_baseline} mins across {sample_hist} earlier sessions)."
            )
        else:
            title = "Initial Task Initiation Friction"
            effective_delay = round(weighted_delay, 1) if weighted_delay is not None else avg_delay_all
            description = (
                f"Across {sample_size} tracked sessions, the transition from planned time to actual work "
                f"averages a delay of {effective_delay} minutes (recency-weighted)."
            )

        tod_all = self.calculator.compute_time_of_day_breakdown()
        context_comparison = self._build_tod_context_comparison(
            tod_all.get("morning", {}),
            tod_all.get("afternoon", {}),
            tod_all.get("evening", {}),
        )

        supporting_metrics = {
            "pattern_type": "start_delay_resistance",
            "status": new_status,
            "confidence": confidence,
            "sample_size": sample_size,
            "effective_recent_sample_size": sample_rec,
            "distinct_days": len(distinct_dates),
            "recent_distinct_days": len(rec_distinct_dates),
            "first_observed_date": first_date,
            "last_observed_date": last_date,
            "trend": trend,
            "metric_name": "average_start_delay_minutes",
            "unit": "min",
            "contradiction_detected": contradiction,
            "insufficient_evidence": False,
            "insufficient_current_evidence": (new_status == "inactive" or trend == "inactive"),
            "lifecycle_category": "insufficient_current_evidence" if (new_status == "inactive" or trend == "inactive") else ("historical_resolved" if new_status in ("resolved", "archived") else "current_pattern"),
            "explanation": description,
            "context_comparison": context_comparison,
            "time_series": daily_series,
            "historical_window": {
                "label": "Historical Baseline (>7d ago)",
                "value": avg_delay_hist,
                "sample_size": sample_hist,
                "unit": "min",
            },
            "recent_window": {
                "label": "Recent (Last 7d)",
                "value": avg_delay_rec,
                "sample_size": sample_rec,
                "weighted_value": weighted_delay,
                "unit": "min",
            },
        }

        pattern = self._upsert_pattern(
            pattern_type="start_delay_resistance",
            title=title,
            description=description,
            confidence=confidence,
            sample_size=sample_size,
            status=new_status,
            supporting_metrics=supporting_metrics,
        )
        supporting_metrics["pattern_id"] = pattern.id
        pattern.supporting_metrics = supporting_metrics
        return pattern

    def _evaluate_morning_momentum(self) -> Optional[BehaviorPattern]:
        """
        Evaluates High Morning Momentum (Positive Pattern V2):
        Detects consistent morning execution (>= 75% completion rate),
        with recency decay, historical vs recent comparison, weakening,
        resolved/inactive state, and recovery semantics.
        """
        existing = self._get_existing_pattern("morning_momentum")

        tod_all = self.calculator.compute_time_of_day_breakdown()
        morning_all = tod_all.get("morning", {})
        sample_size = morning_all.get("total_tasks", 0)

        daily_series = self.calculator.compute_daily_behavior_series(
            metric="completion_rate",
            time_of_day="morning",
        )
        distinct_dates = set(pt["date"] for pt in daily_series)
        rec_distinct_dates = set(pt["date"] for pt in daily_series if pt["date"] >= self.recent_start_str)

        # Evidence Sufficiency: at least 4 morning tasks across at least 2 distinct days
        is_sufficient = sample_size >= 4 and len(distinct_dates) >= 2

        if not is_sufficient:
            if existing is None:
                return None
            confidence = "low"
            status = existing.status or "active"
            title = "Morning Clarity Window (Insufficient Evidence)"
            description = (
                f"Currently tracking morning focus sessions ({sample_size} recorded across {len(distinct_dates)} days). "
                "More morning sessions are needed to establish recurring momentum."
            )
            return self._upsert_pattern(
                pattern_type="morning_momentum",
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                status=status,
                supporting_metrics={
                    "pattern_id": existing.id,
                    "pattern_type": "morning_momentum",
                    "status": status,
                    "confidence": confidence,
                    "sample_size": sample_size,
                    "insufficient_evidence": True,
                    "time_series": daily_series,
                },
            )

        morn_rate_all = morning_all.get("completion_rate", 0.0)

        # Historical vs Recent breakdown
        tod_hist = self.calculator.compute_time_of_day_breakdown(end_date=self.historical_end_str)
        tod_recent = self.calculator.compute_time_of_day_breakdown(
            start_date=self.recent_start_str,
            end_date=self.ref_date_str,
        )
        morning_hist = tod_hist.get("morning", {})
        morning_rec = tod_recent.get("morning", {})

        morn_rate_hist = morning_hist.get("completion_rate", morn_rate_all)
        morn_tasks_hist = morning_hist.get("total_tasks", 0)

        morn_rate_rec = morning_rec.get("completion_rate")
        morn_tasks_rec = morning_rec.get("total_tasks", 0)

        # Recency-weighted completion rate calculation
        comp_obs_tuples = [(pt["date"], pt["value"] / 100.0) for pt in daily_series]
        weighted_rate = self.calculator.calculate_recency_weighted_average(
            comp_obs_tuples,
            half_life_days=self.RECENCY_HALF_LIFE_DAYS,
            ref_date=self.ref_date_str,
        )

        prev_status = existing.status if existing else None
        new_status = "active"
        trend = "active"
        contradiction = False

        if existing is None:
            # New Pattern: requires all-time completion >= 75%
            if morn_rate_all < 0.75:
                return None
            if morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec < 0.60:
                # Recently declining before first creation
                return None
            new_status = "active"
            trend = "active"
        else:
            # Existing Pattern: Positive lifecycle state machine
            if prev_status in ("active", None):
                if morn_tasks_rec == 0 and morn_tasks_hist >= 4:
                    # No morning tasks in recent window: inactive
                    new_status = "inactive"
                    trend = "inactive"
                elif morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec < 0.60:
                    contradiction = True
                    if morn_tasks_rec >= 5 and morn_rate_rec < 0.50:
                        new_status = "resolved"
                        trend = "resolved"
                    else:
                        new_status = "weakening"
                        trend = "weakening"
                elif (weighted_rate is not None and weighted_rate >= 0.70) or morn_rate_all >= 0.75:
                    new_status = "active"
                    trend = "active"
                else:
                    new_status = "weakening"
                    trend = "weakening"
            elif prev_status == "weakening":
                if morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec >= 0.75:
                    # Positive recovery
                    new_status = "active"
                    trend = "recovery"
                elif morn_tasks_rec >= 5 and morn_rate_rec is not None and morn_rate_rec < 0.50:
                    new_status = "resolved"
                    trend = "resolved"
                elif morn_tasks_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "weakening"
                    trend = "weakening"
            elif prev_status == "inactive":
                # Scenario D: Inactive morning momentum gets new evidence
                if morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec >= 0.75:
                    new_status = "active"
                    trend = "recovery"
                elif morn_tasks_rec >= 5 and morn_rate_rec is not None and morn_rate_rec < 0.50:
                    new_status = "resolved"
                    trend = "resolved"
                elif morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec < 0.60:
                    new_status = "weakening"
                    trend = "weakening"
                elif morn_tasks_rec == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "inactive"
                    trend = "inactive"
            elif prev_status == "resolved":
                if morn_tasks_rec >= 3 and morn_rate_rec is not None and morn_rate_rec >= 0.75 and (weighted_rate is None or weighted_rate >= 0.70):
                    # Positive momentum returns
                    new_status = "active"
                    trend = "recovery"
                else:
                    new_status = "resolved"
                    trend = "resolved"

        # Deterministic Current Confidence
        confidence = self._calculate_current_confidence(
            total_sample_size=sample_size,
            total_distinct_days=len(distinct_dates),
            recent_sample_size=morn_tasks_rec,
            recent_distinct_days=len(rec_distinct_dates),
            status=new_status,
            contradiction_detected=contradiction,
        )

        first_date = min(distinct_dates) if distinct_dates else self.ref_date_str
        last_date = max(distinct_dates) if distinct_dates else self.ref_date_str

        if new_status == "inactive":
            title = "Morning Clarity Window (Inactive)"
            description = (
                f"Morning momentum was observed historically across {sample_size} sessions, "
                "but no morning sessions were tracked in the last 7 days. "
                "More recent observations are needed to determine if this pattern persists."
            )
        elif new_status == "resolved":
            title = "Morning Clarity Window (Resolved)"
            rec_pct = int((morn_rate_rec or 0) * 100)
            hist_pct = int(morn_rate_hist * 100)
            description = (
                f"Morning completion has normalized to {rec_pct}% across recent sessions "
                f"(down from historical baseline {hist_pct}%), so morning momentum is no longer an active driver."
            )
        elif new_status == "weakening":
            title = "Morning Clarity Window (Weakening)"
            rec_pct = int((morn_rate_rec or 0) * 100)
            hist_pct = int(morn_rate_hist * 100)
            description = (
                f"Recent morning completion has dipped to {rec_pct}% across {morn_tasks_rec} sessions "
                f"(down from historical baseline of {hist_pct}% across {morn_tasks_hist} earlier sessions)."
            )
        else:
            title = "Morning Clarity Window"
            effective_pct = round(weighted_rate * 100, 1) if weighted_rate is not None else int(morn_rate_all * 100)
            description = (
                f"Mornings (6 AM–12 PM) show your strongest consistency, with a "
                f"{effective_pct}% completion rate across {sample_size} tracked sessions."
            )

        context_comparison = self._build_tod_context_comparison(
            morning_all,
            tod_all.get("afternoon", {}),
            tod_all.get("evening", {}),
            metric_type="completion_rate",
        )

        supporting_metrics = {
            "pattern_type": "morning_momentum",
            "status": new_status,
            "confidence": confidence,
            "sample_size": sample_size,
            "effective_recent_sample_size": morn_tasks_rec,
            "distinct_days": len(distinct_dates),
            "recent_distinct_days": len(rec_distinct_dates),
            "first_observed_date": first_date,
            "last_observed_date": last_date,
            "trend": trend,
            "metric_name": "completion_rate",
            "unit": "%",
            "contradiction_detected": contradiction,
            "insufficient_evidence": False,
            "insufficient_current_evidence": (new_status == "inactive" or trend == "inactive"),
            "lifecycle_category": "insufficient_current_evidence" if (new_status == "inactive" or trend == "inactive") else ("historical_resolved" if new_status in ("resolved", "archived") else "current_pattern"),
            "explanation": description,
            "context_comparison": context_comparison,
            "time_series": daily_series,
            "historical_window": {
                "label": "Historical Baseline (>7d ago)",
                "value": round(morn_rate_hist * 100, 1) if morn_tasks_hist > 0 else None,
                "sample_size": morn_tasks_hist,
                "unit": "%",
            },
            "recent_window": {
                "label": "Recent (Last 7d)",
                "value": round(morn_rate_rec * 100, 1) if morn_tasks_rec > 0 else None,
                "sample_size": morn_tasks_rec,
                "weighted_value": round(weighted_rate * 100, 1) if weighted_rate is not None else None,
                "unit": "%",
            },
        }

        pattern = self._upsert_pattern(
            pattern_type="morning_momentum",
            title=title,
            description=description,
            confidence=confidence,
            sample_size=sample_size,
            status=new_status,
            supporting_metrics=supporting_metrics,
        )
        supporting_metrics["pattern_id"] = pattern.id
        pattern.supporting_metrics = supporting_metrics
        return pattern

    def _evaluate_primary_distraction(self) -> Optional[BehaviorPattern]:
        """
        Evaluates Primary Distraction Channel (V2):
        Recency-aware screen distraction detection with historical baseline vs recent window,
        real daily time-series points, exponential decay weighting, and full lifecycle state transitions
        (active, improving, resolved, relapse, inactive).
        """
        existing = self._get_existing_pattern("primary_distraction")
        
        top_apps_all = self.calculator.compute_top_distractions()
        top_apps_hist = self.calculator.compute_top_distractions(end_date=self.historical_end_str)
        top_apps_rec = self.calculator.compute_top_distractions(
            start_date=self.recent_start_str,
            end_date=self.ref_date_str,
        )

        # 1. Determine primary distraction app
        target_app = None
        if top_apps_rec and top_apps_rec[0]["total_minutes"] >= 15.0 and top_apps_rec[0]["sessions"] >= 3:
            target_app = top_apps_rec[0]["app_name"]
        elif existing is not None and existing.supporting_metrics:
            target_app = existing.supporting_metrics.get("primary_app", {}).get("app_name")
            if not target_app and top_apps_all:
                target_app = top_apps_all[0]["app_name"]
        elif top_apps_all and top_apps_all[0]["total_minutes"] >= 15.0 and top_apps_all[0]["sessions"] >= 3:
            target_app = top_apps_all[0]["app_name"]

        if not target_app:
            if existing is None:
                return None
            status = "inactive"
            return self._upsert_pattern(
                pattern_type="primary_distraction",
                title="Primary Distraction (Inactive)",
                description="No recent screen distraction was recorded in the last 7 days. More observations are needed to determine if this pattern persists.",
                confidence="low",
                sample_size=existing.sample_size or 0,
                status=status,
                supporting_metrics={
                    "pattern_id": existing.id,
                    "pattern_type": "primary_distraction",
                    "status": status,
                    "confidence": "low",
                    "sample_size": existing.sample_size or 0,
                    "insufficient_evidence": False,
                    "insufficient_current_evidence": True,
                    "lifecycle_category": "insufficient_current_evidence",
                    "trend": "inactive",
                    "time_series": [],
                },
            )

        # 2. Daily time series for target app (Real Points Only)
        daily_series = self.calculator.compute_daily_distraction_series(app_name=target_app)
        sample_size = sum(pt["sample_size"] for pt in daily_series)
        total_mins = round(sum(pt["value"] for pt in daily_series), 1)
        distinct_dates = set(pt["date"] for pt in daily_series)

        # Split into historical and recent series
        rec_pts = [pt for pt in daily_series if pt["date"] >= self.recent_start_str]
        hist_pts = [pt for pt in daily_series if pt["date"] <= self.historical_end_str]

        rec_mins = round(sum(pt["value"] for pt in rec_pts), 1)
        rec_sessions = sum(pt["sample_size"] for pt in rec_pts)
        rec_distinct_dates = set(pt["date"] for pt in rec_pts)

        hist_mins = round(sum(pt["value"] for pt in hist_pts), 1)
        hist_sessions = sum(pt["sample_size"] for pt in hist_pts)

        # Recency-weighted daily minutes
        obs_tuples = [(pt["date"], pt["value"]) for pt in daily_series]
        weighted_mins = self.calculator.calculate_recency_weighted_average(
            obs_tuples,
            half_life_days=self.RECENCY_HALF_LIFE_DAYS,
            ref_date=self.ref_date_str,
        )

        # 3. Evidence Sufficiency Check
        is_sufficient = (sample_size >= 3 and total_mins >= 15.0) or (rec_sessions >= 3 and rec_mins >= 15.0)

        if not is_sufficient:
            if existing is None:
                return None
            confidence = "low"
            status = "inactive"
            title = f"Frequent Transition to {target_app} (Insufficient Evidence)"
            description = (
                f"Screen tracking for {target_app} ({total_mins} mins across {sample_size} sessions) "
                "does not meet the threshold to establish a current recurring distraction pattern."
            )
            return self._upsert_pattern(
                pattern_type="primary_distraction",
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                status=status,
                supporting_metrics={
                    "pattern_id": existing.id,
                    "pattern_type": "primary_distraction",
                    "status": status,
                    "confidence": confidence,
                    "sample_size": sample_size,
                    "insufficient_evidence": True,
                    "insufficient_current_evidence": True,
                    "lifecycle_category": "insufficient_current_evidence",
                    "trend": "inactive",
                    "time_series": daily_series,
                },
            )

        # 4. Lifecycle state transitions
        prev_status = existing.status if existing else None
        new_status = "active"
        trend = "active"
        contradiction = False

        if existing is None:
            if rec_sessions >= 3 and rec_mins >= 15.0:
                new_status = "active"
                trend = "active"
            elif sample_size >= 3 and total_mins >= 15.0 and rec_sessions >= 2 and rec_mins >= 10.0:
                new_status = "active"
                trend = "active"
            elif sample_size >= 3 and total_mins >= 15.0 and rec_sessions == 0:
                new_status = "inactive"
                trend = "inactive"
            elif sample_size >= 3 and total_mins >= 15.0 and rec_mins < 10.0:
                new_status = "improving"
                trend = "improving"
                contradiction = True
            else:
                return None
        else:
            if prev_status in ("active", None):
                # Historical distraction existed (>= 15 min), but zero recent usage
                if rec_sessions == 0 and hist_sessions >= 3:
                    new_status = "inactive"
                    trend = "inactive"
                elif hist_sessions >= 3 and hist_mins >= 15.0 and rec_mins < 10.0:
                    contradiction = True
                    if rec_sessions >= 3 and rec_mins < 5.0 and len(rec_distinct_dates) >= 3:
                        new_status = "resolved"
                        trend = "resolved"
                    else:
                        new_status = "improving"
                        trend = "improving"
                elif rec_sessions >= 3 and rec_mins >= 15.0:
                    new_status = "active"
                    trend = "active"
                else:
                    new_status = prev_status or "active"
                    trend = "stable"
            elif prev_status == "improving":
                if rec_sessions >= 3 and rec_mins >= 15.0:
                    new_status = "active"
                    trend = "relapse"
                elif rec_sessions >= 3 and rec_mins < 5.0 and len(rec_distinct_dates) >= 3:
                    new_status = "resolved"
                    trend = "resolved"
                elif rec_sessions == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "improving"
                    trend = "improving"
            elif prev_status == "inactive":
                # Scenario D: Inactive distraction gets new evidence
                if rec_sessions >= 3 and rec_mins >= 15.0:
                    new_status = "active"
                    trend = "relapse"
                elif rec_sessions >= 3 and rec_mins < 5.0 and len(rec_distinct_dates) >= 3:
                    new_status = "resolved"
                    trend = "resolved"
                elif rec_sessions >= 3 and rec_mins < 10.0:
                    new_status = "improving"
                    trend = "improving"
                elif rec_sessions == 0:
                    new_status = "inactive"
                    trend = "inactive"
                else:
                    new_status = "inactive"
                    trend = "inactive"
            elif prev_status == "resolved":
                if rec_sessions >= 3 and rec_mins >= 15.0:
                    # Relapse: Distraction habit returned
                    new_status = "active"
                    trend = "relapse"
                else:
                    new_status = "resolved"
                    trend = "resolved"

        # Deterministic Current Confidence
        confidence = self._calculate_current_confidence(
            total_sample_size=sample_size,
            total_distinct_days=len(distinct_dates),
            recent_sample_size=rec_sessions,
            recent_distinct_days=len(rec_distinct_dates),
            status=new_status,
            contradiction_detected=contradiction,
        )

        first_date = min(distinct_dates) if distinct_dates else self.ref_date_str
        last_date = max(distinct_dates) if distinct_dates else self.ref_date_str

        if new_status == "inactive":
            title = f"Frequent Transition to {target_app} (Inactive)"
            description = (
                f"Screen distraction on {target_app} was tracked historically ({total_mins} mins across {sample_size} sessions), "
                "but no screen usage was recorded in the last 7 days. "
                "More recent observations are needed to determine if this pattern persists."
            )
        elif new_status == "resolved":
            title = f"Frequent Transition to {target_app} (Resolved)"
            description = (
                f"Screen usage on {target_app} has reduced to {rec_mins} mins over the last 7 days "
                f"(down from historical baseline of {hist_mins} mins across {hist_sessions} earlier sessions), resolving this distraction habit."
            )
        elif new_status == "improving":
            title = f"Frequent Transition to {target_app} (Improving)"
            description = (
                f"Screen usage on {target_app} has dropped to {rec_mins} mins recently "
                f"(down from historical baseline of {hist_mins} mins across {hist_sessions} earlier sessions)."
            )
        else:
            title = f"Frequent Transition to {target_app}"
            effective_mins = round(weighted_mins, 1) if weighted_mins is not None else rec_mins
            description = (
                f"{target_app} is currently the primary app visited during delay windows, "
                f"totaling {effective_mins} mins recently ({total_mins} mins across {sample_size} total sessions)."
            )

        app_comparison = [
            {
                "context": app["app_name"],
                "label": app["app_name"],
                "value": app["total_minutes"],
                "sample_size": app["sessions"],
                "unit": "min",
            }
            for app in (top_apps_rec[:4] if top_apps_rec else top_apps_all[:4])
        ]

        primary_app_data = {
            "app_name": target_app,
            "total_minutes": total_mins,
            "sessions": sample_size,
            "recent_minutes": rec_mins,
            "recent_sessions": rec_sessions,
        }

        supporting_metrics = {
            "pattern_type": "primary_distraction",
            "status": new_status,
            "confidence": confidence,
            "sample_size": sample_size,
            "effective_recent_sample_size": rec_sessions,
            "distinct_days": len(distinct_dates),
            "recent_distinct_days": len(rec_distinct_dates),
            "first_observed_date": first_date,
            "last_observed_date": last_date,
            "trend": trend,
            "metric_name": "distraction_duration_minutes",
            "unit": "min",
            "contradiction_detected": contradiction,
            "insufficient_evidence": False,
            "insufficient_current_evidence": (new_status == "inactive" or trend == "inactive"),
            "lifecycle_category": "insufficient_current_evidence" if (new_status == "inactive" or trend == "inactive") else ("historical_resolved" if new_status in ("resolved", "archived") else "current_pattern"),
            "explanation": description,
            "context_comparison": app_comparison,
            "time_series": daily_series,
            "primary_app": primary_app_data,
            "historical_window": {
                "label": "Historical Baseline (>7d ago)",
                "value": hist_mins if hist_sessions > 0 else None,
                "sample_size": hist_sessions,
                "unit": "min",
            },
            "recent_window": {
                "label": "Recent (Last 7d)",
                "value": rec_mins if rec_sessions > 0 else None,
                "sample_size": rec_sessions,
                "weighted_value": weighted_mins,
                "unit": "min",
            },
        }

        pattern = self._upsert_pattern(
            pattern_type="primary_distraction",
            title=title,
            description=description,
            confidence=confidence,
            sample_size=sample_size,
            status=new_status,
            supporting_metrics=supporting_metrics,
        )
        supporting_metrics["pattern_id"] = pattern.id
        pattern.supporting_metrics = supporting_metrics
        return pattern

    def _build_tod_context_comparison(
        self,
        morning: Dict[str, Any],
        afternoon: Dict[str, Any],
        evening: Dict[str, Any],
        metric_type: str = "delay",
    ) -> List[Dict[str, Any]]:
        """Helper to build structured Morning/Afternoon/Evening comparison."""
        if metric_type == "completion_rate":
            return [
                {
                    "context": "Morning",
                    "label": "Morning (6 AM–12 PM)",
                    "value": round(morning.get("completion_rate", 0.0) * 100, 1),
                    "sample_size": morning.get("total_tasks", 0),
                    "unit": "%",
                },
                {
                    "context": "Afternoon",
                    "label": "Afternoon (12 PM–5 PM)",
                    "value": round(afternoon.get("completion_rate", 0.0) * 100, 1),
                    "sample_size": afternoon.get("total_tasks", 0),
                    "unit": "%",
                },
                {
                    "context": "Evening",
                    "label": "Evening (5 PM–10 PM)",
                    "value": round(evening.get("completion_rate", 0.0) * 100, 1),
                    "sample_size": evening.get("total_tasks", 0),
                    "unit": "%",
                },
            ]
        else:
            return [
                {
                    "context": "Morning",
                    "label": "Morning (6 AM–12 PM)",
                    "value": morning.get("average_delay_minutes", 0.0),
                    "sample_size": morning.get("delay_observations", morning.get("total_tasks", 0)),
                    "unit": "min",
                },
                {
                    "context": "Afternoon",
                    "label": "Afternoon (12 PM–5 PM)",
                    "value": afternoon.get("average_delay_minutes", 0.0),
                    "sample_size": afternoon.get("delay_observations", afternoon.get("total_tasks", 0)),
                    "unit": "min",
                },
                {
                    "context": "Evening",
                    "label": "Evening (5 PM–10 PM)",
                    "value": evening.get("average_delay_minutes", 0.0),
                    "sample_size": evening.get("delay_observations", evening.get("total_tasks", 0)),
                    "unit": "min",
                },
            ]

    def _upsert_pattern(
        self,
        pattern_type: str,
        title: str,
        description: str,
        confidence: str,
        sample_size: int,
        status: str,
        supporting_metrics: Dict[str, Any],
    ) -> BehaviorPattern:
        """Finds existing pattern of same type or creates a new one, keeping ID stable."""
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
            pat_id = existing.id
            supporting_metrics["pattern_id"] = pat_id
            existing.title = title
            existing.description = description
            existing.confidence = confidence
            existing.sample_size = sample_size
            existing.status = status
            existing.last_detected = now
            existing.supporting_metrics = dict(supporting_metrics)
            return existing
        else:
            pat_id = str(uuid.uuid4())
            supporting_metrics["pattern_id"] = pat_id
            new_p = BehaviorPattern(
                id=pat_id,
                user_id=self.user_id,
                pattern_type=pattern_type,
                title=title,
                description=description,
                confidence=confidence,
                sample_size=sample_size,
                first_detected=now,
                last_detected=now,
                status=status,
                supporting_metrics=dict(supporting_metrics),
            )
            self.db.add(new_p)
            self.db.flush()
            return new_p
