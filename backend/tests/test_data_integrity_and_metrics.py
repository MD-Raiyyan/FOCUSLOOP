import pytest
from datetime import datetime, timedelta
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.procrastination import ProcrastinationEvent
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.profile import BehaviorProfileManager
from app.ai.context_builder import AIContextBuilder


def test_today_vs_historical_isolation(client, db_session, test_user):
    """
    Test Requirement 3, 4, 5:
    - Today completed count and completion rate reflect today's evidence ONLY.
    - Previous days' records do NOT inflate today's summary.
    - Lifetime/historical summary still sees all historical evidence.
    """
    calc = BehaviorMetricsCalculator(db_session, test_user.id)

    # 1. Create a daily task
    task = Task(user_id=test_user.id, name="Daily Coding", planned_time="09:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 2. Add check-in for yesterday (done)
    checkin_yesterday = TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date=yesterday_str,
        status="done",
        duration_minutes=45,
        start_delay_minutes=10,
    )
    db_session.add(checkin_yesterday)
    db_session.commit()

    # Before today's checkin:
    today_stats = calc.compute_task_completion_stats(date=today_str)
    assert today_stats["total"] == 0
    assert today_stats["done"] == 0
    assert today_stats["completion_rate"] == 0.0

    historical_stats = calc.compute_task_completion_stats()
    assert historical_stats["total"] == 1
    assert historical_stats["done"] == 1
    assert historical_stats["completion_rate"] == 1.0

    # 3. Add check-in for today (done)
    checkin_today = TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date=today_str,
        status="done",
        duration_minutes=30,
        start_delay_minutes=0,
    )
    db_session.add(checkin_today)
    db_session.commit()

    # Now verify today's stats: exactly 1 task done today
    today_stats_after = calc.compute_task_completion_stats(date=today_str)
    assert today_stats_after["total"] == 1
    assert today_stats_after["done"] == 1
    assert today_stats_after["completion_rate"] == 1.0

    # Historical stats sees both: 2 tasks done
    historical_stats_after = calc.compute_task_completion_stats()
    assert historical_stats_after["total"] == 2
    assert historical_stats_after["done"] == 2
    assert historical_stats_after["completion_rate"] == 1.0

    # 4. Verify via GET /api/v1/behavior/summary?date=
    resp_today = client.get(f"/api/v1/behavior/summary?date={today_str}")
    assert resp_today.status_code == 200
    today_summary = resp_today.json()
    assert today_summary["total_tasks_tracked"] == 1
    assert today_summary["completed_tasks"] == 1
    assert today_summary["completion_rate"] == 1.0
    assert today_summary["date"] == today_str

    # Verify all-time summary without date
    resp_all = client.get("/api/v1/behavior/summary")
    assert resp_all.status_code == 200
    all_summary = resp_all.json()
    assert all_summary["total_tasks_tracked"] == 2
    assert all_summary["completed_tasks"] == 2
    assert all_summary["completion_rate"] == 1.0


def test_start_delay_no_data_vs_real_zero(db_session, test_user):
    """
    Test Requirement 6, 7:
    - No start-delay data is returned as None (not 0.0).
    - Actual 0-minute delay is returned as 0.0 (preserved as measured zero).
    - Multiple records average correctly.
    """
    calc = BehaviorMetricsCalculator(db_session, test_user.id)

    # 1. No check-ins at all
    stats_empty = calc.compute_start_delay_stats()
    assert stats_empty["sample_size"] == 0
    assert stats_empty["average_start_delay_minutes"] is None
    assert stats_empty["max_delay_minutes"] is None

    # 2. Check-in exists but without start_delay_minutes (e.g. no delay telemetry)
    task = Task(user_id=test_user.id, name="Reading", frequency="daily")
    db_session.add(task)
    db_session.commit()

    c1 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-20", status="done", start_delay_minutes=None)
    db_session.add(c1)
    db_session.commit()

    stats_no_delay = calc.compute_start_delay_stats()
    assert stats_no_delay["sample_size"] == 0
    assert stats_no_delay["average_start_delay_minutes"] is None

    # 3. Check-in with actual 0-minute delay (started right on time!)
    c2 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-21", status="done", start_delay_minutes=0)
    db_session.add(c2)
    db_session.commit()

    stats_zero_delay = calc.compute_start_delay_stats()
    assert stats_zero_delay["sample_size"] == 1
    assert stats_zero_delay["average_start_delay_minutes"] == 0.0
    assert stats_zero_delay["max_delay_minutes"] == 0

    # 4. Another check-in with 20-minute delay
    c3 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-22", status="done", start_delay_minutes=20)
    db_session.add(c3)
    db_session.commit()

    stats_multi = calc.compute_start_delay_stats()
    assert stats_multi["sample_size"] == 2
    assert stats_multi["average_start_delay_minutes"] == 10.0
    assert stats_multi["max_delay_minutes"] == 20


