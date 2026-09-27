import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.behavior import BehaviorPattern, BehaviorProfile
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.patterns import PatternDetector
from app.ai.context_builder import AIContextBuilder


def test_insufficient_evidence_does_not_create_pattern(db_session, test_user):
    """
    Part 3 & 18: Event != Pattern.
    Tiny samples (e.g. 1 or 2 isolated observations) must NOT create an active pattern.
    """
    task = Task(user_id=test_user.id, name="Afternoon Task", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Only 1 observation with high delay
    c1 = TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date="2026-09-20",
        status="done",
        start_delay_minutes=45,
    )
    db_session.add(c1)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-21")
    patterns = detector.detect_and_update_patterns()

    # No pattern should be created from a single observation!
    pattern_types = [p.pattern_type for p in patterns]
    assert "afternoon_slump" not in pattern_types
    assert "start_delay_resistance" not in pattern_types

    # Add a second observation (still only 2 total, insufficient for habit confirmation)
    c2 = TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date="2026-09-21",
        status="done",
        start_delay_minutes=40,
    )
    db_session.add(c2)
    db_session.commit()

    patterns = detector.detect_and_update_patterns()
    pattern_types = [p.pattern_type for p in patterns]
    # Still insufficient (needs >= 4 afternoon tasks across >= 2 distinct days for slump; >= 5 for delay resistance)
    assert "afternoon_slump" not in pattern_types
    assert "start_delay_resistance" not in pattern_types


def test_sufficient_evidence_creates_active_pattern_with_metrics(db_session, test_user):
    """
    Verifies that sufficient evidence (>= 5 delay observations) with consistently high delay
    creates an active start_delay_resistance pattern with structured supporting evidence.
    """
    task = Task(user_id=test_user.id, name="Writing", planned_time="10:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Add 5 checkins with high delay across 5 distinct days
    dates = ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14"]
    for d in dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=30,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-15")
    patterns = detector.detect_and_update_patterns()

    delay_pat = next((p for p in patterns if p.pattern_type == "start_delay_resistance"), None)
    assert delay_pat is not None
    assert delay_pat.status == "active"
    assert delay_pat.sample_size == 5
    assert delay_pat.confidence in ("low", "moderate")

    # Verify structured supporting metrics
    sup = delay_pat.supporting_metrics
    assert sup is not None
    assert sup["pattern_id"] == delay_pat.id
    assert sup["metric_name"] == "average_start_delay_minutes"
    assert len(sup["time_series"]) == 5
    for pt in sup["time_series"]:
        assert pt["date"] in dates
        assert pt["value"] == 30.0
        assert pt["sample_size"] == 1


def test_recency_and_contradiction_transitions_to_improving(db_session, test_user):
    """
    Part 4, 5, 6, 7:
    Historical period: Days 1-5 have high start delay (35 min).
    Recent period: Days 10-13 have low start delay (8 min, 4 sessions).
    The pattern must NOT stay stubbornly active.
    It must recognize the contradictory evidence and transition to 'improving'.
    """
    task = Task(user_id=test_user.id, name="Daily Study", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Historical period: 5 sessions with 35 min delay
    hist_dates = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]
    for d in hist_dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=35,
        ))
    db_session.commit()

    # Evaluate at end of historical period
    detector_hist = PatternDetector(db_session, test_user.id, ref_date="2026-09-06")
    patterns_hist = detector_hist.detect_and_update_patterns()
    p_hist = next(p for p in patterns_hist if p.pattern_type == "start_delay_resistance")
    assert p_hist.status == "active"
    original_id = p_hist.id

    # Recent period: 3 sessions with prompt start (8 min delay) in the recent 7-day window
    # Ref date: 2026-09-15. Recent window: [2026-09-08, 2026-09-15]
    recent_dates = ["2026-09-11", "2026-09-12", "2026-09-13"]
    for d in recent_dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=8,
        ))
    db_session.commit()

    # Re-evaluate with ref_date = 2026-09-15
    detector_now = PatternDetector(db_session, test_user.id, ref_date="2026-09-15")
    patterns_now = detector_now.detect_and_update_patterns()

    p_now = next(p for p in patterns_now if p.pattern_type == "start_delay_resistance")
    # Must preserve stable ID
    assert p_now.id == original_id
    # Must transition to improving!
    assert p_now.status == "improving"
    assert "Improving" in p_now.title

    sup = p_now.supporting_metrics
    assert sup["contradiction_detected"] is True
    assert sup["trend"] == "improving"
    assert sup["recent_window"]["value"] == 8.0
    assert sup["recent_window"]["sample_size"] == 3
    assert sup["historical_window"]["value"] == 35.0
    assert sup["historical_window"]["sample_size"] == 5


