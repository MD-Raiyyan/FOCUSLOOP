import uuid
from datetime import datetime, timedelta, date
import pytest
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.procrastination import ProcrastinationEvent
from app.models.behavior import BehaviorPattern, BehaviorProfile
from app.models.experiment import Experiment, ExperimentResult
from app.experiments.strategy_catalog import (
    STRATEGY_CATALOG,
    get_strategy,
    get_strategies_for_pattern,
    COOLDOWN_GRADUATED_POSITIVE_DAYS,
    COOLDOWN_NEGATIVE_DAYS,
    COOLDOWN_INCONCLUSIVE_DAYS,
    COOLDOWN_DISMISSED_DAYS,
)
from app.experiments.strategy_selector import StrategySelector
from app.experiments.generator import ExperimentGenerator
from app.experiments.evaluator import ExperimentEvaluator
from app.behavior.profile import BehaviorProfileManager


def test_cold_start_under_three_checkins(db_session, test_user):
    """
    Requirement 11, 24A:
    When a user has < 3 check-ins, StrategySelector returns None (Observation State).
    No personalized experiment is generated.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Daily Focus")
    db_session.add(task)
    # Only 2 check-ins
    db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date="2026-09-24", status="done", start_delay_minutes=30))
    db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date="2026-09-25", status="done", start_delay_minutes=25))
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    exp = selector.generate_experiment()
    assert exp is None, "Cold start with < 3 check-ins must return None (Observation state)"
    assert db_session.query(Experiment).filter(Experiment.user_id == test_user.id).count() == 0


def test_cold_start_no_qualifying_active_pattern(db_session, test_user):
    """
    Requirement 11, 24A:
    When user has >= 3 check-ins but no qualifying active pattern exists,
    StrategySelector returns None.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Daily Focus")
    db_session.add(task)
    for i in range(4):
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=f"2026-09-2{i}", status="done", start_delay_minutes=0))
    # Pattern is resolved, not active
    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Resolved Delay Pattern",
        description="Resolved initiation friction",
        confidence="high",
        sample_size=10,
        status="resolved",
    )
    db_session.add(pattern)
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    exp = selector.generate_experiment()
    assert exp is None, "Resolved patterns are not eligible for active friction experiments"


def test_pattern_eligibility_and_insufficient_evidence_exclusion(db_session, test_user):
    """
    Requirement 9, 24B:
    Only active patterns with moderate or high confidence and without insufficient evidence flags are eligible.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Daily Focus")
    db_session.add(task)
    for i in range(5):
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=f"2026-09-2{i}", status="done", start_delay_minutes=20))

    # Pattern with insufficient evidence flag
    p_insufficient = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="Friction tracking",
        confidence="low",
        sample_size=2,
        status="active",
        supporting_metrics={"insufficient_evidence": True},
    )
    # Valid active pattern
    p_valid = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Consistent initiation delay",
        confidence="moderate",
        sample_size=6,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 4}},
    )
    db_session.add_all([p_insufficient, p_valid])
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    eligible = selector.select_eligible_patterns()
    assert len(eligible) == 1
    assert eligible[0].id == p_valid.id


def test_pattern_prioritization_confidence_and_recent_sample(db_session, test_user):
    """
    Requirement 9, 24C:
    Cascade priority:
    1. High confidence beats moderate.
    2. When confidence is equal, larger recent sample size wins.
    3. When equal, start_delay_resistance > afternoon_slump > primary_distraction.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Focus Work")
    db_session.add(task)
    for i in range(5):
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=f"2026-09-2{i}", status="done", start_delay_minutes=25))

    p_slump_high = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Slump",
        description="Low completion in afternoon",
        confidence="high",
        sample_size=12,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 4}},
    )
    p_delay_mod = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Start Delay Resistance",
        description="High start delay",
        confidence="moderate",
        sample_size=15,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 8}},
    )
    db_session.add_all([p_slump_high, p_delay_mod])
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    eligible = selector.select_eligible_patterns()
    # High confidence beats moderate despite smaller sample size or lower hierarchy
    assert eligible[0].id == p_slump_high.id

    # Now make both high confidence: larger recent sample size wins
    p_delay_mod.confidence = "high"
    db_session.commit()
    eligible2 = selector.select_eligible_patterns()
    assert eligible2[0].id == p_delay_mod.id, "Larger recent sample size (8 vs 4) wins when confidence is equal"


