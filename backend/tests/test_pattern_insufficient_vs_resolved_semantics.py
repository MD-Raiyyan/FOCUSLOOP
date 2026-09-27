import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.behavior import BehaviorPattern
from app.behavior.patterns import PatternDetector
from app.ai.context_builder import AIContextBuilder


def test_scenario_a_true_resolution(db_session, test_user):
    """
    SCENARIO A — TRUE RESOLUTION
    Historical: strong pattern (10 sessions, avg 40 min start delay)
    Recent: 5+ recent observations consistently contradicting the pattern (5 sessions, avg 6 min delay)
    Expected:
    - status = resolved
    - appropriate confidence (moderate/high)
    - appropriate explanation
    """
    task = Task(user_id=test_user.id, name="Writing Task", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 historical checkins (15 to 24 days ago) with 40 min delay
    for i in range(15, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))

    # 5 recent checkins (1 to 5 days ago) with 6 min prompt start
    for i in range(1, 6):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=6,
        ))
    db_session.commit()

    # Pre-existing active pattern in DB
    existing = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Historical hesitation",
        status="active",
        confidence="high",
        sample_size=10,
    )
    db_session.add(existing)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")

    assert pat.status == "resolved"
    assert pat.supporting_metrics["trend"] == "resolved"
    assert pat.supporting_metrics["lifecycle_category"] == "historical_resolved"
    assert "Resolved" in pat.title
    assert pat.confidence in ("moderate", "high")
    assert pat.sample_size == 15  # total lifetime evidence preserved


def test_scenario_b_zero_recent_evidence(db_session, test_user):
    """
    SCENARIO B — ZERO RECENT EVIDENCE
    Historical: strong pattern (10 sessions, avg 40 min start delay)
    Recent: 0 observations in the recent 7-day window
    Expected:
    - NOT resolved!
    - Expected semantic state: inactive / insufficient_current_evidence
    - Confidence must be 'low' (does NOT imply pattern was disproved)
    """
    task = Task(user_id=test_user.id, name="Project Work", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 historical checkins (15 to 24 days ago)
    for i in range(15, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))
    db_session.commit()

    # Pre-existing active pattern
    existing = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Historical hesitation",
        status="active",
        confidence="high",
        sample_size=10,
    )
    db_session.add(existing)
    db_session.commit()

    # Detect on ref_date where recent 7 days have 0 checkins
    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")

    # MUST NOT BE RESOLVED
    assert pat.status != "resolved"
    assert pat.status == "inactive"
    assert pat.supporting_metrics["trend"] == "inactive"
    assert pat.supporting_metrics["insufficient_current_evidence"] is True
    assert pat.supporting_metrics["lifecycle_category"] == "insufficient_current_evidence"
    assert "Inactive" in pat.title
    assert pat.confidence == "low"
    assert pat.sample_size == 10


def test_scenario_c_insufficient_recent_evidence(db_session, test_user):
    """
    SCENARIO C — INSUFFICIENT RECENT EVIDENCE
    Historical: strong pattern (10 sessions, avg 40 min start delay)
    Recent: 1–2 observations that look prompt (e.g. 5 min delay)
    Expected:
    - NOT resolved merely because 1–2 observations look better.
    - Current evidence remains insufficient to disprove an established habit.
    - Stays active (trend='stable') or inactive, NOT resolved.
    """
    task = Task(user_id=test_user.id, name="Coding Practice", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 historical checkins
    for i in range(15, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))

    # Only 1 recent prompt observation (2 days ago)
    d_recent = (ref_d - timedelta(days=2)).strftime("%Y-%m-%d")
    db_session.add(TaskCheckin(
        user_id=test_user.id,
        task_id=task.id,
        date=d_recent,
        status="done",
        start_delay_minutes=5,
    ))
    db_session.commit()

    existing = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Historical hesitation",
        status="active",
        confidence="high",
        sample_size=10,
    )
    db_session.add(existing)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")

    # MUST NOT BE RESOLVED
    assert pat.status != "resolved"
    assert pat.status != "improving"
    # Maintains stable active status because 1 observation is insufficient to claim improvement or resolution
    assert pat.status == "active"
    assert pat.supporting_metrics["trend"] == "stable"


def test_scenario_d_inactive_pattern_gets_new_evidence(db_session, test_user):
    """
    SCENARIO D — INACTIVE PATTERN GETS NEW EVIDENCE
    Historical: pattern existed, then had insufficient evidence -> inactive
    Current: User collects enough new observations supporting the pattern (4 sessions, avg 35 min delay)
    Expected:
    - Pattern is evaluated again normally and re-activates (status='active', trend='active')
    """
    task = Task(user_id=test_user.id, name="Daily Study", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 historical checkins
    for i in range(15, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))

    # 4 new recent checkins with significant delay (avg 35 min)
    for i in range(1, 5):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))
    db_session.commit()

    # Pre-existing pattern in DB was inactive
    existing = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Task Initiation Friction (Inactive)",
        description="Inactive pattern",
        status="inactive",
        confidence="low",
        sample_size=10,
        supporting_metrics={"trend": "inactive", "insufficient_current_evidence": True},
    )
    db_session.add(existing)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")

    # Inactive pattern successfully reactivates to active!
    assert pat.status == "active"
    assert pat.supporting_metrics["trend"] == "active"
    assert pat.supporting_metrics["lifecycle_category"] == "current_pattern"
    assert "Inactive" not in pat.title
    assert pat.sample_size == 14


