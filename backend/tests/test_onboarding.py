import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.models.user import User
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.onboarding import UserGoal, UserRoutineContext, UserChallenge, UserInterest
from app.behavior.metrics import BehaviorMetricsCalculator
from app.behavior.profile import BehaviorProfileManager
from app.ai.context_builder import AIContextBuilder


def test_01_new_user_starts_with_onboarding_incomplete(client):
    """1. New user starts with onboarding incomplete."""
    unique_email = f"newuser_{uuid.uuid4().hex[:6]}@focusloop.io"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "password": "Password123!",
            "name": "Fresh User",
        },
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()["user"]
    assert user_data["onboarding_completed"] is False
    assert user_data["onboarding_completed_at"] is None
    assert user_data["onboarding_step"] == "1"


def test_02_new_user_can_save_partial_onboarding(client):
    """2. New user can save partial onboarding."""
    patch_resp = client.patch(
        "/api/v1/onboarding",
        json={
            "step": "2",
            "age_range": "25-34",
            "gender": "prefer_not_to_say",
        },
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["step"] == "2"
    assert data["profile"]["age_range"] == "25-34"
    assert data["profile"]["gender"] == "prefer_not_to_say"


def test_03_new_user_can_resume_onboarding(client):
    """3. New user can resume onboarding."""
    # First save step 2 partial progress
    client.patch(
        "/api/v1/onboarding",
        json={"step": "2", "age_range": "25-34"},
    )
    status_resp = client.get("/api/v1/onboarding/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["onboarding_completed"] is False
    assert status_data["current_step"] == "2"
    assert status_data["has_partial_data"] is True


def test_04_05_06_onboarding_completion_persists_and_is_idempotent(client):
    """4, 5, 6. Onboarding can be completed, completion persists, and existing completed users are not forced into onboarding."""
    put_resp = client.put(
        "/api/v1/onboarding",
        json={
            "step": "7",
            "goal": {
                "category": "Study consistently",
                "description": "Prepare for my final certification exams",
            },
            "routine": {
                "preferred_time_window": "Evening",
                "daily_available_duration": "1-2 hours",
            },
            "challenges": ["Delaying tasks", "Phone/social media distraction"],
            "interests": ["Coding", "Fitness"],
        },
    )
    assert put_resp.status_code == 200

    comp_resp = client.post("/api/v1/onboarding/complete")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["onboarding_completed"] is True
    assert comp_data["completed_at"] is not None

    # Idempotent re-completion
    comp_resp_2 = client.post("/api/v1/onboarding/complete")
    assert comp_resp_2.status_code == 200
    assert comp_resp_2.json()["onboarding_completed"] is True

    # Check status reflects completed
    status_resp = client.get("/api/v1/onboarding/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["onboarding_completed"] is True


def test_07_unauthorized_users_cannot_access_onboarding():
    """7. Unauthorized users cannot access another user's onboarding."""
    with TestClient(fastapi_app) as unauth_client:
        resp = unauth_client.get("/api/v1/onboarding/status")
        assert resp.status_code == 401

        resp_get = unauth_client.get("/api/v1/onboarding")
        assert resp_get.status_code == 401

        resp_patch = unauth_client.patch("/api/v1/onboarding", json={"step": "3"})
        assert resp_patch.status_code == 401


def test_08_09_10_11_entity_persistence_and_provenance(db_session, test_user):
    """8, 9, 10, 11, 13. Goal, availability, challenge, interest persistence with self_reported provenance."""
    goal = UserGoal(
        user_id=test_user.id,
        category="Improve focus",
        description="Deep work without context switching",
        is_active=True,
    )
    routine = UserRoutineContext(
        user_id=test_user.id,
        preferred_time_window="Morning",
        daily_available_duration="2-4 hours",
    )
    challenge = UserChallenge(
        user_id=test_user.id,
        challenge_text="Losing focus after lunch",
        source="self_reported",
        is_active=True,
    )
    interest = UserInterest(
        user_id=test_user.id,
        interest_text="Gaming",
        source="self_reported",
        is_active=True,
    )
    db_session.add_all([goal, routine, challenge, interest])
    db_session.commit()

    saved_goal = db_session.query(UserGoal).filter(UserGoal.user_id == test_user.id, UserGoal.is_active == True).first()
    assert saved_goal is not None
    assert saved_goal.category == "Improve focus"

    saved_routine = db_session.query(UserRoutineContext).filter(UserRoutineContext.user_id == test_user.id).first()
    assert saved_routine is not None
    assert saved_routine.preferred_time_window == "Morning"

    saved_challenge = db_session.query(UserChallenge).filter(UserChallenge.user_id == test_user.id).first()
    assert saved_challenge is not None
    assert saved_challenge.source == "self_reported"

    saved_interest = db_session.query(UserInterest).filter(UserInterest.user_id == test_user.id).first()
    assert saved_interest is not None
    assert saved_interest.source == "self_reported"


def test_12_profile_editing_after_onboarding(client):
    """12. Users can edit goal, availability, challenges, interests after onboarding."""
    update_resp = client.put(
        "/api/v1/onboarding",
        json={
            "goal": {
                "category": "Build my career",
                "description": "Switch from junior to senior engineer",
            },
            "routine": {
                "preferred_time_window": "Morning",
                "daily_available_duration": "2-4 hours",
            },
            "challenges": ["Overthinking"],
            "interests": ["Reading", "Chess"],
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["goal"]["category"] == "Build my career"
    assert data["routine"]["preferred_time_window"] == "Morning"
    assert len(data["challenges"]) == 1
    assert data["challenges"][0]["challenge_text"] == "Overthinking"
    assert len(data["interests"]) == 2


def test_14_onboarding_does_not_alter_behavior_score_directly(db_session, test_user):
    """14. Onboarding data does NOT alter Behavior Score directly."""
    calc = BehaviorMetricsCalculator(db_session, test_user.id)
    baseline_score = calc.compute_behavior_score()

    # Add ambitious goals and challenges
    goal = UserGoal(
        user_id=test_user.id,
        category="Master Everything",
        description="Become world class in 30 days",
        is_active=True,
    )
    db_session.add(goal)
    db_session.commit()

    # Behavior Score must remain exactly the same because no checkins/tasks changed
    calc_after = BehaviorMetricsCalculator(db_session, test_user.id)
    after_score = calc_after.compute_behavior_score()
    assert after_score == baseline_score


def test_15_16_17_ai_context_builder_inclusion_exclusion_and_provenance(db_session, test_user):
    """
    15. AI Context Builder includes relevant onboarding context.
    16. AI Context Builder excludes irrelevant onboarding context (e.g. unrelated hobby).
    17. AI context distinguishes self-reported vs measured vs derived.
    """
    goal = UserGoal(
        user_id=test_user.id,
        category="Study consistently",
        description="Prepare for medical entrance exam",
        is_active=True,
    )
    routine = UserRoutineContext(
        user_id=test_user.id,
        preferred_time_window="Evening",
        daily_available_duration="2-4 hours",
    )
    challenge = UserChallenge(
        user_id=test_user.id,
        challenge_text="Delaying task starts",
        source="self_reported",
        is_active=True,
    )
    interest = UserInterest(
        user_id=test_user.id,
        interest_text="Gaming",
        source="self_reported",
        is_active=True,
    )
    db_session.add_all([goal, routine, challenge, interest])
    db_session.commit()

    builder = AIContextBuilder(db_session, test_user.id)

    # Query 1: Narrow study question -> Gaming hobby is irrelevant and should be excluded
    ctx_study = builder.build_context(question="Why am I struggling to study lately?")
    user_ctx = ctx_study.user_context
    assert "active_goal" in user_ctx
    assert user_ctx["active_goal"]["category"] == "Study consistently"
    assert user_ctx["active_goal"]["source"] == "self_reported"
    assert "availability" in user_ctx
    assert user_ctx["availability"]["source"] == "self_reported"
    assert "self_reported_challenges" in user_ctx
    # Gaming interest is excluded for study friction question!
    assert "interests" not in user_ctx

    # Query 2: Question explicitly mentioning gaming -> Gaming interest should be included
    ctx_gaming = builder.build_context(question="I like gaming. How can I balance it with studying?")
    user_ctx_gaming = ctx_gaming.user_context
    assert "interests" in user_ctx_gaming
    interest_names = [i["interest"] for i in user_ctx_gaming["interests"]]
    assert "Gaming" in interest_names
    assert user_ctx_gaming["interests"][0]["source"] == "self_reported"

    # 17. Verify provenance separation
    # Self-reported in user_context
    assert user_ctx["active_goal"]["source"] == "self_reported"
    # Measured in metrics
    assert ctx_study.metrics["task_completion"]["source"] == "task_checkins"


def test_18_ai_context_does_not_leak_private_social_data(db_session, test_user):
    """18. AI context does not leak private social/friend data."""
    builder = AIContextBuilder(db_session, test_user.id)
    ctx = builder.build_context(question="Give me a comprehensive coaching review")

    ctx_dict = ctx.to_dict()
    assert "friends" not in ctx_dict
    assert "friendships" not in ctx_dict
    assert "social" not in ctx_dict


def test_19_20_stale_goal_handling_and_no_duplicate_records(client, db_session, test_user):
    """19, 20. Stale/old goal handling behaves correctly if user changes goal, and no duplicates are created."""
    # First goal
    client.put(
        "/api/v1/onboarding",
        json={
            "goal": {"category": "Old Goal", "description": "Old description"},
            "routine": {"preferred_time_window": "Morning", "daily_available_duration": "1 hour"},
        },
    )

    # Second goal (change)
    client.put(
        "/api/v1/onboarding",
        json={
            "goal": {"category": "New Goal", "description": "New description"},
            "routine": {"preferred_time_window": "Night", "daily_available_duration": "3 hours"},
        },
    )

    # Verify in DB: only one active goal exists, previous goal is deactivated
    active_goals = (
        db_session.query(UserGoal)
        .filter(UserGoal.user_id == test_user.id, UserGoal.is_active == True)
        .all()
    )
    assert len(active_goals) == 1
    assert active_goals[0].category == "New Goal"

    # Verify routine context: exactly 1 routine record exists (no duplicate rows)
    routines = (
        db_session.query(UserRoutineContext)
        .filter(UserRoutineContext.user_id == test_user.id)
        .all()
    )
    assert len(routines) == 1
    assert routines[0].preferred_time_window == "Night"