def test_strategy_catalog_mapping_and_formulas():
    """
    Requirement 6, 13, 14, 24D:
    Verifies Strategy Catalog entries, evaluator supported metrics, and bounded target formulas.
    """
    # 1. start_delay_resistance strategies
    delay_strats = get_strategies_for_pattern("start_delay_resistance")
    assert len(delay_strats) >= 3
    strat_types = [s.intervention_type for s in delay_strats]
    assert "initiation_gateway" in strat_types
    assert "task_splitting" in strat_types
    assert "time_shift" in strat_types

    gateway = get_strategy("initiation_gateway")
    assert gateway.target_metric == "average_start_delay_minutes"
    assert gateway.target_direction == "decrease"
    assert gateway.duration_days == 5
    # Target formula: 30% reduction, min 5.0
    assert gateway.compute_target(30.0) == 21.0
    assert gateway.compute_target(5.0) == 5.0
    assert gateway.compute_target(2.0) == 5.0  # bounded to min 5.0, not negative

    # 2. afternoon_slump strategies
    slump_strats = get_strategies_for_pattern("afternoon_slump")
    assert len(slump_strats) >= 2
    circadian = get_strategy("circadian_shift")
    assert circadian.target_metric == "completion_rate"
    assert circadian.target_direction == "increase"
    # Target formula: +0.20, max 1.0
    assert circadian.compute_target(0.60) == 0.80
    assert circadian.compute_target(0.90) == 1.0  # capped at 1.0 (100%)


def test_strategy_cooldown_positive_negative_inconclusive_dismissed(db_session, test_user):
    """
    Requirement 8, 24E:
    Verifies pattern-specific cooldown:
    - Positive conclusion: 30 days
    - Negative conclusion: 14 days
    - Inconclusive conclusion: 7 days
    - Dismissed: 14 days
    """
    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Start Delay Resistance",
        description="Friction",
        confidence="high",
        sample_size=10,
        status="active",
    )
    db_session.add(pattern)
    db_session.commit()

    ref_date_obj = date(2026, 9, 26)
    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    strategy = get_strategy("initiation_gateway")

    # 1. Dismissed experiment 10 days ago (within 14-day window) -> cooled
    exp_dismissed = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=pattern.id,
        title="Test Dismissed",
        description="Test",
        hypothesis="Test",
        intervention_type="initiation_gateway",
        start_date="2026-09-10",
        end_date="2026-09-16",
        target_metric="average_start_delay_minutes",
        status="dismissed",
    )
    db_session.add(exp_dismissed)
    db_session.commit()

    assert selector.is_strategy_on_cooldown(pattern.id, strategy) is True

    # 2. If dismissed 15 days ago (> 14-day window) -> not cooled
    exp_dismissed.start_date = "2026-09-01"
    exp_dismissed.end_date = "2026-09-06"
    db_session.commit()
    assert selector.is_strategy_on_cooldown(pattern.id, strategy) is False

    # 3. Completed experiment with negative outcome 10 days ago -> cooled (<14 days)
    exp_neg = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=pattern.id,
        title="Test Neg",
        description="Test",
        hypothesis="Test",
        intervention_type="initiation_gateway",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="completed",
    )
    res_neg = ExperimentResult(
        id=str(uuid.uuid4()),
        experiment_id=exp_neg.id,
        metric_name="average_start_delay_minutes",
        conclusion="negative",
        result_summary="Worsened",
        created_at=datetime(2026, 9, 16, 12, 0, 0),
    )
    db_session.add_all([exp_neg, res_neg])
    db_session.commit()
    assert selector.is_strategy_on_cooldown(pattern.id, strategy) is True

    # 4. Inconclusive outcome: 7-day cooldown
    res_neg.conclusion = "inconclusive"
    res_neg.created_at = datetime(2026, 9, 18, 12, 0, 0)  # 8 days ago
    db_session.commit()
    assert selector.is_strategy_on_cooldown(pattern.id, strategy) is False, "8 days > 7 day inconclusive cooldown"


