"""Tests for Phase 1: Time-bounded Experiment Metrics and Trustworthy Evaluation.

Verifies:
- Test 1: Pre-experiment baseline only (excludes 30d ago, experiment start, experiment period)
- Test 2: Experiment window only (excludes before and after)
- Test 3: No data during experiment (after_value=None, conclusion=inconclusive, never 0)
- Test 4: Zero actual delay (0.0 average delay is distinct from None/no data)
- Test 5: Old history does not dilute result
- Test 6: Before/after boundary precision (start-7, start, end, end+1)
- Test 7: Insufficient sample size (< MIN_EXPERIMENT_OBSERVATIONS yields inconclusive)
- Test 8: Directionality: lower is better (start delay)
- Test 9: Directionality: higher is better (completion rate)
- Test 10: Zero baseline safety (no division-by-zero, no NaN)
- Test 11: Experiment status safety (suggested or completed cannot be evaluated)
"""
from datetime import datetime, timedelta
import pytest
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.experiment import Experiment, ExperimentResult
from app.experiments.evaluator import (
    ExperimentEvaluator,
    DEFAULT_EXPERIMENT_BASELINE_DAYS,
    MIN_EXPERIMENT_OBSERVATIONS,
)


def _create_task(db_session, user_id, name="Test Task"):
    task = Task(user_id=user_id, name=name, planned_time="09:00", frequency="daily")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def _create_checkin(db_session, user_id, task_id, date, status="done", delay=None):
    checkin = TaskCheckin(
        user_id=user_id,
        task_id=task_id,
        date=date,
        status=status,
        duration_minutes=30,
        start_delay_minutes=delay,
    )
    db_session.add(checkin)
    db_session.commit()
    return checkin


