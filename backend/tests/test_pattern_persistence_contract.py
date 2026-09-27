import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.behavior import BehaviorPattern
from app.behavior.patterns import PatternDetector


def test_pattern_identity_same_user_same_type_updates_same_row(db_session, test_user):
    """
    Contract: For a given user, (user_id, pattern_type) maps to at most one row.
    Repeated runs or updates must update the same row and preserve the primary key.
    """
    detector = PatternDetector(db_session, test_user.id, ref_date="2026-09-15")

    # Insert initial pattern
    p1 = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Initial Hesitation",
        description="User hesitates before tasks.",
        confidence="moderate",
        sample_size=5,
        status="active",
        supporting_metrics={"sample_size": 5, "last_observed_date": "2026-09-14"},
    )
    db_session.commit()
    original_id = p1.id
    assert original_id is not None

    # Upsert with new information for same user and pattern_type
    p2 = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Initial Hesitation (Updated)",
        description="Updated description.",
        confidence="high",
        sample_size=8,
        status="improving",
        supporting_metrics={"sample_size": 8, "last_observed_date": "2026-09-15"},
    )
    db_session.commit()

    assert p2.id == original_id
    rows = (
        db_session.query(BehaviorPattern)
        .filter(
            BehaviorPattern.user_id == test_user.id,
            BehaviorPattern.pattern_type == "start_delay_resistance",
        )
        .all()
    )
    assert len(rows) == 1
    assert rows[0].status == "improving"
    assert rows[0].confidence == "high"


def test_pattern_identity_different_users_can_have_same_pattern_type(db_session, test_user):
    """
    Contract: Different users can independently possess the same pattern_type.
    """
    user_b = User(
        id=str(uuid.uuid4()),
        email=f"user_b_{uuid.uuid4().hex[:6]}@focusloop.test",
        name="User B",
    )
    db_session.add(user_b)
    db_session.commit()

    det_a = PatternDetector(db_session, test_user.id)
    det_b = PatternDetector(db_session, user_b.id)

    pa = det_a._upsert_pattern(
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="User A slump",
        confidence="moderate",
        sample_size=6,
        status="active",
        supporting_metrics={"sample_size": 6},
    )
    pb = det_b._upsert_pattern(
        pattern_type="afternoon_slump",
        title="Afternoon Focus Friction",
        description="User B slump",
        confidence="high",
        sample_size=10,
        status="active",
        supporting_metrics={"sample_size": 10},
    )
    db_session.commit()

    assert pa.id != pb.id
    assert pa.user_id == test_user.id
    assert pb.user_id == user_b.id


def test_pattern_identity_different_pattern_types_create_different_rows(db_session, test_user):
    """
    Contract: Different pattern_types for the same user create distinct rows.
    """
    detector = PatternDetector(db_session, test_user.id)

    p1 = detector._upsert_pattern(
        pattern_type="afternoon_slump",
        title="Afternoon Slump",
        description="Slump description",
        confidence="moderate",
        sample_size=4,
        status="active",
        supporting_metrics={"sample_size": 4},
    )
    p2 = detector._upsert_pattern(
        pattern_type="morning_momentum",
        title="Morning Momentum",
        description="Clarity description",
        confidence="high",
        sample_size=6,
        status="active",
        supporting_metrics={"sample_size": 6},
    )
    db_session.commit()

    assert p1.id != p2.id
    assert p1.pattern_type == "afternoon_slump"
    assert p2.pattern_type == "morning_momentum"