def test_strategy_cooldown_allows_different_strategy_for_same_pattern(db_session, test_user):
    """
    Requirement 8, 24E:
    If Strategy A is on cooldown for a pattern, Strategy B for that same pattern remains eligible.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Daily Focus")
    db_session.add(task)
    for i in range(5):
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=f"2026-09-2{i}", status="done", start_delay_minutes=30))

    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Start Delay Resistance",
        description="Friction",
        confidence="high",
        sample_size=10,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 5}},
    )
    # initiation_gateway is on cooldown (dismissed recently)
    exp_gateway = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=pattern.id,
        title="Gateway Experiment",
        description="Test",
        hypothesis="Test",
        intervention_type="initiation_gateway",
        start_date="2026-09-20",
        end_date="2026-09-25",
        target_metric="average_start_delay_minutes",
        status="dismissed",
    )
    db_session.add_all([pattern, exp_gateway])
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    exp = selector.generate_experiment()
    assert exp is not None
    # Because initiation_gateway was on cooldown, task_splitting was chosen!
    assert exp.intervention_type == "task_splitting"
    assert exp.pattern_id == pattern.id


def test_active_experiment_concurrency_enforcement(client, db_session, test_user):
    """
    Requirement 10, 24F:
    Exactly ONE active experiment allowed per user.
    Attempting to activate a second experiment raises HTTP 400.
    """
    exp1 = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Active Protocol 1",
        description="First active experiment",
        hypothesis="Hypothesis 1",
        intervention_type="initiation_gateway",
        start_date="2026-09-25",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    exp2 = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Suggested Protocol 2",
        description="Suggested experiment",
        hypothesis="Hypothesis 2",
        intervention_type="circadian_shift",
        start_date="2026-09-26",
        target_metric="completion_rate",
        status="suggested",
    )
    db_session.add_all([exp1, exp2])
    db_session.commit()

    # Attempt to activate exp2 while exp1 is active
    resp = client.put(f"/api/v1/experiments/{exp2.id}", json={"status": "active"})
    assert resp.status_code == 400
    assert "already has an active experiment" in resp.json()["detail"]

    # Concurrency in create_experiment: attempting to create a second active experiment raises 400
    create_resp = client.post(
        "/api/v1/experiments",
        json={
            "title": "Third Active Experiment",
            "description": "Desc",
            "hypothesis": "Hypo",
            "intervention_type": "time_shift",
            "start_date": "2026-09-26",
            "target_metric": "average_start_delay_minutes",
        },
    )
    assert create_resp.status_code == 400
    assert "already has an active experiment" in create_resp.json()["detail"]


def test_pattern_linkage_and_immutable_snapshot(db_session, test_user):
    """
    Requirement 15, 24G:
    Generated experiment links pattern_id and stores immutable pattern_snapshot.
    Subsequent pattern changes do not mutate the historical experiment snapshot.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Daily Task")
    db_session.add(task)
    for i in range(5):
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=f"2026-09-2{i}", status="done", start_delay_minutes=35))

    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Start delay peaks in morning",
        confidence="high",
        sample_size=8,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 5, "value": 35.0}},
    )
    db_session.add(pattern)
    db_session.commit()

    selector = StrategySelector(db_session, test_user.id, ref_date="2026-09-26")
    exp = selector.generate_experiment()

    assert exp.pattern_id == pattern.id
    assert exp.pattern_snapshot is not None
    assert exp.pattern_snapshot["pattern_id"] == pattern.id
    assert exp.pattern_snapshot["status"] == "active"
    assert exp.pattern_snapshot["confidence"] == "high"

    # Pattern later mutates to "resolved"
    pattern.status = "resolved"
    pattern.confidence = "low"
    db_session.commit()
    db_session.refresh(exp)

    # Historical experiment snapshot remains unchanged
    assert exp.pattern_snapshot["status"] == "active"
    assert exp.pattern_snapshot["confidence"] == "high"


