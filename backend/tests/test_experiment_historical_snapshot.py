import uuid
from datetime import datetime
import pytest
from app.models.user import User
from app.models.behavior import BehaviorPattern
from app.models.experiment import Experiment, ExperimentResult
from app.behavior.snapshot import build_pattern_snapshot
from app.behavior.patterns import PatternDetector


def test_experiment_creation_stores_pattern_id_and_snapshot(db_session, test_user):
    """
    Contract Requirements 1, 2, 3:
    1. Experiment creation stores pattern_id.
    2. Experiment creation stores an immutable pattern snapshot.
    3. Snapshot contains expected creation-time pattern state:
       - pattern_id, pattern_type, pattern_title, pattern_description,
         confidence, sample_size, status, first_detected, last_detected,
         decision-relevant supporting_metrics, snapshot_created_at.
    """
    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="Start delay peaks between 1 PM and 4 PM",
        confidence="high",
        sample_size=12,
        status="active",
        first_detected=datetime(2026, 9, 10, 10, 0, 0),
        last_detected=datetime(2026, 9, 20, 15, 30, 0),
        supporting_metrics={
            "metric_name": "average_start_delay_minutes",
            "unit": "min",
            "historical_window": {"value": 35.0, "sample_size": 8},
            "recent_window": {"value": 28.0, "sample_size": 4},
            "context_comparison": {"morning_delay": 5.0, "afternoon_delay": 30.0},
            "distinct_days": 6,
            "recent_distinct_days": 3,
            "first_observed_date": "2026-09-10",
            "last_observed_date": "2026-09-20",
            "trend": "active",
        },
    )
    db_session.add(pattern)
    db_session.commit()

    snapshot = build_pattern_snapshot(pattern)
    assert snapshot["pattern_id"] == pattern.id
    assert snapshot["pattern_type"] == "afternoon_slump"
    assert snapshot["pattern_title"] == "Afternoon Focus Friction"
    assert snapshot["confidence"] == "high"
    assert snapshot["sample_size"] == 12
    assert snapshot["status"] == "active"
    assert snapshot["first_detected"] == "2026-09-10T10:00:00"
    assert snapshot["last_detected"] == "2026-09-20T15:30:00"
    assert snapshot["supporting_metrics"]["metric_name"] == "average_start_delay_minutes"
    assert snapshot["supporting_metrics"]["historical_window"]["value"] == 35.0
    assert "snapshot_created_at" in snapshot

    # Create experiment referencing pattern_id and storing snapshot
    exp = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=pattern.id,
        pattern_snapshot=snapshot,
        title="Afternoon Micro-Commitment",
        description="Shift demanding tasks before 12 PM",
        hypothesis="Earlier scheduling will cut afternoon start delay",
        start_date="2026-09-21",
        end_date="2026-09-28",
        target_metric="average_start_delay_minutes",
        baseline_value=30.0,
        target_value=15.0,
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    persisted_exp = db_session.query(Experiment).filter(Experiment.id == exp.id).first()
    assert persisted_exp.pattern_id == pattern.id
    assert persisted_exp.pattern_snapshot is not None
    assert persisted_exp.pattern_snapshot["pattern_id"] == pattern.id
    assert persisted_exp.pattern_snapshot["status"] == "active"
    assert persisted_exp.pattern_snapshot["confidence"] == "high"