def test_sustained_improvement_transitions_to_resolved(db_session, test_user):
    """
    Part 5 & 7:
    When the recent window has sustained evidence (>= 5 sessions) consistently showing
    low friction (< 15 min), the pattern transitions to 'resolved'.
    """
    task = Task(user_id=test_user.id, name="Daily Study", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Historical: 5 sessions with 40 min delay
    for d in ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=40,
        ))
    db_session.commit()

    # First detector run marks it active
    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-06")
    patterns = detector.detect_and_update_patterns()
    p = next(p for p in patterns if p.pattern_type == "start_delay_resistance")
    assert p.status == "active"
    orig_id = p.id

    # Recent window: 5 prompt sessions in the last 7 days (ref_date = 2026-09-17)
    recent_dates = ["2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14", "2026-09-15"]
    for d in recent_dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=5,
        ))
    db_session.commit()

    # Re-evaluate
    detector_resolved = PatternDetector(db_session, test_user.id, ref_date="2026-09-17")
    patterns_resolved = detector_resolved.detect_and_update_patterns()

    p_resolved = next(p for p in patterns_resolved if p.pattern_type == "start_delay_resistance")
    assert p_resolved.id == orig_id
    assert p_resolved.status == "resolved"
    assert "Resolved" in p_resolved.title
    assert p_resolved.supporting_metrics["trend"] == "resolved"
    assert p_resolved.supporting_metrics["recent_window"]["value"] == 5.0
    assert p_resolved.supporting_metrics["recent_window"]["sample_size"] == 5


def test_afternoon_slump_context_comparison_and_graphs(db_session, test_user):
    """
    Part 8, 9, 10, 11:
    Verifies that afternoon slump provides:
    - Contextual comparison (Morning vs Afternoon vs Evening)
    - Real time series points without fabricated dates
    - Correct sample sizes and values
    """
    task_morn = Task(user_id=test_user.id, name="Morning Plan", planned_time="08:00", frequency="daily")
    task_aft = Task(user_id=test_user.id, name="Afternoon Work", planned_time="14:00", frequency="daily")
    task_eve = Task(user_id=test_user.id, name="Evening Review", planned_time="19:00", frequency="daily")
    db_session.add_all([task_morn, task_aft, task_eve])
    db_session.commit()

    # 4 days of observations
    dates = ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13"]
    for d in dates:
        # Morning: 5 min delay, done
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task_morn.id,
            date=d,
            status="done",
            start_delay_minutes=5,
        ))
        # Afternoon: 30 min delay, partial
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task_aft.id,
            date=d,
            status="partial",
            start_delay_minutes=30,
        ))
        # Evening: 10 min delay, done
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task_eve.id,
            date=d,
            status="done",
            start_delay_minutes=10,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-14")
    patterns = detector.detect_and_update_patterns()

    slump_pat = next((p for p in patterns if p.pattern_type == "afternoon_slump"), None)
    assert slump_pat is not None
    assert slump_pat.status == "active"
    assert slump_pat.sample_size == 4

    sup = slump_pat.supporting_metrics
    # Context comparison checks
    contexts = {c["context"]: c for c in sup["context_comparison"]}
    assert "Morning" in contexts
    assert "Afternoon" in contexts
    assert "Evening" in contexts

    assert contexts["Morning"]["value"] == 5.0
    assert contexts["Morning"]["sample_size"] == 4
    assert contexts["Afternoon"]["value"] == 30.0
    assert contexts["Afternoon"]["sample_size"] == 4
    assert contexts["Evening"]["value"] == 10.0
    assert contexts["Evening"]["sample_size"] == 4

    # Time series points: exactly 4 real points, no fabricated data
    ts = sup["time_series"]
    assert len(ts) == 4
    for pt in ts:
        assert pt["date"] in dates
        assert pt["value"] == 30.0
        assert pt["sample_size"] == 1


