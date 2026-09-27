from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.checkin import TaskCheckin
from app.models.task import Task
from app.models.procrastination import ProcrastinationEvent
from app.models.screen_usage import ScreenUsage
from app.models.behavior import BehaviorMetric
from app.models.experiment import Experiment, ExperimentResult


class BehaviorMetricsCalculator:
    """
    Deterministic behavior engine.
    Calculates hard metrics strictly in Python and SQL without LLM estimation.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def compute_task_completion_stats(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates total, done, partial, missed tasks, and completion rate.
        If date is provided, scopes calculations specifically to that occurrence date.
        If start_date and/or end_date are provided, scopes calculations to that inclusive range [start_date, end_date].
        """
        query = self.db.query(TaskCheckin).filter(TaskCheckin.user_id == self.user_id)
        if date:
            query = query.filter(TaskCheckin.date == date)
        if start_date:
            query = query.filter(TaskCheckin.date >= start_date)
        if end_date:
            query = query.filter(TaskCheckin.date <= end_date)
        checkins = query.all()
        total = len(checkins)
        if total == 0:
            return {
                "total": 0,
                "done": 0,
                "partial": 0,
                "missed": 0,
                "completion_rate": None if (start_date or end_date) else 0.0,
                "sample_size": 0,
            }

        done = sum(1 for c in checkins if c.status == "done")
        partial = sum(1 for c in checkins if c.status == "partial")
        missed = sum(1 for c in checkins if c.status == "missed")
        rate = round((done + 0.5 * partial) / total, 2)

        return {
            "total": total,
            "done": done,
            "partial": partial,
            "missed": missed,
            "completion_rate": rate,
            "sample_size": total,
        }

    def compute_start_delay_stats(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates average start delay in minutes.
        Returns average_start_delay_minutes = None when there are no observations.
        Preserves measured 0.0 when delay was observed to be 0 minutes.
        If date is provided, scopes calculations specifically to that occurrence date.
        If start_date and/or end_date are provided, scopes calculations to that inclusive range [start_date, end_date].
        """
        query = (
            self.db.query(TaskCheckin)
            .filter(
                TaskCheckin.user_id == self.user_id,
                TaskCheckin.start_delay_minutes.isnot(None),
            )
        )
        if date:
            query = query.filter(TaskCheckin.date == date)
        if start_date:
            query = query.filter(TaskCheckin.date >= start_date)
        if end_date:
            query = query.filter(TaskCheckin.date <= end_date)
        checkins = query.all()

        if not checkins:
            return {
                "sample_size": 0,
                "average_start_delay_minutes": None,
                "max_delay_minutes": None,
            }

        delays = [c.start_delay_minutes for c in checkins if c.start_delay_minutes is not None]
        if not delays:
            return {
                "sample_size": 0,
                "average_start_delay_minutes": None,
                "max_delay_minutes": None,
            }

        avg_delay = round(sum(delays) / len(delays), 1)
        max_delay = max(delays)

        return {
            "sample_size": len(delays),
            "average_start_delay_minutes": avg_delay,
            "max_delay_minutes": max_delay,
        }

    def compute_time_of_day_breakdown(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyzes task completion and delay by morning, afternoon, evening, night.
        Supports filtering by specific date or date range [start_date, end_date].
        """
        # Join checkin with task to inspect planned_time
        query = (
            self.db.query(TaskCheckin, Task)
            .join(Task, TaskCheckin.task_id == Task.id)
            .filter(TaskCheckin.user_id == self.user_id)
        )
        if date:
            query = query.filter(TaskCheckin.date == date)
        if start_date:
            query = query.filter(TaskCheckin.date >= start_date)
        if end_date:
            query = query.filter(TaskCheckin.date <= end_date)
        results = query.all()

        buckets = {
            "morning": {"total": 0, "done": 0, "delays": []},    # 06:00 - 11:59
            "afternoon": {"total": 0, "done": 0, "delays": []},  # 12:00 - 16:59
            "evening": {"total": 0, "done": 0, "delays": []},    # 17:00 - 21:59
            "night": {"total": 0, "done": 0, "delays": []},      # 22:00 - 05:59
        }

        for checkin, task in results:
            planned_time = task.planned_time or "09:00"
            try:
                hour = int(planned_time.split(":")[0])
            except Exception:
                hour = 9

            if 6 <= hour < 12:
                bucket = "morning"
            elif 12 <= hour < 17:
                bucket = "afternoon"
            elif 17 <= hour < 22:
                bucket = "evening"
            else:
                bucket = "night"

            buckets[bucket]["total"] += 1
            if checkin.status == "done":
                buckets[bucket]["done"] += 1
            if checkin.start_delay_minutes is not None:
                buckets[bucket]["delays"].append(checkin.start_delay_minutes)

        breakdown = {}
        for b_name, data in buckets.items():
            tot = data["total"]
            done = data["done"]
            delays = data["delays"]
            comp_rate = round(done / tot, 2) if tot > 0 else 0.0
            avg_del = round(sum(delays) / len(delays), 1) if delays else 0.0
            breakdown[b_name] = {
                "total_tasks": tot,
                "done_tasks": done,
                "completion_rate": comp_rate,
                "average_delay_minutes": avg_del,
                "delay_observations": len(delays),
            }

        return breakdown

    def compute_daily_behavior_series(
        self,
        metric: str = "start_delay",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        time_of_day: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Computes real day-by-day behavioral observation points.
        Never fabricates dates or points; only dates with actual checkins are included.
        metric: "start_delay" (avg minutes per day) or "completion_rate" (done+0.5*partial)/total.
        time_of_day: optional filter for "morning", "afternoon", "evening", "night".
        Returns: list of {"date": "YYYY-MM-DD", "value": float, "sample_size": int, "unit": str}
        """
        query = (
            self.db.query(TaskCheckin, Task)
            .join(Task, TaskCheckin.task_id == Task.id)
            .filter(TaskCheckin.user_id == self.user_id)
        )
        if start_date:
            query = query.filter(TaskCheckin.date >= start_date)
        if end_date:
            query = query.filter(TaskCheckin.date <= end_date)

        rows = query.all()
        by_date: Dict[str, List[Any]] = {}

        for checkin, task in rows:
            if time_of_day:
                planned_time = task.planned_time or "09:00"
                try:
                    hour = int(planned_time.split(":")[0])
                except Exception:
                    hour = 9

                if 6 <= hour < 12:
                    tod = "morning"
                elif 12 <= hour < 17:
                    tod = "afternoon"
                elif 17 <= hour < 22:
                    tod = "evening"
                else:
                    tod = "night"

                if tod != time_of_day:
                    continue

            d_str = checkin.date
            if not d_str:
                continue
            if d_str not in by_date:
                by_date[d_str] = []
            by_date[d_str].append(checkin)

        series = []
        for d_str in sorted(by_date.keys()):
            day_checkins = by_date[d_str]
            if metric == "start_delay":
                delays = [c.start_delay_minutes for c in day_checkins if c.start_delay_minutes is not None]
                if delays:
                    series.append({
                        "date": d_str,
                        "value": round(sum(delays) / len(delays), 1),
                        "sample_size": len(delays),
                        "unit": "min",
                    })
            elif metric == "completion_rate":
                tot = len(day_checkins)
                if tot > 0:
                    done = sum(1 for c in day_checkins if c.status == "done")
                    partial = sum(1 for c in day_checkins if c.status == "partial")
                    rate = round((done + 0.5 * partial) / tot, 2)
                    series.append({
                        "date": d_str,
                        "value": round(rate * 100, 1),
                        "sample_size": tot,
                        "unit": "%",
                    })

        return series

    @staticmethod
    def calculate_recency_weighted_average(
        observations: List[tuple],  # List of (date_str "YYYY-MM-DD", numeric_val)
        half_life_days: float = 7.0,
        ref_date: Optional[str] = None,
    ) -> Optional[float]:
        """
        Deterministic continuous exponential decay weighting:
        weight = exp(-lambda * age_days) where lambda = ln(2) / half_life_days.
        Returns recency-weighted average, or None if observations is empty.
        """
        if not observations:
            return None
        import math
        ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date() if ref_date else datetime.utcnow().date()
        decay_lambda = math.log(2.0) / max(1.0, half_life_days)
        total_weight = 0.0
        weighted_sum = 0.0
        for date_str, val in observations:
            try:
                obs_d = datetime.strptime(date_str, "%Y-%m-%d").date()
                age_days = max(0, (ref_d - obs_d).days)
            except Exception:
                age_days = 0
            w = math.exp(-decay_lambda * age_days)
            weighted_sum += w * val
            total_weight += w
        return round(weighted_sum / total_weight, 1) if total_weight > 0 else None

    def compute_procrastination_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates confirmed and estimated procrastination episodes."""
        query = (
            self.db.query(ProcrastinationEvent)
            .filter(ProcrastinationEvent.user_id == self.user_id)
        )
        if date:
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                start_dt = datetime.combine(date_obj, time.min)
                end_dt = datetime.combine(date_obj, time.max)
                query = query.filter(
                    ProcrastinationEvent.started_at >= start_dt,
                    ProcrastinationEvent.started_at <= end_dt,
                )
            except Exception:
                pass

        events = query.all()

        if not events:
            return {
                "count": 0,
                "total_seconds": 0,
                "total_minutes": 0.0,
                "average_duration_minutes": 0.0,
                "reasons": {},
            }

        total_sec = sum(e.duration_seconds or 0 for e in events)
        reasons = {}
        for e in events:
            reason = e.trigger_reason or "unspecified"
            reasons[reason] = reasons.get(reason, 0) + 1

        avg_min = round((total_sec / len(events)) / 60, 1) if events else 0.0

        return {
            "count": len(events),
            "total_seconds": total_sec,
            "total_minutes": round(total_sec / 60, 1),
            "average_duration_minutes": avg_min,
            "reasons": reasons,
        }


    def compute_top_distractions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Identifies top apps logged during distraction or screen usage, optionally scoped to [start_date, end_date]."""
        query = self.db.query(
            ScreenUsage.app_name,
            func.sum(ScreenUsage.duration_seconds).label("total_duration"),
            func.count(ScreenUsage.id).label("session_count"),
        ).filter(ScreenUsage.user_id == self.user_id)

        if start_date:
            try:
                start_dt = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time.min)
                query = query.filter(ScreenUsage.started_at >= start_dt)
            except Exception:
                pass
        if end_date:
            try:
                end_dt = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), time.max)
                query = query.filter(ScreenUsage.started_at <= end_dt)
            except Exception:
                pass

        usages = (
            query.group_by(ScreenUsage.app_name)
            .order_by(func.sum(ScreenUsage.duration_seconds).desc())
            .limit(5)
            .all()
        )

        return [
            {
                "app_name": row.app_name,
                "total_minutes": round(row.total_duration / 60, 1),
                "sessions": row.session_count,
            }
            for row in usages
        ]

    def compute_daily_distraction_series(
        self,
        app_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Computes real day-by-day distraction minutes for a specific app or all screen usage.
        Never fabricates dates or points; only dates with actual logged screen usage are included.
        Returns: list of {"date": "YYYY-MM-DD", "value": float, "sample_size": int, "unit": "min"}
        """
        query = self.db.query(ScreenUsage).filter(ScreenUsage.user_id == self.user_id)
        if app_name:
            query = query.filter(ScreenUsage.app_name == app_name)
        if start_date:
            try:
                start_dt = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time.min)
                query = query.filter(ScreenUsage.started_at >= start_dt)
            except Exception:
                pass
        if end_date:
            try:
                end_dt = datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), time.max)
                query = query.filter(ScreenUsage.started_at <= end_dt)
            except Exception:
                pass

        usages = query.order_by(ScreenUsage.started_at.asc()).all()
        by_date: Dict[str, List[int]] = {}
        for u in usages:
            d_str = u.started_at.strftime("%Y-%m-%d")
            if d_str not in by_date:
                by_date[d_str] = []
            by_date[d_str].append(u.duration_seconds or 0)

        series = []
        for d_str in sorted(by_date.keys()):
            durations = by_date[d_str]
            total_min = round(sum(durations) / 60.0, 1)
            series.append({
                "date": d_str,
                "value": total_min,
                "sample_size": len(durations),
                "unit": "min",
            })
        return series


    def compute_behavior_score(self) -> float:
        """
        Calculates the internal composite Behavior Score (0.0 to 100.0).
        Private metric representing current overall behavioral state.
        Synthesizes task completion (45%), initiation promptness (35%), and distraction control (20%).
        """
        comp_stats = self.compute_task_completion_stats()
        delay_stats = self.compute_start_delay_stats()
        proc_stats = self.compute_procrastination_stats()

        if comp_stats["total"] == 0 and delay_stats["sample_size"] == 0:
            return 50.0  # Neutral initial baseline

        # 1. Completion component (0 - 100)
        completion_comp = comp_stats["completion_rate"] * 100.0

        # 2. Promptness component (0 - 100)
        # 0 min delay = 100, 30 min delay = 50, 60+ min delay = 0
        avg_delay = delay_stats["average_start_delay_minutes"]
        if avg_delay is None:
            promptness_comp = 70.0  # Neutral baseline promptness when no delay data exists yet
        else:
            promptness_comp = max(0.0, min(100.0, 100.0 - (avg_delay * 1.67)))

        # 3. Procrastination resistance component (0 - 100)
        proc_min = proc_stats["total_minutes"]
        proc_comp = max(0.0, min(100.0, 100.0 - (proc_min * 1.25)))

        weighted_score = (completion_comp * 0.45) + (promptness_comp * 0.35) + (proc_comp * 0.20)
        return round(max(5.0, min(99.0, weighted_score)), 1)


    def compute_improvement_score(self) -> float:
        """
        Calculates the Improvement Score (0.0 to 100.0).
        Public by default metric emphasizing behavioral growth and change over time
        rather than absolute score.
        """
        checkins = (
            self.db.query(TaskCheckin)
            .filter(TaskCheckin.user_id == self.user_id)
            .order_by(TaskCheckin.created_at.asc())
            .all()
        )

        if len(checkins) < 2:
            # Baseline if user just started
            if len(checkins) == 1 and checkins[0].status == "done":
                return 70.0
            return 55.0

        # Split checkins into earlier baseline half and recent half
        mid = len(checkins) // 2
        baseline_slice = checkins[:mid]
        recent_slice = checkins[mid:]

        # Calculate completion rate for baseline
        base_done = sum(1 for c in baseline_slice if c.status == "done")
        base_partial = sum(1 for c in baseline_slice if c.status == "partial")
        base_rate = (base_done + 0.5 * base_partial) / len(baseline_slice)

        # Calculate completion rate for recent
        rec_done = sum(1 for c in recent_slice if c.status == "done")
        rec_partial = sum(1 for c in recent_slice if c.status == "partial")
        rec_rate = (rec_done + 0.5 * rec_partial) / len(recent_slice)

        # Calculate delay change
        base_delays = [c.start_delay_minutes for c in baseline_slice if c.start_delay_minutes is not None]
        rec_delays = [c.start_delay_minutes for c in recent_slice if c.start_delay_minutes is not None]

        base_avg_delay = sum(base_delays) / len(base_delays) if base_delays else 20.0
        rec_avg_delay = sum(rec_delays) / len(rec_delays) if rec_delays else 15.0

        # Trajectory bonuses
        delta_rate = rec_rate - base_rate  # positive is good
        delta_delay = base_avg_delay - rec_avg_delay  # positive means delay reduced (good)

        baseline_score = 50.0
        rate_bonus = delta_rate * 40.0  # e.g., +0.25 -> +10.0 points
        delay_bonus = max(-20.0, min(20.0, (delta_delay / 15.0) * 15.0))

        # Recent momentum bonus if recent completion is high
        momentum_bonus = (rec_rate - 0.5) * 20.0 if rec_rate > 0.5 else 0.0

        score = baseline_score + rate_bonus + delay_bonus + momentum_bonus
        return round(max(10.0, min(98.0, score)), 1)

    def compute_experiment_effectiveness(self) -> float:
        """
        Calculates Experiment Effectiveness (0.0 to 100.0).
        Public by default metric measuring how effectively the user adopts behavioral interventions.
        Derived from evaluated experiment results without leaking private hypothesis details.
        """
        results = (
            self.db.query(ExperimentResult)
            .join(Experiment, ExperimentResult.experiment_id == Experiment.id)
            .filter(Experiment.user_id == self.user_id)
            .all()
        )

        if not results:
            # Check if there are active experiments
            active_count = (
                self.db.query(Experiment)
                .filter(Experiment.user_id == self.user_id, Experiment.status.in_(["active", "completed"]))
                .count()
            )
            return 75.0 if active_count > 0 else 70.0

        weight_map = {
            "positive": 1.0,
            "neutral": 0.6,
            "inconclusive": 0.5,
            "negative": 0.3,
        }

        total_weight = sum(weight_map.get(r.conclusion, 0.5) for r in results)
        effectiveness = (total_weight / len(results)) * 100.0
        return round(max(10.0, min(99.0, effectiveness)), 1)

    def compute_consistency_score(self) -> float:
        """
        Calculates Consistency (0.0 to 100.0).
        Public by default metric measuring behavioral reliability across time
        (not just raw task volume, but variance and day-to-day follow-through).
        """
        checkins = (
            self.db.query(TaskCheckin)
            .filter(TaskCheckin.user_id == self.user_id)
            .order_by(TaskCheckin.created_at.desc())
            .limit(30)
            .all()
        )

        if not checkins:
            return 50.0

        # 1. Follow-through ratio
        done = sum(1 for c in checkins if c.status == "done")
        partial = sum(1 for c in checkins if c.status == "partial")
        adherence = (done + 0.5 * partial) / len(checkins)

        # 2. Timing stability (low start delay variance)
        delays = [c.start_delay_minutes for c in checkins if c.start_delay_minutes is not None]
        if delays:
            avg_delay = sum(delays) / len(delays)
            stability = max(0.0, 1.0 - (avg_delay / 40.0))
        else:
            stability = 0.7

        # 3. Active day spread
        dates_seen = {c.date for c in checkins if c.date}
        spread_factor = min(1.0, max(0.5, len(dates_seen) / 5.0))

        score = ((adherence * 0.55) + (stability * 0.30) + (spread_factor * 0.15)) * 100.0
        return round(max(15.0, min(98.0, score)), 1)

    def compute_behavior_progress_curve(self, days: int = 14) -> List[Dict[str, Any]]:
        """
        Generates behavior progress curve points based strictly on actual historical evidence.
        Days without recorded check-in evidence are NOT fabricated with synthetic scores or 'stable' trends.
        """
        # Fetch checkins ordered by date ascending
        checkins = (
            self.db.query(TaskCheckin)
            .filter(TaskCheckin.user_id == self.user_id)
            .order_by(TaskCheckin.created_at.asc())
            .all()
        )

        # Group checkins by date
        daily_records: Dict[str, List[TaskCheckin]] = {}
        for c in checkins:
            d_str = c.date or c.created_at.strftime("%Y-%m-%d")
            if d_str not in daily_records:
                daily_records[d_str] = []
            daily_records[d_str].append(c)

        date_keys = sorted(daily_records.keys())
        if not date_keys:
            # Clean empty state for new user with no evidence
            return []

        # If days window is specified (e.g. 14 days), consider dates within window
        today = datetime.utcnow().date()
        window_start = (today - timedelta(days=days - 1)).isoformat()
        relevant_dates = [d for d in date_keys if d >= window_start]
        # If all recorded dates are older than window, keep the most recent recorded dates
        if not relevant_dates:
            relevant_dates = date_keys[-days:]

        points: List[Dict[str, Any]] = []
        prev_score: Optional[float] = None
        prev_trend: Optional[str] = None

        for d_str in relevant_dates:
            day_checkins = daily_records[d_str]
            d_done = sum(1 for c in day_checkins if c.status == "done")
            d_part = sum(1 for c in day_checkins if c.status == "partial")
            d_tot = len(day_checkins)
            day_rate = (d_done + 0.5 * d_part) / d_tot if d_tot > 0 else 0.0

            delays = [c.start_delay_minutes for c in day_checkins if c.start_delay_minutes is not None]
            avg_del = (sum(delays) / len(delays)) if delays else 0.0

            # Score for this recorded day based on evidence
            delay_factor = max(0.0, 30.0 - (avg_del * 0.6)) if delays else 20.0
            day_score = round(max(10.0, min(98.0, (day_rate * 70.0) + delay_factor)), 1)

            # Determine trajectory trend ONLY when previous evidence exists
            if prev_score is None:
                trend = "initial"
            else:
                score_diff = day_score - prev_score
                if score_diff > 3.0:
                    trend = "recovery" if prev_trend == "setback" else "improving"
                elif score_diff < -3.0:
                    trend = "setback"
                else:
                    trend = "stable"

            context = f"{d_done}/{d_tot} tasks completed"
            if delays:
                context += f" • {int(avg_del)}m avg delay"

            points.append({
                "date": d_str,
                "progress_score": day_score,
                "trend": trend,
                "metric_context": context,
            })
            prev_score = day_score
            prev_trend = trend

        return points


    def record_metrics_snapshot(self) -> Dict[str, Any]:
        """Calculates and persists a snapshot of core metrics into `behavior_metrics`."""
        comp_stats = self.compute_task_completion_stats()
        delay_stats = self.compute_start_delay_stats()
        proc_stats = self.compute_procrastination_stats()

        # Persist metric rows
        delay_val = delay_stats["average_start_delay_minutes"]
        metrics_to_save = [
            ("completion_rate", comp_stats["completion_rate"], comp_stats),
            ("average_start_delay_minutes", float(delay_val) if delay_val is not None else 0.0, delay_stats),
            ("procrastination_total_minutes", proc_stats["total_minutes"], proc_stats),
            ("behavior_score", self.compute_behavior_score(), {}),
            ("improvement_score", self.compute_improvement_score(), {}),
            ("consistency", self.compute_consistency_score(), {}),
            ("experiment_effectiveness", self.compute_experiment_effectiveness(), {}),
        ]


        now = datetime.utcnow()
        for m_type, m_val, meta in metrics_to_save:
            metric_entry = BehaviorMetric(
                user_id=self.user_id,
                metric_type=m_type,
                metric_value=float(m_val),
                time_window_end=now,
                metadata_json=meta,
            )
            self.db.add(metric_entry)

        self.db.commit()

        return {
            "completion": comp_stats,
            "start_delay": delay_stats,
            "procrastination": proc_stats,
            "time_of_day": self.compute_time_of_day_breakdown(),
            "top_distractions": self.compute_top_distractions(),
            "behavior_score": self.compute_behavior_score(),
            "improvement_score": self.compute_improvement_score(),
            "consistency": self.compute_consistency_score(),
            "experiment_effectiveness": self.compute_experiment_effectiveness(),
        }