def test_snapshot_remains_immutable_when_pattern_changes(db_session, test_user):
    """
    Contract Requirements 4, 5:
    4. When pattern status later changes (e.g., active -> resolved),
       the historical experiment snapshot MUST NOT change.
    5. When pattern confidence or sample_size changes,
       the historical experiment snapshot MUST NOT change.
    """
    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="start_delay_resistance",
        title="Initial Task Initiation Friction",
        description="Hesitation observed",
        confidence="moderate",
        sample_size=6,
        status="active",
        first_detected=datetime(2026, 9, 1, 9, 0, 0),
        last_detected=datetime(2026, 9, 10, 14, 0, 0),
        supporting_metrics={"last_observed_date": "2026-09-10", "sample_size": 6},
    )
    db_session.add(pattern)
    db_session.commit()

    # Create Experiment 1 at creation time
    exp1 = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=pattern.id,
        pattern_snapshot=build_pattern_snapshot(pattern),
        title="5-Minute Rule Intervention",
        description="Start immediately for 5 minutes",
        hypothesis="Lower initiation threshold reduces start delay",
        start_date="2026-09-11",
        end_date="2026-09-18",
        target_metric="average_start_delay_minutes",
        status="active",
    )
    db_session.add(exp1)
    db_session.commit()

    # Later: Pattern evolves significantly: status -> resolved, confidence -> high, sample_size -> 20
    pattern.status = "resolved"
    pattern.confidence = "high"
    pattern.sample_size = 20
    pattern.last_detected = datetime(2026, 9, 25, 17, 0, 0)
    pattern.supporting_metrics = {"status": "resolved", "sample_size": 20, "last_observed_date": "2026-09-25"}
    db_session.commit()

    # Exp1's snapshot MUST still retain its original creation context!
    refetched_exp1 = db_session.query(Experiment).filter(Experiment.id == exp1.id).first()
    assert refetched_exp1.pattern_snapshot["status"] == "active"
    assert refetched_exp1.pattern_snapshot["confidence"] == "moderate"
    assert refetched_exp1.pattern_snapshot["sample_size"] == 6
    assert refetched_exp1.pattern_snapshot["last_detected"] == "2026-09-10T14:00:00"

    # But the live pattern shows current evolved state
    live_pat = db_session.query(BehaviorPattern).filter(BehaviorPattern.id == pattern.id).first()
    assert live_pat.status == "resolved"
    assert live_pat.confidence == "high"
    assert live_pat.sample_size == 20


def test_pattern_reactivation_preserves_old_experiment_and_creates_distinct_new_snapshot(db_session, test_user):
    """
    Contract Requirements 6, 7, 8:
    6. Pattern later reactivates: old experiment remains unchanged.
    7. A new future experiment gets a new snapshot reflecting reactivation context.
    8. Multiple experiments can reference the same pattern_id.
    """
    detector = PatternDetector(db_session, test_user.id)

    # 1. Pattern initially active
    p = detector._upsert_pattern(
        pattern_type="morning_momentum",
        title="Morning Focus Momentum",
        description="High morning velocity",
        confidence="high",
        sample_size=10,
        status="active",
        supporting_metrics={"status": "active", "sample_size": 10, "last_observed_date": "2026-09-01"},
    )
    db_session.commit()
    stable_pattern_id = p.id

    # Experiment 1 created during initial active phase
    exp1 = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=stable_pattern_id,
        pattern_snapshot=build_pattern_snapshot(p),
        title="Experiment 1 - Morning Anchor",
        description="First intervention",
        hypothesis="Hypothesis 1",
        start_date="2026-09-02",
        target_metric="completion_rate",
        status="completed",
    )
    db_session.add(exp1)
    db_session.commit()

    # 2. Pattern later resolves
    p_res = detector._upsert_pattern(
        pattern_type="morning_momentum",
        title="Morning Focus Momentum (Resolved)",
        description="Clarity resolved",
        confidence="high",
        sample_size=20,
        status="resolved",
        supporting_metrics={"status": "resolved", "sample_size": 20, "last_observed_date": "2026-09-15"},
    )
    db_session.commit()
    assert p_res.id == stable_pattern_id

    # 3. Pattern later relapses / reactivates with new evidence
    p_reactivated = detector._upsert_pattern(
        pattern_type="morning_momentum",
        title="Morning Focus Momentum",
        description="Friction returned",
        confidence="moderate",
        sample_size=25,
        status="active",
        supporting_metrics={"status": "active", "sample_size": 25, "last_observed_date": "2026-09-25"},
    )
    db_session.commit()
    assert p_reactivated.id == stable_pattern_id

    # Experiment 2 created during reactivation phase
    exp2 = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=stable_pattern_id,
        pattern_snapshot=build_pattern_snapshot(p_reactivated),
        title="Experiment 2 - Reactivation Recheck",
        description="Second intervention",
        hypothesis="Hypothesis 2",
        start_date="2026-09-26",
        target_metric="completion_rate",
        status="active",
    )
    db_session.add(exp2)
    db_session.commit()

    # Check both experiments from database
    e1 = db_session.query(Experiment).filter(Experiment.id == exp1.id).first()
    e2 = db_session.query(Experiment).filter(Experiment.id == exp2.id).first()

    # Both reference the SAME stable pattern_id
    assert e1.pattern_id == stable_pattern_id
    assert e2.pattern_id == stable_pattern_id

    # Experiment 1 still has its original creation-time snapshot (status=active, sample_size=10)
    assert e1.pattern_snapshot["status"] == "active"
    assert e1.pattern_snapshot["sample_size"] == 10
    assert e1.pattern_snapshot["supporting_metrics"]["last_observed_date"] == "2026-09-01"

    # Experiment 2 has its own creation-time snapshot (status=active, sample_size=25)
    assert e2.pattern_snapshot["status"] == "active"
    assert e2.pattern_snapshot["sample_size"] == 25
    assert e2.pattern_snapshot["supporting_metrics"]["last_observed_date"] == "2026-09-25"


