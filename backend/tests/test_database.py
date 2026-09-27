import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.models.user import User
from app.models.auth import RefreshSession
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.procrastination import ProcrastinationEvent
from app.models.screen_usage import ScreenUsage
from app.models.sleep import SleepRecord
from app.models.behavior import (
    BehaviorMetric,
    BehaviorPattern,
    BehaviorProfile,
    DEFAULT_PROFILE_VISIBILITY,
)
from app.models.experiment import Experiment, ExperimentResult
from app.models.chat import Conversation, Message
from app.models.social import Friendship


def test_user_persistence_across_sessions(test_engine):
    """Test user creation in one session and retrieval in a completely new session."""
    Session = sessionmaker(bind=test_engine)
    user_id = str(uuid.uuid4())
    user_email = f"persist_{uuid.uuid4().hex[:6]}@focusloop.test"

    # Session 1: Create and commit user
    session1 = Session()
    try:
        user = User(
            id=user_id,
            name="Persistence Tester",
            username=f"user_{uuid.uuid4().hex[:6]}",
            email=user_email,
            password_hash="argon2id$mockedhash12345",
            is_active=True,
        )
        session1.add(user)
        session1.commit()
    finally:
        session1.close()

    # Session 2: Retrieve user in fresh session
    session2 = Session()
    try:
        retrieved = session2.query(User).filter(User.id == user_id).first()
        assert retrieved is not None
        assert retrieved.email == user_email
        assert retrieved.name == "Persistence Tester"
        assert retrieved.password_hash == "argon2id$mockedhash12345"
        assert retrieved.is_active is True
    finally:
        session2.close()


def test_task_and_checkin_relationship(test_engine):
    """Test Task -> TaskCheckin relationship and foreign key cascade."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(
            id=str(uuid.uuid4()),
            name="Task Tester",
            email=f"task_{uuid.uuid4().hex[:6]}@focusloop.test",
        )
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Deep Work Focus Block",
            planned_time="09:00",
            target_duration_minutes="45",
        )
        checkin = TaskCheckin(
            id=str(uuid.uuid4()),
            task_id=task.id,
            user_id=user.id,
            date="2026-09-26",
            status="done",
            duration_minutes=45,
            start_delay_minutes=5,
        )
        session.add_all([user, task, checkin])
        session.commit()

        # Query task and verify checkins relationship
        queried_task = session.query(Task).filter(Task.id == task.id).first()
        assert queried_task is not None
        assert len(queried_task.checkins) == 1
        assert queried_task.checkins[0].status == "done"
        assert queried_task.checkins[0].user_id == user.id
    finally:
        session.close()


def test_task_cascade_deletion(test_engine):
    """Test deleting a task cascades and removes associated check-ins."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"cascade_{uuid.uuid4().hex[:6]}@focusloop.test")
        task = Task(id=str(uuid.uuid4()), user_id=user.id, name="To Delete")
        checkin = TaskCheckin(
            id=str(uuid.uuid4()),
            task_id=task.id,
            user_id=user.id,
            date="2026-09-26",
            status="partial",
        )
        session.add_all([user, task, checkin])
        session.commit()

        # Delete task
        session.delete(task)
        session.commit()

        # Verify checkin is removed
        remaining_checkin = session.query(TaskCheckin).filter(TaskCheckin.id == checkin.id).first()
        assert remaining_checkin is None
    finally:
        session.close()