def test_pattern_idempotency_and_stability(db_session, test_user):
    """
    Part 15 & 18:
    Repeated runs of detect_and_update_patterns must be idempotent:
    - Never create duplicate rows for the same pattern_type
    - Preserve the primary key ID
    - Update timestamps and metrics cleanly
    """
    task = Task(user_id=test_user.id, name="Daily Task", planned_time="09:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    for d in ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14"]:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=25,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-15")
    run1 = detector.detect_and_update_patterns()
    p1 = next(p for p in run1 if p.pattern_type == "start_delay_resistance")
    id1 = p1.id

    # Second run immediately
    run2 = detector.detect_and_update_patterns()
    p2 = next(p for p in run2 if p.pattern_type == "start_delay_resistance")
    id2 = p2.id

    assert id1 == id2

    # Check total rows in database
    count = db_session.query(BehaviorPattern).filter(
        BehaviorPattern.user_id == test_user.id,
        BehaviorPattern.pattern_type == "start_delay_resistance",
    ).count()
    assert count == 1


def test_ai_context_builder_consumes_improving_and_resolved_patterns(db_session, test_user):
    """
    Part 14 & 18:
    AIContextBuilder must retrieve active, improving, and resolved patterns,
    exposing status, trend, recent_value, and historical_value without LLM determining truth.
    """
    # Create an improving pattern
    improving_pattern = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Task Initiation Friction (Improving)",
        description="Your recent task start delay averages 8 mins (down from 35 mins).",
        confidence="moderate",
        sample_size=8,
        status="improving",
        supporting_metrics={
            "trend": "improving",
            "recent_window": {"value": 8.0, "sample_size": 3},
            "historical_window": {"value": 35.0, "sample_size": 5},
        },
    )
    db_session.add(improving_pattern)
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="What are my behavioral patterns?")

    assert len(ctx.patterns) >= 1
    found = next(p for p in ctx.patterns if p["pattern_type"] == "start_delay_resistance")
    assert found["status"] == "improving"
    assert found["trend"] == "improving"
    assert found["recent_value"] == 8.0
    assert found["historical_value"] == 35.0


def test_pattern_relapse_from_resolved_to_active(db_session, test_user):
    """
    Part 7: Pattern Lifecycle.
    If a pattern was 'resolved' or 'improving', but the user encounters friction again
    in recent sessions (>= 3 recent observations with high delay), the pattern relapses to 'active'.
    """
    task = Task(user_id=test_user.id, name="Evening Coding", planned_time="19:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Add historical checkins matching the resolved pattern
    for d in ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=5,
        ))

    # Pre-existing pattern in DB marked as resolved
    resolved_pattern = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Task Initiation Friction (Resolved)",
        description="Resolved friction",
        confidence="high",
        sample_size=5,
        status="resolved",
        supporting_metrics={"trend": "resolved"},
    )
    db_session.add(resolved_pattern)
    db_session.commit()

    # Now user logs 3 sessions with severe delay in the recent window
    for d in ["2026-09-20", "2026-09-21", "2026-09-22"]:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=40,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-23")
    patterns = detector.detect_and_update_patterns()

    relapsed_pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")
    assert relapsed_pat.id == resolved_pattern.id
    assert relapsed_pat.status == "active"
    assert relapsed_pat.supporting_metrics["trend"] == "relapse"


def test_recency_decay_weighting_math(db_session, test_user):
    """
    Part 4: Mathematical verification of continuous exponential recency decay.
    weight = exp(-lambda * age_days) where lambda = ln(2) / 7.
    """
    calc = BehaviorMetricsCalculator(db_session, test_user.id)
    # Observations:
    # 2026-09-15 (today, age 0): value 10 -> weight 1.0
    # 2026-09-08 (7 days ago, age 7): value 30 -> weight 0.5
    # Expected weighted avg: (1.0*10 + 0.5*30) / (1.0 + 0.5) = (10 + 15) / 1.5 = 25 / 1.5 = 16.666... -> 16.7
    obs = [("2026-09-15", 10.0), ("2026-09-08", 30.0)]
    w_avg = calc.calculate_recency_weighted_average(obs, half_life_days=7.0, ref_date="2026-09-15")
    assert w_avg == 16.7