def test_historical_experiments_with_null_pattern_id_remain_intact(db_session, test_user):
    """
    Contract Requirement 9:
    Existing historical experiments with NULL pattern_id remain intact, queryable,
    and can have evaluation results.
    """
    exp_null = Experiment(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_id=None,
        pattern_snapshot=None,
        title="Legacy Experiment Without Pattern Link",
        description="Legacy intervention",
        hypothesis="Legacy hypothesis",
        start_date="2026-08-01",
        end_date="2026-08-15",
        target_metric="start_delay_minutes",
        status="completed",
    )
    db_session.add(exp_null)
    db_session.commit()

    res = ExperimentResult(
        id=str(uuid.uuid4()),
        experiment_id=exp_null.id,
        metric_name="start_delay_minutes",
        before_value=30.0,
        after_value=20.0,
        change_value=-10.0,
        percent_change=-33.3,
        conclusion="positive",
        result_summary="Legacy experiment completed successfully.",
    )
    db_session.add(res)
    db_session.commit()

    fetched = db_session.query(Experiment).filter(Experiment.id == exp_null.id).first()
    assert fetched is not None
    assert fetched.pattern_id is None
    assert fetched.pattern_snapshot is None
    assert len(fetched.results) == 1
    assert fetched.results[0].conclusion == "positive"


def test_http_api_experiment_creation_captures_pattern_snapshot(client, db_session, test_user):
    """
    Contract Requirement 10:
    Verifies HTTP POST /api/v1/experiments automatically captures pattern_snapshot
    from the referenced pattern_id and returns it in GET /api/v1/experiments.
    """
    # 1. Create a pattern in DB for test_user
    pattern = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="primary_distraction",
        title="Frequent Social Media Loop",
        description="Distraction loops after difficult tasks",
        confidence="high",
        sample_size=9,
        status="active",
        first_detected=datetime(2026, 9, 15, 10, 0, 0),
        last_detected=datetime(2026, 9, 22, 14, 0, 0),
        supporting_metrics={
            "metric_name": "screen_time_minutes",
            "unit": "min",
            "sample_size": 9,
            "last_observed_date": "2026-09-22",
            "trend": "active",
        },
    )
    db_session.add(pattern)
    db_session.commit()

    # 2. HTTP POST /api/v1/experiments with pattern_id
    payload = {
        "title": "Social App Lock Challenge",
        "description": "Block social apps during morning focus",
        "hypothesis": "Blocking distraction will increase completed focus blocks",
        "intervention_type": "app_lock",
        "start_date": "2026-09-23",
        "end_date": "2026-09-30",
        "target_metric": "completion_rate",
        "baseline_value": 0.5,
        "target_value": 0.8,
        "pattern_id": pattern.id,
    }
    post_res = client.post("/api/v1/experiments", json=payload)
    assert post_res.status_code == 201
    created_data = post_res.json()

    assert created_data["pattern_id"] == pattern.id
    assert created_data["pattern_snapshot"] is not None
    assert created_data["pattern_snapshot"]["pattern_id"] == pattern.id
    assert created_data["pattern_snapshot"]["pattern_type"] == "primary_distraction"
    assert created_data["pattern_snapshot"]["status"] == "active"
    assert created_data["pattern_snapshot"]["confidence"] == "high"

    # 3. HTTP GET /api/v1/experiments
    get_res = client.get("/api/v1/experiments")
    assert get_res.status_code == 200
    exps = get_res.json()
    matched = next((e for e in exps if e["id"] == created_data["id"]), None)
    assert matched is not None
    assert matched["pattern_id"] == pattern.id
    assert matched["pattern_snapshot"]["pattern_title"] == "Frequent Social Media Loop"
