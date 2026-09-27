"""
Grading and Level Abstraction for FocusLoop.

Provides an extensible, decoupled architecture for interpreting multi-dimensional
behavioral progress without hardcoding irreversible formulas into database models.
"""
from dataclasses import dataclass
from typing import Protocol, List, Dict, Any, Optional


@dataclass
class BehaviorLevelInfo:
    level_number: int
    level_name: str
    full_title: str
    description: str
    milestone_unlocked: str
    next_level_requirements: str
    progress_to_next_level: float  # 0.0 - 100.0


class GradingStrategy(Protocol):
    """Protocol for behavioral level calculation strategies."""

    def evaluate(
        self,
        behavior_score: float,
        improvement_score: float,
        consistency: float,
        experiment_effectiveness: float,
        total_sessions: int = 0,
    ) -> BehaviorLevelInfo:
        ...


class MultiDimensionalBehaviorGradingStrategy:
    """
    Default FocusLoop grading strategy.
    
    Evaluates behavioral progress across distinct dimensions (consistency, improvement,
    experiment adoption, and baseline behavior state) rather than a naive linear XP scale.
    """

    LEVEL_DEFINITIONS = [
        {
            "level": 1,
            "name": "Foundation",
            "title": "Level 1 — Foundation",
            "desc": "Establishing behavioral baselines and initiating routine observation.",
            "milestone": "First behavioral patterns identified",
            "req": "Maintain consistency >= 45% and complete at least 3 sessions",
            "min_consistency": 0.0,
            "min_behavior": 0.0,
            "min_sessions": 0,
        },
        {
            "level": 2,
            "name": "Pattern Explorer",
            "title": "Level 2 — Pattern Explorer",
            "desc": "Recognizing focus friction, friction windows, and delay triggers.",
            "milestone": "Procrastination triggers mapped",
            "req": "Consistency >= 60%, Improvement >= 50%, and Behavior Score >= 50",
            "min_consistency": 45.0,
            "min_behavior": 35.0,
            "min_sessions": 3,
        },
        {
            "level": 3,
            "name": "Momentum Builder",
            "title": "Level 3 — Momentum Builder",
            "desc": "Stabilizing positive routines and actively testing focus interventions.",
            "milestone": "Active behavioral experiment cycle initiated",
            "req": "Consistency >= 75%, Experiment Effectiveness >= 60%, and Behavior Score >= 65",
            "min_consistency": 60.0,
            "min_behavior": 50.0,
            "min_sessions": 8,
        },
        {
            "level": 4,
            "name": "Habit Optimizer",
            "title": "Level 4 — Habit Optimizer",
            "desc": "High reliability across focus windows and rapid recovery from setbacks.",
            "milestone": "Sustained high completion with low task initiation delay",
            "req": "Consistency >= 85%, Behavior Score >= 80%, and positive trajectory",
            "min_consistency": 75.0,
            "min_behavior": 65.0,
            "min_sessions": 15,
        },
        {
            "level": 5,
            "name": "Deep Focus Master",
            "title": "Level 5 — Deep Focus Master",
            "desc": "Autonomous self-regulation and mastered behavioral feedback loops.",
            "milestone": "Peak sustained cognitive resilience",
            "req": "Max tier achieved",
            "min_consistency": 85.0,
            "min_behavior": 80.0,
            "min_sessions": 25,
        },
    ]

    def evaluate(
        self,
        behavior_score: float,
        improvement_score: float,
        consistency: float,
        experiment_effectiveness: float,
        total_sessions: int = 0,
    ) -> BehaviorLevelInfo:
        # Determine highest qualified level
        current_tier = self.LEVEL_DEFINITIONS[0]
        level_index = 0

        for i, tier in enumerate(self.LEVEL_DEFINITIONS):
            if (
                consistency >= tier["min_consistency"]
                and behavior_score >= tier["min_behavior"]
                and total_sessions >= tier["min_sessions"]
            ):
                current_tier = tier
                level_index = i

        # Calculate progress towards next level
        if level_index < len(self.LEVEL_DEFINITIONS) - 1:
            next_tier = self.LEVEL_DEFINITIONS[level_index + 1]
            c_gap = max(0.1, next_tier["min_consistency"] - current_tier["min_consistency"])
            b_gap = max(0.1, next_tier["min_behavior"] - current_tier["min_behavior"])

            c_progress = min(1.0, max(0.0, (consistency - current_tier["min_consistency"]) / c_gap))
            b_progress = min(1.0, max(0.0, (behavior_score - current_tier["min_behavior"]) / b_gap))

            # Progress is a weighted multi-dimensional blend towards next tier
            next_progress = round(((c_progress * 0.5) + (b_progress * 0.5)) * 100, 1)
            next_req = next_tier["req"]
        else:
            next_progress = 100.0
            next_req = "Maximum level achieved"

        return BehaviorLevelInfo(
            level_number=current_tier["level"],
            level_name=current_tier["name"],
            full_title=current_tier["title"],
            description=current_tier["desc"],
            milestone_unlocked=current_tier["milestone"],
            next_level_requirements=next_req,
            progress_to_next_level=next_progress,
        )


_default_grading_strategy: GradingStrategy = MultiDimensionalBehaviorGradingStrategy()


def get_grading_strategy() -> GradingStrategy:
    """Returns the globally configured grading strategy instance."""
    return _default_grading_strategy


def set_grading_strategy(strategy: GradingStrategy):
    """Allows runtime swapping of the grading strategy for experiments or custom profiles."""
    global _default_grading_strategy
    _default_grading_strategy = strategy
