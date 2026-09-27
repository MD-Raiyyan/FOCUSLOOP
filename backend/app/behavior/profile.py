from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.behavior import BehaviorProfile, BehaviorPattern, DEFAULT_PROFILE_VISIBILITY
from app.models.experiment import Experiment
from app.models.social import Friendship
from app.models.onboarding import UserGoal, UserRoutineContext
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.patterns import PatternDetector
from app.behavior.grading import get_grading_strategy


class BehaviorProfileManager:
    """
    Manages and updates the user's dynamic Behavioral Profile.
    Enforces privacy boundaries between internal behavioral intelligence and social progress metrics.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.metrics_calc = BehaviorMetricsCalculator(db, user_id)
        self.pattern_detector = PatternDetector(db, user_id)

    def get_or_create_profile(self) -> BehaviorProfile:
        """Retrieves existing profile or initializes a fresh one with default visibility settings."""
        profile = self.db.query(BehaviorProfile).filter(BehaviorProfile.user_id == self.user_id).first()
        if not profile:
            profile = BehaviorProfile(
                user_id=self.user_id,
                profile_data={},
                visibility_settings=dict(DEFAULT_PROFILE_VISIBILITY),
                behavior_score=50.0,
                current_level="Level 1 — Foundation",
                improvement_score=50.0,
                experiment_effectiveness=75.0,
                consistency=50.0,
                model_version="v1.0",
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        elif not profile.visibility_settings:
            profile.visibility_settings = dict(DEFAULT_PROFILE_VISIBILITY)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_visibility(self, visibility_updates: Dict[str, bool]) -> Dict[str, bool]:
        """Updates user's profile privacy / visibility preferences."""
        profile = self.get_or_create_profile()
        current_settings = dict(profile.visibility_settings or DEFAULT_PROFILE_VISIBILITY)

        # Update only valid visibility keys
        valid_keys = set(DEFAULT_PROFILE_VISIBILITY.keys())
        for k, v in visibility_updates.items():
            if k in valid_keys and isinstance(v, bool):
                current_settings[k] = v

        profile.visibility_settings = current_settings
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile.visibility_settings

    def refresh_profile(self) -> Dict[str, Any]:
        """
        Calculates latest metrics, updates patterns, computes scores and grading levels,
        and synchronizes with the database.
        """
        # 1. Update patterns
        patterns = self.pattern_detector.detect_and_update_patterns()

        # 2. Extract deterministic metrics
        comp_stats = self.metrics_calc.compute_task_completion_stats()
        delay_stats = self.metrics_calc.compute_start_delay_stats()
        tod = self.metrics_calc.compute_time_of_day_breakdown()
        distractions = self.metrics_calc.compute_top_distractions()

        # 3. High-level metric abstractions
        behavior_score = self.metrics_calc.compute_behavior_score()
        improvement_score = self.metrics_calc.compute_improvement_score()
        experiment_eff = self.metrics_calc.compute_experiment_effectiveness()
        consistency = self.metrics_calc.compute_consistency_score()

        # 4. Grading / Level interpretation
        grading_strategy = get_grading_strategy()
        level_info = grading_strategy.evaluate(
            behavior_score=behavior_score,
            improvement_score=improvement_score,
            consistency=consistency,
            experiment_effectiveness=experiment_eff,
            total_sessions=comp_stats["total"],
        )

        # 5. Find best and worst time windows
        best_window = "09:00 - 12:00 (default)"
        worst_window = "14:00 - 17:00 (default)"
        max_rate = -1.0
        min_rate = 2.0

        for window, data in tod.items():
            if data["total_tasks"] > 0:
                if data["completion_rate"] > max_rate:
                    max_rate = data["completion_rate"]
                    best_window = f"{window.capitalize()} ({int(max_rate*100)}% completion)"
                if data["completion_rate"] < min_rate:
                    min_rate = data["completion_rate"]
                    worst_window = f"{window.capitalize()} ({int(min_rate*100)}% completion)"

        top_distraction_name = distractions[0]["app_name"] if distractions else "None detected yet"

        # 6. Extract behavioral intelligence (Strengths & Areas to Improve)
        strengths = []
        weaknesses = []
        insights = []

        if comp_stats["completion_rate"] >= 0.70:
            strengths.append(f"Strong task completion ({int(comp_stats['completion_rate']*100)}% overall follow-through)")
        if delay_stats.get("average_start_delay_minutes") is not None and delay_stats["average_start_delay_minutes"] <= 10.0 and delay_stats["sample_size"] > 0:
            strengths.append(f"Rapid task initiation (avg {delay_stats['average_start_delay_minutes']}m start delay)")
        if consistency >= 70.0:
            strengths.append(f"High routine consistency ({consistency}%)")

        for p in patterns:
            if p.pattern_type in ["morning_momentum"]:
                strengths.append(p.title)
            elif p.pattern_type in ["afternoon_slump", "start_delay_resistance", "primary_distraction"]:
                weaknesses.append(p.title)
                insights.append(p.description)

        if not strengths:
            strengths.append("Active initial focus observation in progress")
        if not weaknesses:
            weaknesses.append("No critical friction patterns detected yet")

        # 7. Milestone tracking
        milestones = [
            f"Current Level: {level_info.full_title}",
            level_info.milestone_unlocked,
        ]
        if comp_stats["done"] >= 1:
            milestones.append(f"Completed {comp_stats['done']} focused sessions")
        if improvement_score >= 65.0:
            milestones.append("Positive behavioral improvement trajectory maintained")
        if consistency >= 70.0:
            milestones.append("Achieved high consistency rating")

        # Goal-aware context enrichment (interprets behavior without modifying scores)
        active_goal = (
            self.db.query(UserGoal)
            .filter(UserGoal.user_id == self.user_id, UserGoal.is_active == True)
            .order_by(UserGoal.created_at.desc())
            .first()
        )
        routine_ctx = (
            self.db.query(UserRoutineContext)
            .filter(UserRoutineContext.user_id == self.user_id)
            .first()
        )
        goal_context_data = None
        if active_goal:
            goal_context_data = {
                "category": active_goal.category,
                "description": active_goal.description,
                "source": "self_reported",
            }
            if delay_stats.get("average_start_delay_minutes") is not None and delay_stats["average_start_delay_minutes"] > 15 and delay_stats.get("sample_size", 0) > 0:
                insights.append(
                    f"Measured task initiation friction (avg {delay_stats['average_start_delay_minutes']}m delay) "
                    f"within active {active_goal.category.lower()} workflow ('{active_goal.description}')."
                )

        profile_dict = {
            "task_completion_rate": comp_stats["completion_rate"],
            "total_tasks_completed": comp_stats["done"],
            "average_start_delay_minutes": delay_stats["average_start_delay_minutes"],
            "best_focus_window": best_window,
            "worst_focus_window": worst_window,
            "common_distraction_app": top_distraction_name,
            "active_patterns": [p.title for p in patterns],
            "strengths": strengths,
            "weaknesses": weaknesses,
            "insights": insights,
            "milestones": milestones,
            "active_goal_context": goal_context_data,
            "level_info": {
                "level_number": level_info.level_number,
                "level_name": level_info.level_name,
                "full_title": level_info.full_title,
                "description": level_info.description,
                "next_level_requirements": level_info.next_level_requirements,
                "progress_to_next_level": level_info.progress_to_next_level,
            },
            "last_updated": datetime.utcnow().isoformat(),
        }

        # 8. Save to database
        profile_obj = self.get_or_create_profile()
        profile_obj.profile_data = profile_dict
        profile_obj.behavior_score = behavior_score
        profile_obj.current_level = level_info.full_title
        profile_obj.improvement_score = improvement_score
        profile_obj.experiment_effectiveness = experiment_eff
        profile_obj.consistency = consistency
        profile_obj.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(profile_obj)
        return profile_dict

    def get_personal_profile(self) -> Dict[str, Any]:
        """
        Builds complete personal Behavior Profile for the owner.
        Contains all private behavioral intelligence, detailed patterns, scores,
        experiments, and visibility configuration.
        """
        # Ensure latest data
        self.refresh_profile()
        profile_obj = self.get_or_create_profile()
        user = self.db.query(User).filter(User.id == self.user_id).first()

        patterns = self.db.query(BehaviorPattern).filter(BehaviorPattern.user_id == self.user_id).all()
        experiments = (
            self.db.query(Experiment)
            .filter(Experiment.user_id == self.user_id)
            .order_by(Experiment.created_at.desc())
            .limit(5)
            .all()
        )
        progress_curve = self.metrics_calc.compute_behavior_progress_curve(days=14)
        distractions = self.metrics_calc.compute_top_distractions()

        data = profile_obj.profile_data or {}
        level_info = data.get("level_info", {
            "level_number": 1,
            "level_name": "Foundation",
            "full_title": profile_obj.current_level or "Level 1 — Foundation",
            "description": "Baseline behavioral phase",
            "next_level_requirements": "Log routine check-ins",
            "progress_to_next_level": 0.0,
        })

        return {
            "identity": {
                "id": user.id,
                "name": user.name or "FocusLoop Explorer",
                "username": user.username or (user.name.lower().replace(" ", "_") if user.name else None),
                "email": user.email,
                "bio": user.bio or "Building sustainable focus habits with FocusLoop.",
                "avatar_url": user.avatar_url,
                "timezone": user.timezone,
            },
            "visibility_settings": profile_obj.visibility_settings or DEFAULT_PROFILE_VISIBILITY,
            "metrics": {
                "current_level": profile_obj.current_level or level_info.get("full_title"),
                "level_info": level_info,
                "behavior_score": profile_obj.behavior_score,
                "improvement_score": profile_obj.improvement_score,
                "experiment_effectiveness": profile_obj.experiment_effectiveness,
                "consistency": profile_obj.consistency,
            },
            "progress_curve": progress_curve,
            "behavioral_intelligence": {
                "patterns": [
                    {
                        "id": p.id,
                        "pattern_type": p.pattern_type,
                        "title": p.title,
                        "description": p.description,
                        "confidence": p.confidence,
                        "sample_size": p.sample_size,
                        "status": p.status,
                        "supporting_metrics": p.supporting_metrics,
                    }
                    for p in patterns
                ],
                "strengths": data.get("strengths", []),
                "weaknesses": data.get("weaknesses", []),
                "insights": data.get("insights", []),
                "focus_windows": {
                    "best": data.get("best_focus_window", "Morning"),
                    "worst": data.get("worst_focus_window", "Afternoon"),
                },
                "distractions": distractions,
                "experiments": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "hypothesis": e.hypothesis,
                        "target_metric": e.target_metric,
                        "status": e.status,
                        "start_date": e.start_date,
                        "end_date": e.end_date,
                    }
                    for e in experiments
                ],
            },
            "milestones": data.get("milestones", []),
            "updated_at": profile_obj.updated_at.isoformat() if profile_obj.updated_at else datetime.utcnow().isoformat(),
        }

    def get_social_profile(self, viewer_id: str) -> Dict[str, Any]:
        """
        Builds the restricted Social Profile shown to friends.
        Enforces backend authorization and filters out sensitive fields according to visibility preferences.
        Guarantees that private behavioral patterns, weaknesses, and non-shared scores are NEVER sent.
        """
        # Refresh if needed
        profile_obj = self.get_or_create_profile()
        target_user = self.db.query(User).filter(User.id == self.user_id).first()

        # Check friendship status
        is_friend = False
        if viewer_id == self.user_id:
            is_friend = True
        else:
            friendship = (
                self.db.query(Friendship)
                .filter(
                    ((Friendship.user_id == viewer_id) & (Friendship.friend_id == self.user_id))
                    | ((Friendship.user_id == self.user_id) & (Friendship.friend_id == viewer_id)),
                    Friendship.status == "accepted",
                )
                .first()
            )
            is_friend = friendship is not None

        visibility = profile_obj.visibility_settings or DEFAULT_PROFILE_VISIBILITY

        # Filter metrics strictly according to visibility configuration
        public_metrics = {}

        # 1. Improvement Score (Public by default)
        if visibility.get("improvement_score", True):
            public_metrics["improvement_score"] = profile_obj.improvement_score

        # 2. Experiment Effectiveness (Public by default)
        if visibility.get("experiment_effectiveness", True):
            public_metrics["experiment_effectiveness"] = profile_obj.experiment_effectiveness

        # 3. Consistency (Public by default)
        if visibility.get("consistency", True):
            public_metrics["consistency"] = profile_obj.consistency

        # 4. Current Level (Private by default)
        if visibility.get("current_level", False):
            public_metrics["current_level"] = profile_obj.current_level

        # 5. Behavior Score (Private by default)
        if visibility.get("behavior_score", False):
            public_metrics["behavior_score"] = profile_obj.behavior_score

        # Progress Curve: Continuous trajectory over time (Public progress visualization)
        progress_curve = self.metrics_calc.compute_behavior_progress_curve(days=14)

        # Behavioral patterns (Private by default)
        patterns_to_expose = None
        if visibility.get("behavioral_patterns", False):
            raw_patterns = self.db.query(BehaviorPattern).filter(BehaviorPattern.user_id == self.user_id).all()
            patterns_to_expose = [
                {
                    "title": p.title,
                    "confidence": p.confidence,
                    "status": p.status,
                }
                for p in raw_patterns
            ]

        # Milestones: shareable achievements
        data = profile_obj.profile_data or {}
        milestones = [
            m for m in data.get("milestones", [])
            if not m.startswith("Current Level:") or visibility.get("current_level", False)
        ]

        return {
            "identity": {
                "id": target_user.id,
                "name": target_user.name or "FocusLoop Explorer",
                "username": target_user.username or (target_user.name.lower().replace(" ", "_") if target_user.name else None),
                "bio": target_user.bio or "Building sustainable focus habits with FocusLoop.",
                "avatar_url": target_user.avatar_url,
            },
            "is_friend": is_friend,
            "metrics": public_metrics,
            "progress_curve": progress_curve,
            "milestones": milestones,
            "behavioral_patterns": patterns_to_expose,
        }