def test_1_pre_experiment_baseline_only(db_session, test_user):
    """TEST 1: Baseline includes only evidence inside the pre-experiment baseline window.
    Given an experiment starting at 2026-09-10 (baseline: 2026-09-03 to 2026-09-09):
    Evidence from 30 days ago (2026-08-11), experiment start (2026-09-10), and experiment period (2026-09-12)
    must NOT enter the baseline calculation. Only 5 days ago (2026-09-05) enters.
    """
    task = _create_task(db_session, test_user.id)

    # 30 days ago: 60m delay (should NOT be in baseline)
    _create_checkin(db_session, test_user.id, task.id, "2026-08-11", delay=60)
    # 5 days ago (in baseline window 2026-09-03..2026-09-09): 3 checkins with delay=20
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=20)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=20)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-07", delay=20)
    # Experiment start day (2026-09-10): delay=5 (in experiment window, NOT baseline)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=5)
    # Experiment period (2026-09-11, 2026-09-12): delay=5
    _create_checkin(db_session, test_user.id, task.id, "2026-09-11", delay=5)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-12", delay=5)

    exp = Experiment(
        user_id=test_user.id,
        title="Start Delay Reduction",
        description="Test description",
        hypothesis="Lower initiation barrier reduces start delay",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, baseline_days=7, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    # Baseline must be strictly 20.0 (from 2026-09-05..07), NOT diluted by the 60m from 30 days ago
    assert result.before_value == 20.0
    # Experiment period must be strictly 5.0 (from 2026-09-10..12)
    assert result.after_value == 5.0
    assert result.change_value == -15.0
    assert result.conclusion == "positive"


def test_2_experiment_window_only(db_session, test_user):
    """TEST 2: after_value includes only evidence inside the experiment window [start_date, end_date]."""
    task = _create_task(db_session, test_user.id)

    # Pre-experiment baseline (2026-09-04..06): 3 observations with delay=40
    _create_checkin(db_session, test_user.id, task.id, "2026-09-04", delay=40)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=40)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=40)

    # During experiment (2026-09-10..12): 3 observations with delay=15
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=15)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-11", delay=15)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-12", delay=15)

    # After experiment end (2026-09-16): 1 observation with huge delay=90 (must NOT affect after_value)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-16", delay=90)

    exp = Experiment(
        user_id=test_user.id,
        title="Strict Window Test",
        description="Test description",
        hypothesis="Window bounding works",
        start_date="2026-09-10",
        end_date="2026-09-14",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, baseline_days=7, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    # after_value must be 15.0, unaffected by post-experiment delay=90
    assert result.after_value == 15.0
    assert result.before_value == 40.0


def test_3_no_data_during_experiment(db_session, test_user):
    """TEST 3: Experiment with zero valid observations must have after_value=None and conclusion=inconclusive,
    NEVER after_value=0.
    """
    task = _create_task(db_session, test_user.id)

    # Baseline has valid observations
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=30)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=30)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-07", delay=30)

    # Zero observations during experiment
    exp = Experiment(
        user_id=test_user.id,
        title="Ghost Experiment",
        description="No observations logged",
        hypothesis="Missing data does not mean perfection",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.after_value is None
    assert result.after_value != 0.0
    assert result.conclusion == "inconclusive"
    assert "no valid observations in experiment window" in result.result_summary


def test_4_zero_actual_delay(db_session, test_user):
    """TEST 4: A real observation with delay=0.0 must be preserved as 0.0 average delay, distinct from no data."""
    task = _create_task(db_session, test_user.id)

    # Baseline: 3 observations with delay=20
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=20)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=20)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-07", delay=20)

    # Experiment: 3 observations with delay=0 (started right on time!)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=0)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-11", delay=0)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-12", delay=0)

    exp = Experiment(
        user_id=test_user.id,
        title="Zero Delay Protocol",
        description="Punctual task initiation",
        hypothesis="Zero delay is real",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.after_value == 0.0
    assert result.after_value is not None
    assert result.change_value == -20.0
    assert result.conclusion == "positive"


def test_5_old_history_does_not_dilute_result(db_session, test_user):
    """TEST 5: Months of old evidence must not dilute a short experiment's measured result."""
    task = _create_task(db_session, test_user.id)

    # 100 days ago: 50 check-ins with terrible delay (60m)
    for i in range(10):
        d_str = (datetime(2026, 5, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
        _create_checkin(db_session, test_user.id, task.id, d_str, delay=60)

    # Baseline (2026-09-04..06): 3 observations with delay=30
    _create_checkin(db_session, test_user.id, task.id, "2026-09-04", delay=30)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=30)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=30)

    # Experiment (2026-09-10..12): 3 observations with delay=10
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=10)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-11", delay=10)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-12", delay=10)

    exp = Experiment(
        user_id=test_user.id,
        title="Anti-Dilution Test",
        description="Testing historical isolation",
        hypothesis="Old history ignored",
        start_date="2026-09-10",
        end_date="2026-09-14",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, baseline_days=7, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    # Baseline was 30.0 (not the ~55 lifetime average)
    assert result.before_value == 30.0
    # After was 10.0 (not diluted by 60m delays)
    assert result.after_value == 10.0
    assert result.change_value == -20.0
    assert result.conclusion == "positive"


def test_6_before_after_boundary(db_session, test_user):
    """TEST 6: Checks exact boundary allocation:
    - baseline start (start_date - 7 days) -> in baseline
    - day before start (start_date - 1 day) -> in baseline
    - experiment start (start_date) -> in experiment
    - experiment end (end_date) -> in experiment
    - just after experiment end (end_date + 1 day) -> excluded from both
    - day before baseline start (start_date - 8 days) -> excluded from both
    """
    task = _create_task(db_session, test_user.id)
    # Start: 2026-09-10, End: 2026-09-15
    # Baseline window: 2026-09-03 to 2026-09-09

    # 1. Day before baseline start: 2026-09-02 (excluded)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-02", delay=100)

    # 2. Baseline start boundary: 2026-09-03 (included in baseline)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-03", delay=30)
    # Mid-baseline: 2026-09-06
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=30)
    # 3. Baseline end boundary: 2026-09-09 (included in baseline)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-09", delay=30)

    # 4. Experiment start boundary: 2026-09-10 (included in experiment)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=15)
    # Mid-experiment: 2026-09-12
    _create_checkin(db_session, test_user.id, task.id, "2026-09-12", delay=15)
    # 5. Experiment end boundary: 2026-09-15 (included in experiment)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-15", delay=15)

    # 6. Just after experiment end: 2026-09-16 (excluded)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-16", delay=100)

    exp = Experiment(
        user_id=test_user.id,
        title="Boundary Precision Test",
        description="Testing boundary dates",
        hypothesis="Boundaries are exact",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, baseline_days=7, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    # Baseline: exactly the 3 entries of 30 (Sep 3, 6, 9) = 30.0 (excludes Sep 2 delay of 100)
    assert result.before_value == 30.0
    # Experiment: exactly the 3 entries of 15 (Sep 10, 12, 15) = 15.0 (excludes Sep 16 delay of 100)
    assert result.after_value == 15.0


def test_7_insufficient_sample(db_session, test_user):
    """TEST 7: Fewer observations than MIN_EXPERIMENT_OBSERVATIONS must result in conclusion=inconclusive."""
    task = _create_task(db_session, test_user.id)

    # Only 2 observations in baseline (less than 3)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-05", delay=30)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-06", delay=30)

    # Only 2 observations in experiment (less than 3)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-10", delay=10)
    _create_checkin(db_session, test_user.id, task.id, "2026-09-11", delay=10)

    exp = Experiment(
        user_id=test_user.id,
        title="Sparse Evidence Protocol",
        description="Sparse test",
        hypothesis="Low sample must be inconclusive",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.conclusion == "inconclusive"
    assert "baseline observations (2) < 3" in result.result_summary


def test_8_lower_is_better_delay(db_session, test_user):
    """TEST 8: For start delay, baseline=40, after=20 is classified as positive."""
    task = _create_task(db_session, test_user.id)

    for d in ["2026-09-04", "2026-09-05", "2026-09-06"]:
        _create_checkin(db_session, test_user.id, task.id, d, delay=40)

    for d in ["2026-09-10", "2026-09-11", "2026-09-12"]:
        _create_checkin(db_session, test_user.id, task.id, d, delay=20)

    exp = Experiment(
        user_id=test_user.id,
        title="Delay Improvement Protocol",
        description="Test",
        hypothesis="Lower delay is positive",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.before_value == 40.0
    assert result.after_value == 20.0
    assert result.change_value == -20.0
    assert result.percent_change == -50.0
    assert result.conclusion == "positive"


def test_9_higher_is_better_completion_rate(db_session, test_user):
    """TEST 9: For completion rate, baseline < after is classified as positive."""
    task1 = _create_task(db_session, test_user.id, name="Task 1")
    task2 = _create_task(db_session, test_user.id, name="Task 2")

    # Baseline: 3 days, 1 done 1 missed each day -> completion_rate = 0.50
    for d in ["2026-09-04", "2026-09-05", "2026-09-06"]:
        _create_checkin(db_session, test_user.id, task1.id, d, status="done")
        _create_checkin(db_session, test_user.id, task2.id, d, status="missed")

    # Experiment: 3 days, both done each day -> completion_rate = 1.00
    for d in ["2026-09-10", "2026-09-11", "2026-09-12"]:
        _create_checkin(db_session, test_user.id, task1.id, d, status="done")
        _create_checkin(db_session, test_user.id, task2.id, d, status="done")

    exp = Experiment(
        user_id=test_user.id,
        title="Completion Rate Protocol",
        description="Test",
        hypothesis="Higher completion rate is positive",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="completion_rate",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.before_value == 0.50
    assert result.after_value == 1.00
    assert result.change_value == 0.50
    assert result.conclusion == "positive"


def test_10_zero_baseline_safety(db_session, test_user):
    """TEST 10: When baseline=0, percentage change is None (no division by zero, no NaN/inf)."""
    task = _create_task(db_session, test_user.id)

    # Baseline: 3 checkins with delay=0
    for d in ["2026-09-04", "2026-09-05", "2026-09-06"]:
        _create_checkin(db_session, test_user.id, task.id, d, delay=0)

    # Experiment: 3 checkins with delay=15
    for d in ["2026-09-10", "2026-09-11", "2026-09-12"]:
        _create_checkin(db_session, test_user.id, task.id, d, delay=15)

    exp = Experiment(
        user_id=test_user.id,
        title="Zero Baseline Safety Test",
        description="Test zero baseline",
        hypothesis="No division by zero",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id, min_observations=3)
    result = evaluator.evaluate_experiment(exp.id)

    assert result is not None
    assert result.before_value == 0.0
    assert result.after_value == 15.0
    assert result.change_value == 15.0
    # Must be None, not inf, NaN, or zero division error
    assert result.percent_change is None
    assert result.conclusion == "negative"


def test_11_experiment_status_safety(db_session, test_user):
    """TEST 11: Attempting to evaluate an experiment that is not 'active' must be rejected
    and must not silently convert into a completed experiment.
    """
    exp_suggested = Experiment(
        user_id=test_user.id,
        title="Suggested Only Protocol",
        description="Not started",
        hypothesis="Cannot evaluate suggested",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="suggested",
    )
    db_session.add(exp_suggested)
    db_session.commit()

    evaluator = ExperimentEvaluator(db_session, test_user.id)
    res = evaluator.evaluate_experiment(exp_suggested.id)

    # Must be rejected (returns None)
    assert res is None
    # Status must NOT be changed to completed
    db_session.refresh(exp_suggested)
    assert exp_suggested.status == "suggested"


def test_api_status_validation_rejects_inactive(client, db_session, test_user):
    """API endpoint returns 400 Bad Request when attempting to evaluate a suggested experiment."""
    exp = Experiment(
        user_id=test_user.id,
        title="Draft Protocol",
        description="Draft",
        hypothesis="Cannot evaluate draft",
        start_date="2026-09-10",
        end_date="2026-09-15",
        target_metric="average_start_delay_minutes",
        status="suggested",
    )
    db_session.add(exp)
    db_session.commit()

    resp = client.post(f"/api/v1/experiments/{exp.id}/evaluate")
    assert resp.status_code == 400
    data = resp.json()
    assert "Only 'active' experiments can be evaluated" in data["detail"]