def test_graph_data_has_no_fabricated_gap_points(db_session, test_user):
    """
    Part 10 & 11:
    Verifies that time series contains ONLY real dates with actual observations.
    Days with no checkins must NOT produce synthetic 0s, 50%s, or interpolated points.
    """
    task = Task(user_id=test_user.id, name="Daily Task", frequency="daily")
    db_session.add(task)
    db_session.commit()

    # Observations on Day 1 and Day 5 (Days 2, 3, 4 have NO checkins)
    db_session.add(TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date="2026-09-10",
        status="done",
        start_delay_minutes=25,
    ))
    db_session.add(TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date="2026-09-14",
        status="done",
        start_delay_minutes=35,
    ))
    db_session.commit()

    calc = BehaviorMetricsCalculator(db_session, test_user.id)
    series = calc.compute_daily_behavior_series("start_delay")

    dates = [pt["date"] for pt in series]
    assert dates == ["2026-09-10", "2026-09-14"]
    assert "2026-09-11" not in dates
    assert "2026-09-12" not in dates
    assert "2026-09-13" not in dates


def test_api_behavior_patterns_and_summary_serialization(client, db_session, test_user):
    """
    Part 9 & 18:
    Ensures GET /api/v1/behavior/patterns and GET /api/v1/behavior/summary
    serialize all V2 pattern attributes and supporting metrics without schema failure.
    """
    task = Task(user_id=test_user.id, name="Work Task", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    for d in ["2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13", "2026-09-14"]:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=25,
        ))
    db_session.commit()

    # Test /api/v1/behavior/patterns
    resp_pat = client.get("/api/v1/behavior/patterns")
    assert resp_pat.status_code == 200
    pats = resp_pat.json()
    assert len(pats) >= 1
    p = pats[0]
    assert "id" in p
    assert "pattern_type" in p
    assert "status" in p
    assert "confidence" in p
    assert "supporting_metrics" in p
    assert "time_series" in p["supporting_metrics"]

    # Test /api/v1/behavior/summary
    resp_sum = client.get("/api/v1/behavior/summary")
    assert resp_sum.status_code == 200
    summary = resp_sum.json()
    assert "active_patterns" in summary
    assert len(summary["active_patterns"]) >= 1


def test_behavior_profile_freshness_after_new_checkin(client, db_session, test_user):
    """
    Part 17 & 18: Profile freshness fix.
    1. User has an existing profile (persisted snapshot).
    2. User records a new check-in.
    3. User requests/views the profile via GET /api/v1/behavior/profile.
    4. The profile reflects the newly recorded behavioral evidence.
    """
    # 1. User has existing profile with 0 completed sessions
    resp1 = client.get("/api/v1/behavior/profile")
    assert resp1.status_code == 200
    pdata1 = resp1.json()["profile_data"]
    assert pdata1["total_tasks_completed"] == 0

    # 2. User creates task and records a check-in
    task = Task(user_id=test_user.id, name="Daily Habit", planned_time="09:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    checkin_payload = {
        "task_id": task.id,
        "date": "2026-09-27",
        "status": "done",
        "duration_minutes": 45,
        "start_delay_minutes": 5,
    }
    resp_checkin = client.post("/api/v1/checkins", json=checkin_payload)
    assert resp_checkin.status_code in (200, 201)

    # 3. User requests/views profile
    resp2 = client.get("/api/v1/behavior/profile")
    assert resp2.status_code == 200
    pdata2 = resp2.json()["profile_data"]

    # 4. Profile reflects the newly recorded checkin!
    assert pdata2["total_tasks_completed"] == 1
    assert pdata2["task_completion_rate"] == 1.0
    assert pdata2["average_start_delay_minutes"] == 5.0


