import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.screen_usage import ScreenUsage
from app.models.behavior import BehaviorPattern
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.patterns import PatternDetector


def test_confidence_not_inflated_by_old_data_scenario_a_and_b(db_session, test_user):
    """
    Part 2 & 3:
    Scenario A: 30 old high-friction observations + 5 recent contradictory (low-friction) observations.
    - raw sample_size preserves total historical volume (35)
    - historical_window sample_size = 30
    - recent_window sample_size = 5
    - status transitions to 'improving'
    - CURRENT confidence must NOT be 'high' merely because lifetime sample_size is 35!
    """
    task = Task(user_id=test_user.id, name="Daily Writing", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"

    # 30 old observations (15 to 44 days ago): high delay of 40 mins
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()
    for i in range(15, 45):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=40,
        ))

    # 5 recent contradictory observations (1 to 5 days ago): prompt delay of only 8 mins
    recent_dates = [(ref_d - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 6)]
    for d_str in recent_dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=8,
        ))
    db_session.commit()

    # Pre-existing active pattern in DB
    existing_pat = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Historical friction",
        status="active",
        confidence="high",
        sample_size=30,
    )
    db_session.add(existing_pat)
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()

    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")
    sup = pat.supporting_metrics

    # Verify sample sizes
    assert pat.sample_size == 35  # Lifetime raw sample size preserved
    assert sup["historical_window"]["sample_size"] == 30
    assert sup["recent_window"]["sample_size"] == 5
    assert sup["effective_recent_sample_size"] == 5

    # Verify status transitioned to resolved or improving (not active!)
    assert pat.status in ("improving", "resolved")
    assert sup["contradiction_detected"] is True

    # CRITICAL: Confidence is NOT 'high'! It is 'moderate' based on 5 recent observations
    assert pat.confidence != "high"
    assert pat.confidence == "moderate"

    # Scenario B: same 5 recent prompt observations + no old observations
    user_b = User(
        id="00000000-0000-0000-0000-000000000099",
        name="User B",
        email="b@test.local",
        username="user_b",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    task_b = Task(user_id=user_b.id, name="Daily Writing B", planned_time="14:00", frequency="daily")
    db_session.add(task_b)
    db_session.commit()
    for d_str in recent_dates:
        db_session.add(TaskCheckin(
            user_id=user_b.id,
            task_id=task_b.id,
            date=d_str,
            status="done",
            start_delay_minutes=8,
        ))
    db_session.commit()
    detector_b = PatternDetector(db_session, user_b.id, ref_date=ref_date)
    pats_b = detector_b.detect_and_update_patterns()
    # 5 prompt sessions without historical friction should never trigger start delay resistance!
    delay_b = next((p for p in pats_b if p.pattern_type == "start_delay_resistance"), None)
    assert delay_b is None


def test_substantial_consistent_evidence_achieves_high_confidence(db_session, test_user):
    """
    Part 3:
    Verifies that when BOTH:
    - historical evidence is substantial (e.g. 20 observations across 10 days)
    - recent evidence is also substantial and consistent (e.g. 5 observations across 3+ days)
    HIGH confidence is correctly produced.
    """
    task = Task(user_id=test_user.id, name="Afternoon Work", planned_time="14:00", frequency="daily")
    morn_task = Task(user_id=test_user.id, name="Morning Prep", planned_time="09:00", frequency="daily")
    db_session.add_all([task, morn_task])
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 15 historical afternoon sessions with high delay (35 mins)
    for i in range(10, 25):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))

    # 5 recent afternoon sessions with consistently high delay (35 mins) across 5 distinct days
    for i in range(1, 6):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()

    pat = next(p for p in patterns if p.pattern_type == "start_delay_resistance")
    assert pat.status == "active"
    assert pat.sample_size == 20
    assert pat.confidence == "high"