def test_user_cross_isolation(test_engine):
    """Test that User B cannot query or retrieve tasks belonging to User A."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user_a = User(id=str(uuid.uuid4()), email=f"usera_{uuid.uuid4().hex[:6]}@test.com")
        user_b = User(id=str(uuid.uuid4()), email=f"userb_{uuid.uuid4().hex[:6]}@test.com")
        task_a = Task(id=str(uuid.uuid4()), user_id=user_a.id, name="Confidential Task A")
        session.add_all([user_a, user_b, task_a])
        session.commit()

        # Query user B tasks
        user_b_tasks = session.query(Task).filter(Task.user_id == user_b.id).all()
        assert len(user_b_tasks) == 0

        # Query with user B filter for task_a id
        b_access = session.query(Task).filter(Task.id == task_a.id, Task.user_id == user_b.id).first()
        assert b_access is None
    finally:
        session.close()


def test_refresh_session_persistence_and_revocation(test_engine):
    """Test persistent refresh session storage, verification, and revocation."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"auth_{uuid.uuid4().hex[:6]}@test.com")
        session_id = str(uuid.uuid4())
        token_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        refresh_session = RefreshSession(
            id=session_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30),
            revoked_at=None,
        )
        session.add_all([user, refresh_session])
        session.commit()

        # Active check
        active_session = session.query(RefreshSession).filter(
            RefreshSession.id == session_id,
            RefreshSession.revoked_at.is_(None),
        ).first()
        assert active_session is not None

        # Revoke session
        active_session.revoked_at = datetime.utcnow()
        session.commit()

        # Rejected check
        revoked_query = session.query(RefreshSession).filter(
            RefreshSession.id == session_id,
            RefreshSession.revoked_at.is_(None),
        ).first()
        assert revoked_query is None
    finally:
        session.close()


def test_procrastination_event_distinguishes_confirmed_vs_inferred(test_engine):
    """Test distinguishing user-confirmed procrastination from inferred events."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"proc_{uuid.uuid4().hex[:6]}@test.com")
        confirmed_event = ProcrastinationEvent(
            id=str(uuid.uuid4()),
            user_id=user.id,
            duration_seconds=900,
            user_confirmed=True,
            trigger_reason="overwhelmed",
            context_data={"top_app": "youtube"},
        )
        inferred_event = ProcrastinationEvent(
            id=str(uuid.uuid4()),
            user_id=user.id,
            duration_seconds=1200,
            user_confirmed=False,
            trigger_reason="heuristic_inactivity",
            context_data={"heuristic": "screen_time_spike"},
        )
        session.add_all([user, confirmed_event, inferred_event])
        session.commit()

        confirmed_records = session.query(ProcrastinationEvent).filter(
            ProcrastinationEvent.user_id == user.id,
            ProcrastinationEvent.user_confirmed.is_(True),
        ).all()
        inferred_records = session.query(ProcrastinationEvent).filter(
            ProcrastinationEvent.user_id == user.id,
            ProcrastinationEvent.user_confirmed.is_(False),
        ).all()

        assert len(confirmed_records) == 1
        assert confirmed_records[0].trigger_reason == "overwhelmed"
        assert len(inferred_records) == 1
        assert inferred_records[0].trigger_reason == "heuristic_inactivity"
    finally:
        session.close()


def test_experiment_and_result_persistence(test_engine):
    """Test experiment and experiment_results persistence with metrics."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"exp_{uuid.uuid4().hex[:6]}@test.com")
        exp = Experiment(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Morning Scheduling Shift",
            description="Shift daily focus task from 14:00 to 10:00",
            hypothesis="Starting earlier will reduce start delay",
            start_date="2026-09-01",
            end_date="2026-09-14",
            target_metric="start_delay_minutes",
            baseline_value=35.0,
            target_value=10.0,
            status="completed",
        )
        result = ExperimentResult(
            id=str(uuid.uuid4()),
            experiment_id=exp.id,
            metric_name="start_delay_minutes",
            before_value=35.0,
            after_value=8.0,
            change_value=-27.0,
            percent_change=-77.1,
            conclusion="positive",
            result_summary="Start delay decreased significantly.",
        )
        session.add_all([user, exp, result])
        session.commit()

        queried_exp = session.query(Experiment).filter(Experiment.id == exp.id).first()
        assert queried_exp is not None
        assert len(queried_exp.results) == 1
        assert queried_exp.results[0].conclusion == "positive"
        assert queried_exp.results[0].change_value == -27.0
    finally:
        session.close()