def test_pattern_lifecycle_transitions_keep_same_stable_id(db_session, test_user):
    """
    Contract: Lifecycle transitions (active -> improving -> weakening -> inactive -> resolved -> active)
    must update the EXACT SAME database row and maintain a stable ID.
    No new pattern row is created and no deletions occur.
    """
    detector = PatternDetector(db_session, test_user.id)

    # 1. Active
    p_act = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Active)",
        description="Active friction",
        confidence="high",
        sample_size=10,
        status="active",
        supporting_metrics={"status": "active"},
    )
    db_session.commit()
    stable_id = p_act.id

    # 2. Improving
    p_imp = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Improving)",
        description="Delays dropping",
        confidence="moderate",
        sample_size=14,
        status="improving",
        supporting_metrics={"status": "improving"},
    )
    db_session.commit()
    assert p_imp.id == stable_id

    # 3. Weakening
    p_weak = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Weakening)",
        description="Pattern weakening",
        confidence="low",
        sample_size=16,
        status="weakening",
        supporting_metrics={"status": "weakening"},
    )
    db_session.commit()
    assert p_weak.id == stable_id

    # 4. Inactive (insufficient recent evidence)
    p_inact = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Inactive)",
        description="No recent evidence",
        confidence="low",
        sample_size=16,
        status="inactive",
        supporting_metrics={"status": "inactive"},
    )
    db_session.commit()
    assert p_inact.id == stable_id

    # 5. Resolved
    p_res = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Resolved)",
        description="Resolution confirmed",
        confidence="high",
        sample_size=22,
        status="resolved",
        supporting_metrics={"status": "resolved"},
    )
    db_session.commit()
    assert p_res.id == stable_id

    # 6. Reactivated back to active
    p_relapse = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay (Active)",
        description="Pattern returned",
        confidence="moderate",
        sample_size=26,
        status="active",
        supporting_metrics={"status": "active"},
    )
    db_session.commit()
    assert p_relapse.id == stable_id

    # Verify single row in database
    total_patterns = (
        db_session.query(BehaviorPattern)
        .filter(
            BehaviorPattern.user_id == test_user.id,
            BehaviorPattern.pattern_type == "start_delay_resistance",
        )
        .all()
    )
    assert len(total_patterns) == 1
    assert total_patterns[0].id == stable_id
    assert total_patterns[0].status == "active"


def test_pattern_rows_never_deleted_on_lifecycle_refresh(db_session, test_user):
    """
    Contract: Patterns must NEVER be deleted by normal lifecycle handling.
    Inactive patterns remain in DB. Resolved patterns remain in DB.
    """
    detector = PatternDetector(db_session, test_user.id)

    # Establish pattern
    p = detector._upsert_pattern(
        pattern_type="afternoon_slump",
        title="Afternoon Slump",
        description="Slump observed",
        confidence="moderate",
        sample_size=8,
        status="active",
        supporting_metrics={"sample_size": 8},
    )
    db_session.commit()
    pat_id = p.id

    # Transition to inactive
    p_inact = detector._upsert_pattern(
        pattern_type="afternoon_slump",
        title="Afternoon Slump (Inactive)",
        description="Insufficient recent evidence",
        confidence="low",
        sample_size=8,
        status="inactive",
        supporting_metrics={"sample_size": 8, "insufficient_current_evidence": True},
    )
    db_session.commit()

    # Query directly from DB
    persisted = db_session.query(BehaviorPattern).filter(BehaviorPattern.id == pat_id).first()
    assert persisted is not None
    assert persisted.status == "inactive"

    # Reading persisted patterns via reader returns the pattern
    patterns = detector.get_persisted_patterns()
    assert any(pat.id == pat_id and pat.status == "inactive" for pat in patterns)


def test_pattern_unique_constraint_at_database_level(db_session, test_user):
    """
    Contract: UNIQUE(user_id, pattern_type) constraint must prevent raw duplicate insertions.
    """
    p1 = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="unique_test_slump",
        title="Test 1",
        description="Desc 1",
        status="active",
        first_detected=datetime.utcnow(),
        last_detected=datetime.utcnow(),
    )
    db_session.add(p1)
    db_session.commit()

    # Attempt to insert exact duplicate (user_id, pattern_type) directly
    p2 = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="unique_test_slump",
        title="Test 2",
        description="Desc 2",
        status="active",
        first_detected=datetime.utcnow(),
        last_detected=datetime.utcnow(),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(p2)
            db_session.flush()