def test_morning_momentum_v2_full_lifecycle(db_session, test_user):
    """
    Part 4: Morning Momentum V2:
    1. Sufficient evidence -> active positive pattern.
    2. Repeated recent underperformance -> weakens.
    3. Sustained poor morning completion -> resolves / inactive.
    4. Return of strong morning execution -> recovers to active.
    """
    morn_task = Task(user_id=test_user.id, name="Morning Focus", planned_time="08:30", frequency="daily")
    db_session.add(morn_task)
    db_session.commit()

    ref_d = datetime.strptime("2026-09-30", "%Y-%m-%d").date()

    # Step 1: 8 historical morning tasks with 100% completion rate (8 done)
    for i in range(10, 18):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=morn_task.id,
            date=d_str,
            status="done",
            duration_minutes=30,
        ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-30")
    patterns = detector.detect_and_update_patterns()

    pat = next(p for p in patterns if p.pattern_type == "morning_momentum")
    assert pat.status == "active"
    assert "Morning Clarity Window" in pat.title
    assert pat.supporting_metrics["time_series"] is not None

    # Step 2: Recent window experiences 3 morning sessions with low completion (1 done, 2 missed)
    for i, st in enumerate(["missed", "missed", "done"]):
        d_str = (ref_d - timedelta(days=i + 1)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=morn_task.id,
            date=d_str,
            status=st,
            duration_minutes=10 if st == "done" else 0,
        ))
    db_session.commit()

    detector2 = PatternDetector(db_session, test_user.id, ref_date="2026-09-30")
    patterns2 = detector2.detect_and_update_patterns()
    pat2 = next(p for p in patterns2 if p.pattern_type == "morning_momentum")

    # Positive pattern weakens!
    assert pat2.status == "weakening"
    assert pat2.supporting_metrics["trend"] == "weakening"
    assert "Weakening" in pat2.title

    # Step 3: Sustained decline (add 2 more missed morning tasks -> 5 recent tasks, 1 done, 4 missed = 20%)
    for i in [4, 5]:
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=morn_task.id,
            date=d_str,
            status="missed",
        ))
    db_session.commit()

    detector3 = PatternDetector(db_session, test_user.id, ref_date="2026-09-30")
    patterns3 = detector3.detect_and_update_patterns()
    pat3 = next(p for p in patterns3 if p.pattern_type == "morning_momentum")

    # Positive pattern resolves / is no longer active
    assert pat3.status == "resolved"
    assert pat3.supporting_metrics["trend"] == "resolved"
    assert "Resolved" in pat3.title

    # Step 4: Recovery! In a new week, user logs 4 consecutive successful morning tasks (100% completion)
    new_ref = "2026-10-10"
    new_ref_d = datetime.strptime(new_ref, "%Y-%m-%d").date()
    for i in range(1, 5):
        d_str = (new_ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=morn_task.id,
            date=d_str,
            status="done",
            duration_minutes=35,
        ))
    db_session.commit()

    detector4 = PatternDetector(db_session, test_user.id, ref_date=new_ref)
    patterns4 = detector4.detect_and_update_patterns()
    pat4 = next(p for p in patterns4 if p.pattern_type == "morning_momentum")

    # Recovers back to active!
    assert pat4.status == "active"
    assert pat4.supporting_metrics["trend"] == "recovery"


def test_primary_distraction_v2_recency_and_graph(db_session, test_user):
    """
    Part 5 & 6: Primary Distraction V2:
    - Recency awareness: historical distraction vs recent window
    - Real time-series graph with actual dates and durations
    - State transitions: active -> improving / resolved -> relapse
    """
    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 1. Historical distraction (12 days ago): 3 sessions of Instagram totalling 90 minutes
    hist_d = (ref_d - timedelta(days=12)).strftime("%Y-%m-%d")
    for _ in range(3):
        db_session.add(ScreenUsage(
            user_id=test_user.id,
            app_identifier="com.instagram.android",
            app_name="Instagram",
            started_at=datetime.strptime(hist_d + " 14:00:00", "%Y-%m-%d %H:%M:%S"),
            ended_at=datetime.strptime(hist_d + " 14:30:00", "%Y-%m-%d %H:%M:%S"),
            duration_seconds=1800,  # 30 min each
        ))
    db_session.commit()

    detector1 = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns1 = detector1.detect_and_update_patterns()
    pat1 = next(p for p in patterns1 if p.pattern_type == "primary_distraction")

    # Time series contains real points
    time_series = pat1.supporting_metrics["time_series"]
    assert len(time_series) == 1
    assert time_series[0]["date"] == hist_d
    assert time_series[0]["value"] == 90.0
    assert time_series[0]["sample_size"] == 3

    # 2. Recent usage drops to zero/near-zero: Pattern recognizes historical vs recent
    # With zero usage in the last 7 days, it transitions to inactive (insufficient current evidence)
    assert pat1.status in ("inactive", "resolved", "improving")
    assert pat1.status == "inactive"
    assert pat1.supporting_metrics["historical_window"]["value"] == 90.0

    # 3. Relapse: Recent high distraction resurfaces (3 sessions, 60 minutes in recent window)
    rec_d1 = (ref_d - timedelta(days=2)).strftime("%Y-%m-%d")
    rec_d2 = (ref_d - timedelta(days=1)).strftime("%Y-%m-%d")

    db_session.add(ScreenUsage(
        user_id=test_user.id,
        app_identifier="com.instagram.android",
        app_name="Instagram",
        started_at=datetime.strptime(rec_d1 + " 15:00:00", "%Y-%m-%d %H:%M:%S"),
        ended_at=datetime.strptime(rec_d1 + " 15:20:00", "%Y-%m-%d %H:%M:%S"),
        duration_seconds=1200,  # 20 min
    ))
    db_session.add(ScreenUsage(
        user_id=test_user.id,
        app_identifier="com.instagram.android",
        app_name="Instagram",
        started_at=datetime.strptime(rec_d2 + " 16:00:00", "%Y-%m-%d %H:%M:%S"),
        ended_at=datetime.strptime(rec_d2 + " 16:40:00", "%Y-%m-%d %H:%M:%S"),
        duration_seconds=2400,  # 40 min
    ))
    db_session.add(ScreenUsage(
        user_id=test_user.id,
        app_identifier="com.instagram.android",
        app_name="Instagram",
        started_at=datetime.strptime(rec_d2 + " 17:00:00", "%Y-%m-%d %H:%M:%S"),
        ended_at=datetime.strptime(rec_d2 + " 17:15:00", "%Y-%m-%d %H:%M:%S"),
        duration_seconds=900,  # 15 min
    ))
    db_session.commit()

    detector2 = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns2 = detector2.detect_and_update_patterns()
    pat2 = next(p for p in patterns2 if p.pattern_type == "primary_distraction")

    # Relapse back to active!
    assert pat2.status == "active"
    assert pat2.supporting_metrics["trend"] == "relapse"
    assert len(pat2.supporting_metrics["time_series"]) == 3
    assert pat2.supporting_metrics["recent_window"]["value"] == 75.0