def test_scenario_e_true_resolved_pattern_relapses(db_session, test_user):
    """
    SCENARIO E — TRUE RESOLVED PATTERN RELAPSES
    Pattern: previously resolved
    Current: sufficient recent evidence shows the original friction returning (4 sessions, avg 40 min delay)
    Expected:
    - relapse -> active
    """
    task = Task(user_id=test_user.id, name="Daily Study", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 historical checkins
    for i in range(15, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))

    # 4 recent checkins with severe delay
    for i in range(1, 5):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))
    db_session.commit()

    # Pre-existing pattern in DB was resolved
    existing = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Task Initiation Friction (Resolved)",
        description="Resolved pattern",
        status="resolved",
        confidence="moderate",
        sample_size=10,
        supporting_metrics={"trend": "resolved"},
    )
    db_session.add(existing)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")

    # Relapse back to active!
    assert pat.status == "active"
    assert pat.supporting_metrics["trend"] == "relapse"
    assert pat.supporting_metrics["lifecycle_category"] == "current_pattern"


def test_ai_context_current_inactive_resolved_separation(db_session, test_user):
    """
    Verifies that AIContextBuilder cleanly separates:
    - current_patterns (active, improving, weakening)
    - inactive_patterns (insufficient current evidence)
    - resolved_patterns (sufficient recent resolution evidence)
    And provides honest guidance so AI never falsely claims resolution.
    """
    # 1. Active pattern
    p_active = BehaviorPattern(
        id="00000000-0000-0000-0000-000000000001",
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="Active slump",
        status="active",
        confidence="moderate",
        sample_size=6,
        supporting_metrics={"trend": "active", "recent_window": {"value": 30.0}},
    )
    # 2. Inactive pattern
    p_inactive = BehaviorPattern(
        id="00000000-0000-0000-0000-000000000002",
        user_id=test_user.id,
        pattern_type="primary_distraction",
        title="Frequent Transition to YouTube (Inactive)",
        description="Inactive distraction",
        status="inactive",
        confidence="low",
        sample_size=12,
        supporting_metrics={"trend": "inactive", "insufficient_current_evidence": True},
    )
    # 3. Resolved pattern
    p_resolved = BehaviorPattern(
        id="00000000-0000-0000-0000-000000000003",
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Task Initiation Friction (Resolved)",
        description="Resolved friction",
        status="resolved",
        confidence="moderate",
        sample_size=15,
        supporting_metrics={"trend": "resolved"},
    )
    db_session.add_all([p_active, p_inactive, p_resolved])
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="What patterns do you notice in my habits?")

    # 1. Check current patterns
    assert len(ctx.current_patterns) == 1
    assert ctx.current_patterns[0]["id"] == p_active.id
    assert ctx.current_patterns[0]["is_current"] is True
    assert ctx.current_patterns[0]["lifecycle_category"] == "current_pattern"

    # 2. Check inactive patterns
    assert len(ctx.inactive_patterns) == 1
    assert ctx.inactive_patterns[0]["id"] == p_inactive.id
    assert ctx.inactive_patterns[0]["is_current"] is False
    assert ctx.inactive_patterns[0]["lifecycle_category"] == "insufficient_current_evidence"
    assert "INSUFFICIENT CURRENT EVIDENCE" in ctx.inactive_patterns[0]["explanation_guidance"]
    assert "You must NOT say this pattern was resolved" in ctx.inactive_patterns[0]["explanation_guidance"]

    # 3. Check resolved patterns
    assert len(ctx.resolved_patterns) == 1
    assert ctx.resolved_patterns[0]["id"] == p_resolved.id
    assert ctx.resolved_patterns[0]["is_current"] is False
    assert ctx.resolved_patterns[0]["lifecycle_category"] == "historical_resolved"
    assert "HISTORICAL / RESOLVED" in ctx.resolved_patterns[0]["explanation_guidance"]


def test_api_serialization_and_idempotency(client, db_session, test_user):
    """
    Verifies that:
    1. GET /api/v1/behavior/patterns serializes inactive patterns cleanly with correct JSON schema
    2. GET /api/v1/behavior/summary correctly includes active patterns without crashing on inactive/resolved
    3. Repeated calls are completely idempotent and do not create duplicate rows
    """
    task = Task(user_id=test_user.id, name="Evening Coding", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 old checkins (> 10 days ago) -> will produce inactive afternoon_slump and start_delay_resistance
    for i in range(12, 22):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))
    db_session.commit()

    # Pre-seed existing pattern
    pat = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="Historical slump",
        status="active",
        confidence="high",
        sample_size=10,
    )
    db_session.add(pat)
    db_session.commit()

    # 1. GET /patterns
    resp = client.get("/api/v1/behavior/patterns")
    assert resp.status_code == 200
    patterns = resp.json()
    assert isinstance(patterns, list)
    p_slump = next(p for p in patterns if p["pattern_type"] == "afternoon_slump")
    assert p_slump["status"] == "inactive"
    assert p_slump["supporting_metrics"]["lifecycle_category"] == "insufficient_current_evidence"
    assert p_slump["supporting_metrics"]["insufficient_current_evidence"] is True

    # 2. Idempotency: repeated GET /patterns
    resp2 = client.get("/api/v1/behavior/patterns")
    assert resp2.status_code == 200
    patterns2 = resp2.json()
    assert len(patterns) == len(patterns2)

    db_count = db_session.query(BehaviorPattern).filter(BehaviorPattern.user_id == test_user.id).count()
    assert db_count == len(patterns)

    # 3. GET /summary
    resp_sum = client.get("/api/v1/behavior/summary")
    assert resp_sum.status_code == 200
    summary = resp_sum.json()
    assert "completion_rate" in summary
    assert "active_patterns" in summary