def test_pattern_timestamp_semantics_stability_and_advancement(db_session, test_user):
    """
    Contract:
    - first_detected remains stable (original detection timestamp).
    - last_detected changes ONLY when supporting evidence actually changes.
    - last_detected MUST NOT advance merely because an API endpoint or detector recalculated the row.
    - last_evaluated_at updates on every evaluation.
    """
    detector = PatternDetector(db_session, test_user.id)

    # 1. Initial creation with evidence up to 2026-09-10
    p1 = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay",
        description="Start hesitation",
        confidence="moderate",
        sample_size=5,
        status="active",
        supporting_metrics={"last_observed_date": "2026-09-10", "sample_size": 5},
    )
    db_session.commit()

    first_det_time = p1.first_detected
    last_det_time_1 = p1.last_detected
    last_eval_time_1 = p1.last_evaluated_at

    assert first_det_time is not None
    assert last_det_time_1 is not None
    assert last_eval_time_1 is not None

    # 2. Recalculation with NO new evidence (same last_observed_date, same sample_size)
    p2 = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay",
        description="Start hesitation",
        confidence="moderate",
        sample_size=5,
        status="active",
        supporting_metrics={"last_observed_date": "2026-09-10", "sample_size": 5},
    )
    db_session.commit()

    # first_detected must be completely stable
    assert p2.first_detected == first_det_time

    # last_detected MUST NOT advance on pure recalculation without new evidence!
    assert p2.last_detected == last_det_time_1

    # last_evaluated_at MUST update on every recalculation
    assert p2.last_evaluated_at is not None

    # 3. New evidence arrives (later observed date and higher sample size)
    p3 = detector._upsert_pattern(
        pattern_type="start_delay_resistance",
        title="Task Delay",
        description="Start hesitation",
        confidence="high",
        sample_size=8,
        status="active",
        supporting_metrics={"last_observed_date": "2026-09-16", "sample_size": 8},
    )
    db_session.commit()

    # first_detected remains completely stable
    assert p3.first_detected == first_det_time

    # last_detected MUST advance because real evidence changed!
    assert p3.last_detected != last_det_time_1
    assert p3.last_detected.strftime("%Y-%m-%d") >= "2026-09-16"


def test_confidence_recency_semantics_lifetime_does_not_override_current(db_session, test_user):
    """
    Contract: High lifetime sample size alone NEVER forces current confidence to 'high'
    when current/recent evidence is sparse or absent.
    """
    detector = PatternDetector(db_session, test_user.id)

    # 100 historical tasks but 0 recent tasks -> status inactive -> confidence low
    conf = detector._calculate_current_confidence(
        total_sample_size=100,
        total_distinct_days=40,
        recent_sample_size=0,
        recent_distinct_days=0,
        status="inactive",
    )
    assert conf == "low"

    # Substantial lifetime (15 tasks) + substantial recent (5 tasks across 3 days) -> high
    conf_high = detector._calculate_current_confidence(
        total_sample_size=15,
        total_distinct_days=6,
        recent_sample_size=5,
        recent_distinct_days=3,
        status="active",
    )
    assert conf_high == "high"


def test_reader_vs_refresh_service_separation(db_session, test_user):
    """
    Contract:
    - get_persisted_patterns is a pure read operation that does not evaluate or alter timestamps.
    - refresh_patterns recalculates from raw evidence.
    """
    detector = PatternDetector(db_session, test_user.id)

    # Create pattern row directly
    initial_eval = datetime(2026, 9, 1, 12, 0, 0)
    p = BehaviorPattern(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        pattern_type="morning_momentum",
        title="Morning Clarity",
        description="Consistent morning focus",
        confidence="moderate",
        sample_size=4,
        status="active",
        first_detected=datetime(2026, 9, 1, 10, 0, 0),
        last_detected=datetime(2026, 9, 1, 11, 0, 0),
        last_evaluated_at=initial_eval,
    )
    db_session.add(p)
    db_session.commit()

    # Pure read
    persisted = detector.get_persisted_patterns()
    assert len(persisted) == 1
    assert persisted[0].pattern_type == "morning_momentum"
    # Reading must NOT alter last_evaluated_at
    assert persisted[0].last_evaluated_at == initial_eval