def test_primary_distraction_scenario_e_reduction_to_improving(db_session, test_user):
    """
    Part 5 & 16 (Scenario E):
    Historical: Social app = 120 min/week across 4 sessions
    Recent: Social app = 8 min/week
    Expected:
    - historical evidence preserved (120 min)
    - current distraction recognizes reduction and transitions to 'improving'
    - title reflects improving status
    """
    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 1. Pre-existing active pattern in DB
    existing_pat = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="primary_distraction",
        title="Frequent Transition to YouTube",
        description="Historical distraction",
        status="active",
        confidence="high",
        sample_size=4,
        supporting_metrics={"primary_app": {"app_name": "YouTube"}},
    )
    db_session.add(existing_pat)

    # 2. Historical: 4 sessions of YouTube totalling 120 minutes (30 min each, 12 days ago)
    hist_d = (ref_d - timedelta(days=12)).strftime("%Y-%m-%d")
    for _ in range(4):
        db_session.add(ScreenUsage(
            user_id=test_user.id,
            app_identifier="com.google.android.youtube",
            app_name="YouTube",
            started_at=datetime.strptime(hist_d + " 15:00:00", "%Y-%m-%d %H:%M:%S"),
            ended_at=datetime.strptime(hist_d + " 15:30:00", "%Y-%m-%d %H:%M:%S"),
            duration_seconds=1800,  # 30 min each
        ))

    # 3. Recent: 1 session of YouTube for only 8 minutes (2 days ago)
    rec_d = (ref_d - timedelta(days=2)).strftime("%Y-%m-%d")
    db_session.add(ScreenUsage(
        user_id=test_user.id,
        app_identifier="com.google.android.youtube",
        app_name="YouTube",
        started_at=datetime.strptime(rec_d + " 16:00:00", "%Y-%m-%d %H:%M:%S"),
        ended_at=datetime.strptime(rec_d + " 16:08:00", "%Y-%m-%d %H:%M:%S"),
        duration_seconds=480,  # 8 min
    ))
    db_session.commit()

    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()
    pat = next(p for p in patterns if p.pattern_type == "primary_distraction")

    # Historical evidence preserved
    assert pat.supporting_metrics["historical_window"]["value"] == 120.0
    assert pat.supporting_metrics["recent_window"]["value"] == 8.0

    # Current distraction transitions to 'improving'
    assert pat.status == "improving"
    assert pat.supporting_metrics["trend"] == "improving"
    assert "Improving" in pat.title