def test_conversation_and_messages_persistence(test_engine):
    """Test conversation and chronological message storage."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"chat_{uuid.uuid4().hex[:6]}@test.com")
        conv = Conversation(id=str(uuid.uuid4()), user_id=user.id, title="Reflecting on Morning Routines")
        msg1 = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            sender="user",
            content="I noticed I delay my first task when I sleep poorly.",
        )
        msg2 = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            sender="assistant",
            content="That correlates with your recorded start delays. Let's design a micro-experiment.",
        )
        session.add_all([user, conv, msg1, msg2])
        session.commit()

        queried_conv = session.query(Conversation).filter(Conversation.id == conv.id).first()
        assert queried_conv is not None
        assert len(queried_conv.messages) == 2
        assert queried_conv.messages[0].sender == "user"
        assert queried_conv.messages[1].sender == "assistant"
    finally:
        session.close()


def test_sleep_record_persistence(test_engine):
    """Test SleepRecord persistence and association with User."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"sleep_{uuid.uuid4().hex[:6]}@test.com")
        now = datetime.utcnow()
        sleep_rec = SleepRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            start_time=now - timedelta(hours=8),
            end_time=now,
            duration_minutes=480,
            quality_score=85.0,
            source="manual",
            notes="Felt well rested",
        )
        session.add_all([user, sleep_rec])
        session.commit()

        queried = session.query(SleepRecord).filter(SleepRecord.id == sleep_rec.id).first()
        assert queried is not None
        assert queried.duration_minutes == 480
        assert queried.quality_score == 85.0
        assert queried.user.id == user.id
    finally:
        session.close()


def test_friendship_uniqueness_constraint(test_engine):
    """Test unique constraint prevents duplicate friendship pairs."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user1 = User(id=str(uuid.uuid4()), email=f"u1_{uuid.uuid4().hex[:6]}@test.com")
        user2 = User(id=str(uuid.uuid4()), email=f"u2_{uuid.uuid4().hex[:6]}@test.com")
        session.add_all([user1, user2])
        session.commit()

        friendship1 = Friendship(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            friend_id=user2.id,
            status="accepted",
        )
        session.add(friendship1)
        session.commit()

        # Duplicate friendship attempt
        friendship2 = Friendship(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            friend_id=user2.id,
            status="accepted",
        )
        session.add(friendship2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_profile_visibility_defaults_and_privacy(test_engine):
    """Test BehaviorProfile visibility defaults adhere strictly to privacy guidelines."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        user = User(id=str(uuid.uuid4()), email=f"priv_{uuid.uuid4().hex[:6]}@test.com")
        profile = BehaviorProfile(
            user_id=user.id,
            profile_data={"insights": "sensitive internal behavior patterns"},
            visibility_settings=dict(DEFAULT_PROFILE_VISIBILITY),
            behavior_score=78.5,
            current_level="Level 2 — Acceleration",
            improvement_score=15.0,
            experiment_effectiveness=82.0,
            consistency=75.0,
        )
        session.add_all([user, profile])
        session.commit()

        queried = session.query(BehaviorProfile).filter(BehaviorProfile.user_id == user.id).first()
        assert queried is not None
        vis = queried.visibility_settings

        # Assert private by default
        assert vis.get("current_level") is False
        assert vis.get("behavior_score") is False
        assert vis.get("behavioral_patterns") is False

        # Assert public to friends by default
        assert vis.get("improvement_score") is True
        assert vis.get("experiment_effectiveness") is True
        assert vis.get("consistency") is True
    finally:
        session.close()


