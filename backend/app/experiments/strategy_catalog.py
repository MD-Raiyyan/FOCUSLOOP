from dataclasses import dataclass
from typing import List, Callable, Dict, Optional

# Cooldown and Suppression Constants (Requirement 8)
COOLDOWN_ACTIVE_SUPPRESSION_DAYS: Optional[int] = None  # Suppress while active
COOLDOWN_GRADUATED_POSITIVE_DAYS: int = 30              # "Graduated" / recently successful
COOLDOWN_NEGATIVE_DAYS: int = 14                        # Suppress for 14 days after negative conclusion
COOLDOWN_INCONCLUSIVE_DAYS: int = 7                     # Suppress for 7 days after inconclusive conclusion
COOLDOWN_DISMISSED_DAYS: int = 14                       # Suppress for 14 days after user dismissal

# Explicit MVP Friction Hierarchy for Tie-Breaking (Requirement 9)
PATTERN_PRIORITY_HIERARCHY: List[str] = [
    "start_delay_resistance",
    "afternoon_slump",
    "primary_distraction",
]


# Deterministic Target Calculation Formulas (Requirement 13)
def _target_delay_reduce_30(baseline: float) -> float:
    """Reduces average start delay by 30%, bounded to minimum 5.0 minutes, never negative."""
    return max(5.0, round(baseline * 0.70, 1))


def _target_delay_reduce_25(baseline: float) -> float:
    """Reduces average start delay by 25%, bounded to minimum 5.0 minutes, never negative."""
    return max(5.0, round(baseline * 0.75, 1))


def _target_completion_increase_20(baseline: float) -> float:
    """Increases completion rate by 0.20 (20%), bounded to maximum 1.0 (100%)."""
    return min(1.0, round(baseline + 0.20, 2))


def _target_completion_increase_15(baseline: float) -> float:
    """Increases completion rate by 0.15 (15%), bounded to maximum 1.0 (100%)."""
    return min(1.0, round(baseline + 0.15, 2))


@dataclass(frozen=True)
class Strategy:
    """
    Deterministic specification for a reusable behavioral intervention strategy.
    Defines measurable metrics, bounded target formulas, and default hypotheses.
    """
    intervention_type: str
    applicable_patterns: List[str]
    target_metric: str  # Supported by evaluator: "average_start_delay_minutes" or "completion_rate"
    target_direction: str  # "decrease" or "increase"
    duration_days: int  # Deterministic duration (5 days for MVP)
    default_title: str
    default_description: str
    default_hypothesis: str
    compute_target: Callable[[float], float]


# Strategy Catalog Registry (Requirement 6)
STRATEGY_CATALOG: Dict[str, Strategy] = {
    # -------------------------------------------------------------------------
    # A. start_delay_resistance
    # -------------------------------------------------------------------------
    "initiation_gateway": Strategy(
        intervention_type="initiation_gateway",
        applicable_patterns=["start_delay_resistance"],
        target_metric="average_start_delay_minutes",
        target_direction="decrease",
        duration_days=5,
        default_title="The 5-Minute Initiation Gateway",
        default_description="Commit to opening your task and working for just 5 minutes with zero expectation of finishing. You have full permission to stop after 5 minutes.",
        default_hypothesis="Lowering the initiation barrier to 5 minutes will reduce average start delay by at least 30%.",
        compute_target=_target_delay_reduce_30,
    ),
    "task_splitting": Strategy(
        intervention_type="task_splitting",
        applicable_patterns=["start_delay_resistance"],
        target_metric="average_start_delay_minutes",
        target_direction="decrease",
        duration_days=5,
        default_title="Micro-Task Partitioning",
        default_description="Divide your planned focus task into 3 concrete micro-actions before starting, and execute only the first action.",
        default_hypothesis="Eliminating task ambiguity with micro-steps will reduce task start delay by at least 25%.",
        compute_target=_target_delay_reduce_25,
    ),
    "time_shift": Strategy(
        intervention_type="time_shift",
        applicable_patterns=["start_delay_resistance"],
        target_metric="average_start_delay_minutes",
        target_direction="decrease",
        duration_days=5,
        default_title="Protected Focus Block",
        default_description="Schedule task initiation 30 minutes earlier into your morning peak focus window to bypass initiation fatigue.",
        default_hypothesis="Aligning task initiation with peak alertness will reduce average start delay by at least 25%.",
        compute_target=_target_delay_reduce_25,
    ),

    # -------------------------------------------------------------------------
    # B. afternoon_slump
    # -------------------------------------------------------------------------
    "circadian_shift": Strategy(
        intervention_type="circadian_shift",
        applicable_patterns=["afternoon_slump"],
        target_metric="completion_rate",
        target_direction="increase",
        duration_days=5,
        default_title="Morning Circadian Alignment",
        default_description="Shift demanding focus sessions before 11:30 AM and reserve the afternoon slump window for light administrative work.",
        default_hypothesis="Aligning high-friction work with morning circadian clarity will increase task completion rate by at least 20%.",
        compute_target=_target_completion_increase_20,
    ),
    "friction_reduction": Strategy(
        intervention_type="friction_reduction",
        applicable_patterns=["afternoon_slump"],
        target_metric="completion_rate",
        target_direction="increase",
        duration_days=5,
        default_title="Afternoon Scope Compression",
        default_description="Reduce planned afternoon session duration targets by 40% to maintain momentum without triggering cognitive depletion.",
        default_hypothesis="Lowering cognitive session load during post-lunch slump will increase completion rate by at least 15%.",
        compute_target=_target_completion_increase_15,
    ),

    # -------------------------------------------------------------------------
    # C. primary_distraction
    # -------------------------------------------------------------------------
    "distraction_control": Strategy(
        intervention_type="distraction_control",
        applicable_patterns=["primary_distraction"],
        target_metric="average_start_delay_minutes",
        target_direction="decrease",
        duration_days=5,
        default_title="Pre-Session App Friction Barrier",
        default_description="Close or place a 1-minute delay barrier on your primary distraction channel 5 minutes before scheduled focus initiation.",
        default_hypothesis="Introducing friction on primary distraction channels will reduce task start delay by at least 25%.",
        compute_target=_target_delay_reduce_25,
    ),
    "environment_change": Strategy(
        intervention_type="environment_change",
        applicable_patterns=["primary_distraction"],
        target_metric="completion_rate",
        target_direction="increase",
        duration_days=5,
        default_title="Single-Tab Workstation Protocol",
        default_description="Activate fullscreen focus mode with only your primary work document visible. Keep all social and messaging tabs closed.",
        default_hypothesis="Eliminating peripheral visual cues from distraction apps will increase task completion rate by at least 20%.",
        compute_target=_target_completion_increase_20,
    ),
}


def get_strategy(intervention_type: Optional[str]) -> Optional[Strategy]:
    """Retrieves strategy definition by intervention type identifier."""
    if not intervention_type:
        return None
    return STRATEGY_CATALOG.get(intervention_type)


def get_strategies_for_pattern(pattern_type: str) -> List[Strategy]:
    """Retrieves all candidate strategy definitions applicable to the given pattern type."""
    return [
        strat for strat in STRATEGY_CATALOG.values()
        if pattern_type in strat.applicable_patterns
    ]