def test_existing_pattern_insufficient_current_evidence_handling(db_session, test_user):
    """
    Part 8:
    A pattern was previously detected and stored as active.
    The user later has 0 or insufficient current evidence in the recent 7-day window.
    The old pattern must NOT blindly remain active forever.
    It transitions to 'resolved' (trend='inactive') with low confidence,
    while preserving historical rows and sample_size.
    """
    task = Task(user_id=test_user.id, name="Old Project", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    ref_date = "2026-09-30"
    ref_d = datetime.strptime(ref_date, "%Y-%m-%d").date()

    # 10 old checkins from 20 days ago (all > 7 days ago)
    for i in range(20, 30):
        d_str = (ref_d - timedelta(days=i)).strftime("%Y-%m-%d")
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d_str,
            status="done",
            start_delay_minutes=35,
        ))
    db_session.commit()

    # Pre-existing active row in database
    existing_pattern = BehaviorPattern(
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="Active slump",
        status="active",
        confidence="high",
        sample_size=10,
    )
    db_session.add(existing_pattern)
    db_session.commit()

    # Run detection on ref_date where recent 7 days have ZERO afternoon tasks
    detector = PatternDetector(db_session, test_user.id, ref_date=ref_date)
    patterns = detector.detect_and_update_patterns()

    pat = next(p for p in patterns if p.pattern_type == "afternoon_slump")

    # Must NOT remain blindly active, and must NOT be marked resolved without evidence!
    assert pat.status == "inactive"
    assert pat.supporting_metrics["trend"] == "inactive"
    assert pat.supporting_metrics["insufficient_current_evidence"] is True
    assert pat.supporting_metrics["lifecycle_category"] == "insufficient_current_evidence"
    assert "Inactive" in pat.title
    assert pat.confidence == "low"
    assert pat.sample_size == 10  # Historical sample size preserved


def test_http_api_endpoints_full_e2e_integration(client, db_session, test_user):
    """
    Part 10 & 11:
    Exercises the complete HTTP API chain:
    HTTP Client -> FastAPI route -> Auth Dependency -> SQLAlchemy session
    -> PatternDetector & BehaviorMetrics -> Serialization -> JSON Response
    Verifies:
    1. GET /api/v1/behavior/patterns
    2. GET /api/v1/behavior/summary
    3. GET /api/v1/behavior/profile
    4. Repeated request idempotency (no duplicate pattern rows)
    """
    task = Task(user_id=test_user.id, name="Daily Coding", planned_time="14:00", frequency="daily")
    db_session.add(task)
    db_session.commit()

    dates = ["2026-09-24", "2026-09-25", "2026-09-26", "2026-09-27", "2026-09-28"]
    for d in dates:
        db_session.add(TaskCheckin(
            user_id=test_user.id,
            task_id=task.id,
            date=d,
            status="done",
            start_delay_minutes=30,
        ))
    db_session.commit()

    # 1. GET /api/v1/behavior/patterns
    resp_pat = client.get("/api/v1/behavior/patterns")
    assert resp_pat.status_code == 200
    pats = resp_pat.json()
    assert isinstance(pats, list)
    assert len(pats) >= 1
    p0 = pats[0]
    assert "id" in p0
    assert "pattern_type" in p0
    assert "title" in p0
    assert "description" in p0
    assert "status" in p0
    assert "confidence" in p0
    assert "supporting_metrics" in p0
    sup = p0["supporting_metrics"]
    assert "time_series" in sup
    assert "context_comparison" in sup

    # 2. Repeated request idempotency check: calling /patterns again should not duplicate rows
    resp_pat2 = client.get("/api/v1/behavior/patterns")
    assert resp_pat2.status_code == 200
    pats2 = resp_pat2.json()
    assert len(pats2) == len(pats)
    pattern_count = db_session.query(BehaviorPattern).filter(BehaviorPattern.user_id == test_user.id).count()
    assert pattern_count == len(pats)

    # 3. GET /api/v1/behavior/summary
    resp_sum = client.get("/api/v1/behavior/summary")
    assert resp_sum.status_code == 200
    summary = resp_sum.json()
    assert "completion_rate" in summary
    assert "average_start_delay_minutes" in summary
    assert "active_patterns" in summary
    assert "profile" in summary
    assert summary["total_tasks_tracked"] == 5

    # 4. GET /api/v1/behavior/profile
    resp_prof = client.get("/api/v1/behavior/profile")
    assert resp_prof.status_code == 200
    prof = resp_prof.json()
    assert "user_id" in prof
    assert prof["user_id"] == test_user.id
    assert "profile_data" in prof
    assert prof["profile_data"]["total_tasks_completed"] == 5