def test_progress_curve_truthful_evidence(db_session, test_user):
    """
    Test Requirement 13, 14, 15:
    - New user progress curve contains no fabricated stable days.
    - Stable state requires actual evidence across consecutive days.
    - Existing real evidence produces actual curve points only.
    """
    calc = BehaviorMetricsCalculator(db_session, test_user.id)

    # 1. Brand-new user: zero evidence -> empty curve
    empty_curve = calc.compute_behavior_progress_curve(days=14)
    assert empty_curve == []

    # 2. One day of data: exactly 1 point with trend="initial"
    task = Task(user_id=test_user.id, name="Deep Focus", frequency="daily")
    db_session.add(task)
    db_session.commit()

    c1 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-25", status="done", start_delay_minutes=5)
    db_session.add(c1)
    db_session.commit()

    curve_1 = calc.compute_behavior_progress_curve(days=14)
    assert len(curve_1) == 1
    assert curve_1[0]["date"] == "2026-09-25"
    assert curve_1[0]["trend"] == "initial"
    assert curve_1[0]["progress_score"] > 0

    # 3. Second day of similar data: difference within ±3.0 -> trend="stable" backed by evidence!
    c2 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-26", status="done", start_delay_minutes=5)
    db_session.add(c2)
    db_session.commit()

    curve_2 = calc.compute_behavior_progress_curve(days=14)
    assert len(curve_2) == 2
    assert curve_2[0]["trend"] == "initial"
    assert curve_2[1]["trend"] == "stable"
    assert curve_2[1]["date"] == "2026-09-26"

    # 4. Third day with missed task: setback
    c3 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-27", status="missed")
    db_session.add(c3)
    db_session.commit()

    curve_3 = calc.compute_behavior_progress_curve(days=14)
    assert len(curve_3) == 3
    assert curve_3[2]["trend"] == "setback"

    # 5. Fourth day with 100% completion: recovery
    c4 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-28", status="done", start_delay_minutes=0)
    db_session.add(c4)
    db_session.commit()

    curve_4 = calc.compute_behavior_progress_curve(days=14)
    assert len(curve_4) == 4
    assert curve_4[3]["trend"] == "recovery"


def test_metric_contract_ranges_and_baselines(db_session, test_user):
    """
    Test Requirement 8, 9, 10, 11, 12:
    - completion_rate is 0.0 to 1.0 ratio
    - behavior_score is 0.0 to 100.0 score (baseline = 50.0 for new user)
    - improvement_score is 0.0 to 100.0 score (baseline = 55.0 for new user)
    - consistency is 0.0 to 100.0 score (baseline = 50.0 for new user)
    - experiment_effectiveness is 0.0 to 100.0 score (baseline = 70.0 for new user)
    """
    calc = BehaviorMetricsCalculator(db_session, test_user.id)

    comp = calc.compute_task_completion_stats()
    assert 0.0 <= comp["completion_rate"] <= 1.0

    b_score = calc.compute_behavior_score()
    assert b_score == 50.0  # Baseline
    assert 0.0 <= b_score <= 100.0

    imp_score = calc.compute_improvement_score()
    assert imp_score == 55.0  # Baseline
    assert 0.0 <= imp_score <= 100.0

    cons_score = calc.compute_consistency_score()
    assert cons_score == 50.0  # Baseline
    assert 0.0 <= cons_score <= 100.0

    eff_score = calc.compute_experiment_effectiveness()
    assert eff_score == 70.0  # Baseline
    assert 0.0 <= eff_score <= 100.0


def test_ai_context_freshness_after_checkin(client, db_session, test_user):
    """
    Test Requirement 17, 18:
    - New check-in updates behavior state immediately.
    - AI context builder retrieves fresh evidence on next call.
    """
    # 1. Initially user has 0 checkins
    builder = AIContextBuilder(db_session, test_user.id)
    ctx1 = builder.build_context(question="How is my progress?")
    assert ctx1.metrics["task_completion"]["total_tasks_tracked"] == 0
    assert ctx1.metrics["task_completion"]["completed_tasks"] == 0

    # 2. Record check-in via API
    task = Task(user_id=test_user.id, name="Writing Code", frequency="daily")
    db_session.add(task)
    db_session.commit()

    checkin = TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date="2026-09-27",
        status="done",
        duration_minutes=40,
        start_delay_minutes=5,
    )
    db_session.add(checkin)
    db_session.commit()

    # 3. AI context builder on the next query sees fresh data
    ctx2 = builder.build_context(question="How is my progress?")
    assert ctx2.metrics["task_completion"]["total_tasks_tracked"] == 1
    assert ctx2.metrics["task_completion"]["completed_tasks"] == 1
    assert ctx2.metrics["task_completion"]["completion_rate"] == 1.0