def test_transaction_rollback_on_failure(test_engine):
    """Test that failed transactions roll back cleanly without partial persistence."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    dup_email = f"dup_{uuid.uuid4().hex[:6]}@test.com"
    task_id = str(uuid.uuid4())
    try:
        user1 = User(id=str(uuid.uuid4()), email=dup_email)
        session.add(user1)
        session.commit()

        # In a subsequent transaction, add a task, then fail with duplicate unique email
        task = Task(id=task_id, user_id=user1.id, name="Uncommitted Task")
        session.add(task)

        user2 = User(id=str(uuid.uuid4()), email=dup_email)
        session.add(user2)
        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

        # Confirm the uncommitted task was rolled back
        queried = session.query(Task).filter(Task.id == task_id).first()
        assert queried is None
    finally:
        session.close()


def test_real_postgresql_end_to_end_persistence():
    """
    STEP 26: Real PostgreSQL test against live PostgreSQL database.
    Verifies connection, table persistence across session/engine closures,
    foreign keys, cascade deletions, and clean transactional boundaries.
    """
    pg_url = "postgresql+psycopg2://localhost:5432/focusloop"
    try:
        pg_engine = create_engine(pg_url, pool_pre_ping=True)
        # Verify connection
        with pg_engine.connect() as conn:
            pass
    except Exception as e:
        pytest.skip(f"PostgreSQL not accessible on {pg_url}: {e}")

    # Ensure tables exist
    Base.metadata.create_all(bind=pg_engine)
    PgSession = sessionmaker(bind=pg_engine)

    # 1. Insert real records in session 1
    session1 = PgSession()
    test_uid = str(uuid.uuid4())
    test_email = f"pg_{uuid.uuid4().hex[:8]}@focusloop.prod"
    try:
        pg_user = User(
            id=test_uid,
            name="Postgres Persistence User",
            username=f"pguser_{uuid.uuid4().hex[:6]}",
            email=test_email,
            password_hash="argon2id$verifiedhash789",
            is_active=True,
        )
        pg_task = Task(
            id=str(uuid.uuid4()),
            user_id=test_uid,
            name="PostgreSQL Focus Task",
            planned_time="11:00",
        )
        pg_checkin = TaskCheckin(
            id=str(uuid.uuid4()),
            task_id=pg_task.id,
            user_id=test_uid,
            date="2026-09-26",
            status="done",
            duration_minutes=30,
        )
        pg_sleep = SleepRecord(
            id=str(uuid.uuid4()),
            user_id=test_uid,
            start_time=datetime.utcnow() - timedelta(hours=7),
            end_time=datetime.utcnow(),
            duration_minutes=420,
            quality_score=90.0,
        )
        session1.add_all([pg_user, pg_task, pg_checkin, pg_sleep])
        session1.commit()
    finally:
        session1.close()

    # 2. Simulate complete restart: Dispose the engine completely
    pg_engine.dispose()

    # 3. Re-open brand new engine and session
    restarted_engine = create_engine(pg_url, pool_pre_ping=True)
    RestartedSession = sessionmaker(bind=restarted_engine)
    session2 = RestartedSession()
    try:
        # Verify records survived complete restart
        restarted_user = session2.query(User).filter(User.id == test_uid).first()
        assert restarted_user is not None
        assert restarted_user.email == test_email
        assert len(restarted_user.tasks) == 1
        assert restarted_user.tasks[0].name == "PostgreSQL Focus Task"
        assert len(restarted_user.tasks[0].checkins) == 1
        assert restarted_user.tasks[0].checkins[0].status == "done"
        assert len(restarted_user.sleep_records) == 1
        assert restarted_user.sleep_records[0].duration_minutes == 420

        # Verify cascade deletion on PostgreSQL
        session2.delete(restarted_user)
        session2.commit()

        # Confirm cascade deletion cleaned up child records
        rem_tasks = session2.query(Task).filter(Task.user_id == test_uid).all()
        rem_checkins = session2.query(TaskCheckin).filter(TaskCheckin.user_id == test_uid).all()
        rem_sleep = session2.query(SleepRecord).filter(SleepRecord.user_id == test_uid).all()
        assert len(rem_tasks) == 0
        assert len(rem_checkins) == 0
        assert len(rem_sleep) == 0
    finally:
        session2.close()
        restarted_engine.dispose()
