import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.behavior import BehaviorProfile, BehaviorPattern
from app.models.experiment import Experiment, ExperimentResult
from app.models.screen_usage import ScreenUsage
from app.models.sleep import SleepRecord
from app.models.onboarding import UserGoal, UserRoutineContext, UserChallenge, UserInterest
from app.behavior.metrics import BehaviorMetricsCalculator
from app.schemas.ai import AIContext


class AIContextBuilder:
    """
    Constructs an evidence-based, privacy-safe, question-relevant context payload for the LLM.
    Guarantees that all quantitative data is calculated deterministically by the backend
    before being supplied to the AI.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.metrics_calc = BehaviorMetricsCalculator(db, user_id)

    def classify_query(self, question: Optional[str]) -> List[str]:
        """
        Deterministically classifies the user's question into one or more topic intents
        to select question-relevant evidence and filter out unrelated data.
        """
        if not question or not question.strip():
            return ["general_coaching"]

        q = question.lower().strip()
        intents = set()

        # Procrastination / Start Delay / Initiation Friction
        proc_keywords = [
            "procrastinat", "delay", "friction", "stuck", "resist", "hesitat",
            "start delay", "put off", "putting off", "avoid", "initiation",
            "distract", "sluggish", "lazy"
        ]
        if any(kw in q for kw in proc_keywords):
            intents.add("procrastination_delay")

        # Experiments & Interventions
        exp_keywords = [
            "experiment", "hypothesis", "intervention", "did it work", "trial",
            "result", "evaluate", "recommend that experiment", "test", "micro-start",
            "what to try", "what should i try"
        ]
        if any(kw in q for kw in exp_keywords):
            intents.add("experiment_evaluation")

        # Progress / Trajectory / Improvement / Consistency
        trend_keywords = [
            "improv", "progress", "trajectory", "getting better", "consistent",
            "consistency", "score", "trend", "level", "change over time",
            "am i doing better"
        ]
        if any(kw in q for kw in trend_keywords):
            intents.add("improvement_trend")

        # Patterns / Habits / Learned Profile Observations
        pattern_keywords = [
            "pattern", "habit", "routine", "what have you learned", "learned",
            "strength", "weakness", "insight", "focus window", "best time",
            "worst time", "rhythm", "tendency"
        ]
        if any(kw in q for kw in pattern_keywords):
            intents.add("patterns_habits")

        # Time of day specifics
        tod_keywords = ["morning", "afternoon", "evening", "night"]
        if any(kw in q for kw in tod_keywords):
            intents.add("time_of_day")

        if not intents:
            intents.add("general_coaching")

        return sorted(list(intents))

    def build_context(
        self,
        question: Optional[str] = None,
        specific_pattern_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AIContext:
        """
        Builds a structured, question-relevant AIContext for the authenticated user.
        Enforces strict identity scoping and filters evidence by intent.
        """
        # 1. Identity scoping
        user = self.db.query(User).filter(User.id == self.user_id).first()
        user_name = user.name if user else "Friend"

        # 2. Intent classification
        intents = self.classify_query(question)
        if specific_pattern_id:
            intents.append("patterns_habits")
            intents = sorted(list(set(intents)))

        limitations: List[str] = []

        # 3. Base Task Completion Metrics
        comp_stats = self.metrics_calc.compute_task_completion_stats()
        total_tasks = comp_stats.get("total", 0)
        if total_tasks < 5:
            limitations.append(f"Low sample size (N={total_tasks} tasks tracked); observations are preliminary.")

        metrics_payload: Dict[str, Any] = {
            "task_completion": {
                "total_tasks_tracked": total_tasks,
                "completed_tasks": comp_stats.get("done", 0),
                "partial_tasks": comp_stats.get("partial", 0),
                "missed_tasks": comp_stats.get("missed", 0),
                "completion_rate": comp_stats.get("completion_rate", 0.0),
                "sample_size": total_tasks,
                "source": "task_checkins",
            }
        }

        # 4. Procrastination & Start Delay Metrics
        if any(i in intents for i in ["procrastination_delay", "time_of_day", "general_coaching"]):
            delay_stats = self.metrics_calc.compute_start_delay_stats()
            proc_stats = self.metrics_calc.compute_procrastination_stats()
            tod_stats = self.metrics_calc.compute_time_of_day_breakdown()

            metrics_payload["start_delay"] = {
                "average_start_delay_minutes": delay_stats.get("average_start_delay_minutes", 0.0),
                "sample_size": delay_stats.get("sample_size", 0),
                "source": "task_checkins.start_delay",
            }

            metrics_payload["procrastination_episodes"] = {
                "count": proc_stats.get("count", 0),
                "total_minutes": proc_stats.get("total_minutes", 0),
                "average_minutes": proc_stats.get("average_minutes", 0.0),
                "source": "procrastination_events",
            }

            # Filter or highlight time of day breakdown if specific time asked
            q_lower = (question or "").lower()
            if "evening" in q_lower or "night" in q_lower:
                evening_data = tod_stats.get("evening", {})
                metrics_payload["evening_performance"] = {
                    "total_tasks": evening_data.get("total_tasks", 0),
                    "completed_tasks": evening_data.get("done", 0),
                    "completion_rate": evening_data.get("completion_rate", 0.0),
                    "source": "task_checkins.time_of_day",
                }
            elif "morning" in q_lower:
                morning_data = tod_stats.get("morning", {})
                metrics_payload["morning_performance"] = {
                    "total_tasks": morning_data.get("total_tasks", 0),
                    "completed_tasks": morning_data.get("done", 0),
                    "completion_rate": morning_data.get("completion_rate", 0.0),
                    "source": "task_checkins.time_of_day",
                }
            elif "afternoon" in q_lower:
                afternoon_data = tod_stats.get("afternoon", {})
                metrics_payload["afternoon_performance"] = {
                    "total_tasks": afternoon_data.get("total_tasks", 0),
                    "completed_tasks": afternoon_data.get("done", 0),
                    "completion_rate": afternoon_data.get("completion_rate", 0.0),
                    "source": "task_checkins.time_of_day",
                }
            else:
                metrics_payload["time_of_day_breakdown"] = tod_stats

        # 5. Improvement & Consistency Metrics
        if any(i in intents for i in ["improvement_trend", "general_coaching"]):
            metrics_payload["trajectory"] = {
                "improvement_score": self.metrics_calc.compute_improvement_score(),
                "consistency_score": self.metrics_calc.compute_consistency_score(),
                "behavior_score": self.metrics_calc.compute_behavior_score(),
                "experiment_effectiveness": self.metrics_calc.compute_experiment_effectiveness(),
                "provenance": "behavior_engine.continuous_progress",
            }

        # 6. Behavioral Patterns (Active, Improving, Weakening, Inactive, and Resolved with Provenance)
        patterns_query = (
            self.db.query(BehaviorPattern)
            .filter(
                BehaviorPattern.user_id == self.user_id,
                BehaviorPattern.status.in_(["active", "improving", "weakening", "resolved", "archived", "inactive"]),
            )
        )
        if specific_pattern_id:
            patterns_query = patterns_query.filter(BehaviorPattern.id == specific_pattern_id)
        all_patterns = patterns_query.all()

        patterns_payload: List[Dict[str, Any]] = []
        current_patterns_payload: List[Dict[str, Any]] = []
        inactive_patterns_payload: List[Dict[str, Any]] = []
        resolved_patterns_payload: List[Dict[str, Any]] = []
        q_text = (question or "").lower()

        for p in all_patterns:
            # Include if specific pattern ID requested, or general coaching, or pattern query
            include = False
            if specific_pattern_id or "patterns_habits" in intents or "general_coaching" in intents:
                include = True
            elif "procrastination_delay" in intents and p.pattern_type in [
                "start_delay_resistance", "primary_distraction", "distraction_loop"
            ]:
                include = True
            elif "time_of_day" in intents and ("evening" in q_text or "night" in q_text) and "evening" in p.title.lower():
                include = True
            elif "time_of_day" in intents and "morning" in q_text and "morning" in p.title.lower():
                include = True
            elif "time_of_day" in intents and "afternoon" in q_text and "afternoon" in p.title.lower():
                include = True

            if include:
                sup = p.supporting_metrics or {}
                status_str = (p.status or "active").lower()
                is_inactive = (
                    status_str == "inactive"
                    or sup.get("trend") == "inactive"
                    or bool(sup.get("insufficient_current_evidence"))
                )
                is_resolved = not is_inactive and status_str in ("resolved", "archived")

                if is_inactive:
                    lifecycle_cat = "insufficient_current_evidence"
                    is_current = False
                elif is_resolved:
                    lifecycle_cat = "historical_resolved"
                    is_current = False
                else:
                    lifecycle_cat = "current_pattern"
                    is_current = True

                pattern_dict = {
                    "id": p.id,
                    "pattern_type": p.pattern_type,
                    "title": p.title,
                    "description": p.description,
                    "status": p.status,
                    "trend": sup.get("trend", p.status),
                    "confidence": p.confidence,  # "low", "moderate", "high"
                    "sample_size": p.sample_size,
                    "is_current": is_current,
                    "lifecycle_category": lifecycle_cat,
                    "recent_value": sup.get("recent_window", {}).get("value"),
                    "historical_value": sup.get("historical_window", {}).get("value"),
                    "time_window": {
                        "first_detected": p.first_detected.isoformat() if p.first_detected else None,
                        "last_detected": p.last_detected.isoformat() if p.last_detected else None,
                    },
                    "supporting_metrics": sup,
                    "source": "behavior_engine.pattern_detector",
                }

                if is_inactive:
                    pattern_dict["explanation_guidance"] = (
                        "INSUFFICIENT CURRENT EVIDENCE / INACTIVE: This pattern was observed historically, "
                        "but there are not enough recent observations to determine if it is currently present. "
                        "You must NOT say this pattern was resolved or overcome. "
                        "Instead, explain that more recent observations are needed to confirm whether the pattern persists."
                    )
                    inactive_patterns_payload.append(pattern_dict)
                elif is_resolved:
                    pattern_dict["explanation_guidance"] = (
                        "HISTORICAL / RESOLVED: This pattern has sufficient recent behavioral evidence demonstrating "
                        "resolution. It must NOT be described as an active behavioral problem."
                    )
                    resolved_patterns_payload.append(pattern_dict)
                else:
                    current_patterns_payload.append(pattern_dict)

                patterns_payload.append(pattern_dict)

        if not current_patterns_payload and not specific_pattern_id:
            limitations.append("No active recurring behavioral patterns detected with sufficient confidence yet.")
        if inactive_patterns_payload and not specific_pattern_id:
            limitations.append("Some historical patterns have insufficient recent observations to determine their active state.")

        # 7. Behavioral Profile (Internal Intelligence Extraction)
        profile_obj = (
            self.db.query(BehaviorProfile)
            .filter(BehaviorProfile.user_id == self.user_id)
            .first()
        )
        profile_payload: Dict[str, Any] = {}
        if profile_obj and profile_obj.profile_data:
            pdata = profile_obj.profile_data
            profile_payload["observation_status"] = "current_evolving_observation"
            profile_payload["best_focus_window"] = pdata.get("best_focus_window")
            profile_payload["worst_focus_window"] = pdata.get("worst_focus_window")
            profile_payload["common_distraction_app"] = pdata.get("common_distraction_app")
            profile_payload["successful_interventions"] = pdata.get("successful_interventions", [])
            profile_payload["procrastination_summary"] = pdata.get("procrastination_summary", {})

            if any(i in intents for i in ["patterns_habits", "general_coaching"]):
                profile_payload["observed_strengths"] = pdata.get("strengths", [])
                profile_payload["observed_friction_areas"] = pdata.get("weaknesses", [])

            if "improvement_trend" in intents:
                profile_payload["current_level"] = profile_obj.current_level
                profile_payload["level_details"] = pdata.get("level_info", {})
                profile_payload["milestones"] = pdata.get("milestones", [])

            profile_payload["provenance"] = "behavior_engine.profile_manager"
        else:
            limitations.append("Behavioral profile is currently being initialized.")

        # 8. Behavioral Experiments Context
        experiments_payload: List[Dict[str, Any]] = []
        if any(i in intents for i in ["experiment_evaluation", "general_coaching", "procrastination_delay"]):
            exp_query = (
                self.db.query(Experiment)
                .filter(Experiment.user_id == self.user_id)
                .order_by(Experiment.created_at.desc())
            )
            if specific_pattern_id:
                exp_query = exp_query.filter(Experiment.pattern_id == specific_pattern_id)
            user_experiments = exp_query.limit(5).all()

            for exp in user_experiments:
                exp_dict: Dict[str, Any] = {
                    "id": exp.id,
                    "pattern_id": exp.pattern_id,
                    "title": exp.title,
                    "description": exp.description,
                    "hypothesis": exp.hypothesis,
                    "intervention_type": exp.intervention_type,
                    "target_metric": exp.target_metric,
                    "baseline_value": exp.baseline_value,
                    "target_value": exp.target_value,
                    "status": exp.status,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "results": [
                        {
                            "before_value": r.before_value,
                            "after_value": r.after_value,
                            "change_value": r.change_value,
                            "percent_change": r.percent_change,
                            "conclusion": r.conclusion,
                            "result_summary": r.result_summary,
                            "recorded_at": r.created_at.isoformat() if r.created_at else None,
                            "provenance": "backend_experiment_evaluator",
                        }
                        for r in exp.results
                    ],
                }
                experiments_payload.append(exp_dict)

        # 9. Device Telemetry Availability Status (Honest Representation)
        screen_records_count = (
            self.db.query(ScreenUsage)
            .filter(ScreenUsage.user_id == self.user_id)
            .count()
        )
        if screen_records_count > 0:
            distractions = self.metrics_calc.compute_top_distractions()
            telemetry_status = {
                "screen_usage": {
                    "status": "available",
                    "top_apps": distractions[:3],
                    "records_count": screen_records_count,
                    "source": "device_screen_usage",
                }
            }
        else:
            telemetry_status = {
                "screen_usage": {
                    "status": "unavailable",
                    "reason": "Automatic app tracking telemetry is not enabled or recorded. Do not infer specific app distractions unless user self-reports them.",
                }
            }
            limitations.append("Screen usage telemetry is unavailable.")

        sleep_records_count = (
            self.db.query(SleepRecord)
            .filter(SleepRecord.user_id == self.user_id)
            .count()
        )
        if sleep_records_count > 0:
            latest_sleep = (
                self.db.query(SleepRecord)
                .filter(SleepRecord.user_id == self.user_id)
                .order_by(SleepRecord.created_at.desc())
                .first()
            )
            telemetry_status["sleep_tracking"] = {
                "status": "available",
                "duration_minutes": latest_sleep.duration_minutes if latest_sleep else None,
                "quality_score": latest_sleep.quality_score if latest_sleep else None,
                "source": "sleep_records",
            }
        else:
            telemetry_status["sleep_tracking"] = {
                "status": "unavailable",
                "reason": "Sleep telemetry is not synced or recorded. Do not speculate on sleep deprivation or circadian causes without measured data.",
            }
            limitations.append("Sleep telemetry is unavailable.")

        # 10. Conversation Context (Carefully Distinguishing Facts vs User Self-Report)
        conversation_payload: Dict[str, Any] = {}
        if conversation_history:
            conversation_payload = {
                "recent_messages": conversation_history[-6:],  # controlled window
                "evidential_boundary_rule": (
                    "Conversation messages reflect user conversational flow and self-reports. "
                    "User statements (e.g., 'I always delay at night') represent subjective user perception, "
                    "NOT verified backend facts. Compare user perceptions against verified metrics."
                ),
            }

        # 11. Structured User Context (Onboarding & Living Context with Provenance)
        user_context_payload: Dict[str, Any] = {}
        active_goal = (
            self.db.query(UserGoal)
            .filter(UserGoal.user_id == self.user_id, UserGoal.is_active == True)
            .order_by(UserGoal.created_at.desc())
            .first()
        )
        if active_goal:
            user_context_payload["active_goal"] = {
                "category": active_goal.category,
                "description": active_goal.description,
                "source": "self_reported",
            }
        else:
            limitations.append("User has not set a primary goal yet.")

        routine_ctx = (
            self.db.query(UserRoutineContext)
            .filter(UserRoutineContext.user_id == self.user_id)
            .first()
        )
        if routine_ctx and (routine_ctx.preferred_time_window or routine_ctx.daily_available_duration):
            user_context_payload["availability"] = {
                "preferred_time_window": routine_ctx.preferred_time_window,
                "daily_available_duration": routine_ctx.daily_available_duration,
                "source": "self_reported",
            }

        # Challenges: relevant for procrastination, general coaching, patterns, and improvement trends
        if any(i in intents for i in ["procrastination_delay", "general_coaching", "patterns_habits", "improvement_trend"]):
            user_challenges = (
                self.db.query(UserChallenge)
                .filter(UserChallenge.user_id == self.user_id, UserChallenge.is_active == True)
                .all()
            )
            if user_challenges:
                user_context_payload["self_reported_challenges"] = [
                    {
                        "challenge": c.challenge_text,
                        "source": c.source or "self_reported",
                    }
                    for c in user_challenges
                ]

        # Interests / Hobbies: Filter strictly by question intent (exclude when unrelated)
        user_interests = (
            self.db.query(UserInterest)
            .filter(UserInterest.user_id == self.user_id, UserInterest.is_active == True)
            .all()
        )
        if user_interests:
            q_str = (question or "").lower()
            interest_keywords = [
                "interest", "hobby", "hobbies", "activity", "balance",
                "leisure", "free time", "gaming", "fitness", "music",
                "reading", "coding", "relax", "recreation"
            ]
            has_interest_mention = any(kw in q_str for kw in interest_keywords) or any(
                i.interest_text.lower() in q_str for i in user_interests if len(i.interest_text) > 2
            )
            # Only include if specifically referenced in question or exploratory coaching
            if has_interest_mention:
                user_context_payload["interests"] = [
                    {
                        "interest": i.interest_text,
                        "source": i.source or "self_reported",
                    }
                    for i in user_interests
                ]

        # 12. Profile Nature Limitation
        limitations.append("Behavioral profile represents current dynamic observations, not fixed personality traits.")

        return AIContext(
            user_id=self.user_id,
            user_name=user_name,
            user_question=question,
            classified_intents=intents,
            time_window={"generated_at": comp_stats.get("completion_rate")},
            user_context=user_context_payload,
            metrics=metrics_payload,
            patterns=patterns_payload,
            current_patterns=current_patterns_payload,
            inactive_patterns=inactive_patterns_payload,
            resolved_patterns=resolved_patterns_payload,
            behavior_profile=profile_payload,
            experiments=experiments_payload,
            telemetry_status=telemetry_status,
            conversation_context=conversation_payload,
            limitations=limitations,
        )