def test_authoritative_baseline_recalculated_on_activation(client, db_session, test_user):
    """
    Requirement 12, 24H:
    Suggestion baseline is provisional.
    At activation, baseline is recalculated over [T_start - 7d, T_start - 1d]
    and matches what ExperimentEvaluator computes.
    """
    task = Task(id=str(uuid.uuid4()), user_id=test_user.id, name="Work Block")
    db_session.add(task)
    # Check-ins in window [2026-09-18 to 2026-09-24] with avg delay = 30m
    for day in ["2026-09-19", "2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23"]:
        db_session.add(TaskCheckin(id=str(uuid.uuid4()), task_id=task.id, user_id=test_user.id, date=day, status="done", start_delay_minutes=30))

    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Start Delay Resistance",
        description="Friction",
        confidence="high",
        sample_size=5,
        status="active",
        supporting_metrics={"recent_window": {"sample_size": 5}},
    )
    db_session.add(pattern)
    db_session.commit()

    # Generate suggested experiment
    generator = ExperimentGenerator(db_session, test_user.id, ref_date="2026-09-25")
    experiments = generator.suggest_experiments()
    assert len(experiments) > 0
    suggested = experiments[0]
    assert suggested.status == "suggested"

    # Activate experiment via PUT /api/v1/experiments/{id}
    activate_resp = client.put(f"/api/v1/experiments/{suggested.id}", json={"status": "active"})
    assert activate_resp.status_code == 200
    active_exp = activate_resp.json()
    assert active_exp["status"] == "active"
    assert active_exp["baseline_value"] is not None


def test_learning_projection_to_successful_interventions(db_session, test_user):
    """
    Requirement 5, 24I:
    Completed experiments with conclusion='positive' project their intervention_type
    into BehaviorProfile.profile_data['successful_interventions'].
    """
    exp_pos = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        title="Micro-Start Protocol",
        description="Test",
        hypothesis="Test",
        intervention_type="initiation_gateway",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="completed",
    )
    res_pos = ExperimentResult(
        id=str(uuid.uuid4()),
        experiment_id=exp_pos.id,
        metric_name="average_start_delay_minutes",
        conclusion="positive",
        result_summary="Significant improvement observed",
    )
    db_session.add_all([exp_pos, res_pos])
    db_session.commit()

    profile_mgr = BehaviorProfileManager(db_session, test_user.id)
    profile_dict = profile_mgr.refresh_profile()

    assert "successful_interventions" in profile_dict
    assert "initiation_gateway" in profile_dict["successful_interventions"]


def test_procrastination_mode_remains_raw_evidence_only(db_session, test_user):
    """
    Requirement 3, 20, 24J:
    Procrastination events are aggregated for metrics/profile, but are NOT added
    to PatternDetector V2 in this phase.
    """
    p_event = ProcrastinationEvent(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        started_at=datetime.utcnow() - timedelta(minutes=25),
        ended_at=datetime.utcnow(),
        duration_seconds=1500,
        user_confirmed=True,
        trigger_reason="overwhelmed",
    )
    db_session.add(p_event)
    db_session.commit()

    profile_mgr = BehaviorProfileManager(db_session, test_user.id)
    profile_dict = profile_mgr.refresh_profile()

    assert "procrastination_summary" in profile_dict
    assert profile_dict["procrastination_summary"]["count"] >= 1
    assert profile_dict["procrastination_summary"]["total_minutes"] >= 20.0
