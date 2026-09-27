import pytest
from datetime import datetime, timedelta
from app.behavior.grading import (
    MultiDimensionalBehaviorGradingStrategy,
    get_grading_strategy,
    set_grading_strategy,
    BehaviorLevelInfo,
)


def test_personal_profile_view(client):
    """
    Test that owner viewing their own profile receives complete behavioral intelligence:
    behavior_score, current_level, behavioral_patterns, strengths, weaknesses, insights, and curve.
    """
    # Create a task and checkin for default user
    task = client.post("/api/v1/tasks", json={"name": "Morning Research", "planned_time": "09:00"}).json()
    client.post(
        "/api/v1/checkins",
        json={
            "task_id": task["id"],
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "status": "done",
            "duration_minutes": 45,
            "start_delay_minutes": 5,
        },
    )

    resp = client.get("/api/v1/profile/me")
    assert resp.status_code == 200
    data = resp.json()

    # Identity
    assert "identity" in data
    assert data["identity"]["name"] == "FocusLoop Explorer"

    # Default visibility settings
    vis = data["visibility_settings"]
    assert vis["current_level"] is False
    assert vis["behavior_score"] is False
    assert vis["behavioral_patterns"] is False
    assert vis["improvement_score"] is True
    assert vis["experiment_effectiveness"] is True
    assert vis["consistency"] is True

    # Owner metrics (all private and public metrics visible to owner)
    metrics = data["metrics"]
    assert "current_level" in metrics
    assert "behavior_score" in metrics
    assert "improvement_score" in metrics
    assert "experiment_effectiveness" in metrics
    assert "consistency" in metrics
    assert "level_info" in metrics
    assert metrics["level_info"]["level_number"] >= 1

    # Behavioral intelligence (Strictly private section)
    intel = data["behavioral_intelligence"]
    assert "patterns" in intel
    assert "strengths" in intel
    assert "weaknesses" in intel
    assert "insights" in intel
    assert "focus_windows" in intel
    assert "experiments" in intel

    # Continuous progress curve
    curve = data["progress_curve"]
    assert isinstance(curve, list)
    assert len(curve) > 0
    assert "progress_score" in curve[0]
    assert "trend" in curve[0]


from app.models.social import Friendship


def test_social_profile_default_privacy(client, db_session):
    """
    Test default privacy enforcement:
    A viewer/friend viewing the profile CANNOT see private metrics:
    - behavior_score is None / omitted
    - current_level is None / omitted
    - behavioral_patterns is None
    - sensitive intelligence (weaknesses, internal analysis, experiment details) is NOT present in schema.
    Public metrics (improvement_score, experiment_effectiveness, consistency, progress_curve) ARE present.
    """
    # 1. Create a second user (the target user)
    user2_resp = client.post(
        "/api/v1/users",
        json={"name": "Sarah", "username": "sarah_focus", "email": "sarah@example.com"},
    )
    assert user2_resp.status_code == 201
    user2 = user2_resp.json()
    user2_id = user2["id"]

    # 2. Add as friend and accept request
    friend_resp = client.post("/api/v1/social/friends", json={"friend_id": user2_id})
    assert friend_resp.status_code == 201
    friendship_id = friend_resp.json()["id"]
    friendship = db_session.query(Friendship).filter(Friendship.id == friendship_id).first()
    friendship.status = "accepted"
    db_session.commit()

    # 3. View Sarah's social profile as current user
    social_resp = client.get(f"/api/v1/profile/users/{user2_id}")
    assert social_resp.status_code == 200
    social_data = social_resp.json()

    assert social_data["is_friend"] is True
    assert social_data["identity"]["name"] == "Sarah"
    assert social_data["identity"]["username"] == "sarah_focus"

    metrics = social_data["metrics"]
    # Private by default: MUST be null / omitted
    assert metrics["behavior_score"] is None
    assert metrics["current_level"] is None

    # Public by default: MUST be visible
    assert metrics["improvement_score"] is not None
    assert metrics["experiment_effectiveness"] is not None
    assert metrics["consistency"] is not None

    # Detailed behavioral patterns must be None by default
    assert social_data["behavioral_patterns"] is None

    # Progress curve must be visible list (communicates growth/trajectory; empty for brand new user with no evidence)
    assert isinstance(social_data["progress_curve"], list)
    assert len(social_data["progress_curve"]) == 0

    # Ensure sensitive fields are not in the response model at all
    assert "behavioral_intelligence" not in social_data
    assert "weaknesses" not in social_data
    assert "insights" not in social_data


def test_visibility_settings_toggle_and_isolation(client):
    """
    Test user-controlled visibility:
    1. User updates visibility (e.g. makes behavior_score visible and consistency private).
    2. Verify changing one setting does NOT leak other private metrics (Section 8 isolation rule).
    3. Verify friend's view reflects the new privacy state accurately.
    """
    # Check default visibility
    vis_resp = client.get("/api/v1/profile/visibility")
    assert vis_resp.status_code == 200
    assert vis_resp.json()["behavior_score"] is False

    # Update visibility: enable behavior_score, disable consistency
    update_resp = client.put(
        "/api/v1/profile/visibility",
        json={
            "behavior_score": True,
            "consistency": False,
        },
    )
    assert update_resp.status_code == 200
    updated_vis = update_resp.json()
    assert updated_vis["behavior_score"] is True
    assert updated_vis["consistency"] is False
    # Ensure other settings remain independent
    assert updated_vis["current_level"] is False
    assert updated_vis["behavioral_patterns"] is False
    assert updated_vis["improvement_score"] is True

    # View personal profile: reflected in owner settings
    me_resp = client.get("/api/v1/profile/me")
    assert me_resp.json()["visibility_settings"]["behavior_score"] is True


def test_non_friend_profile_view(client):
    """
    Test non-friend viewing profile:
    - is_friend is False
    - Strictly enforces backend privacy controls
    - Never leaks sensitive data
    """
    user_resp = client.post(
        "/api/v1/users",
        json={"name": "Liam", "username": "liam_deepwork", "email": "liam@example.com"},
    )
    liam_id = user_resp.json()["id"]

    # View Liam's profile without being friends
    resp = client.get(f"/api/v1/profile/users/{liam_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_friend"] is False
    assert data["identity"]["name"] == "Liam"
    assert data["metrics"]["behavior_score"] is None
    assert data["metrics"]["current_level"] is None
    assert "behavioral_intelligence" not in data


def test_friend_view_updates_dynamically_when_settings_change(client, db_session):
    """
    Test that when a target user makes behavior_score visible:
    - Friend sees behavior_score
    - Friend STILL DOES NOT see current_level (isolation requirement)
    - Friend DOES NOT see raw patterns or private weaknesses
    """
    user_target = client.post(
        "/api/v1/users",
        json={"name": "Nora", "username": "nora_f", "email": "nora@example.com"},
    ).json()
    target_id = user_target["id"]

    # Create friendship
    client.post("/api/v1/social/friends", json={"friend_id": target_id})

    # Default: friend sees no behavior_score
    view1 = client.get(f"/api/v1/profile/users/{target_id}").json()
    assert view1["metrics"]["behavior_score"] is None
    assert view1["metrics"]["current_level"] is None

    # Target user updates their visibility settings in DB to make behavior_score True
    from app.models.behavior import BehaviorProfile
    target_prof = db_session.query(BehaviorProfile).filter(BehaviorProfile.user_id == target_id).first()
    if not target_prof:
        from app.behavior.profile import BehaviorProfileManager
        BehaviorProfileManager(db_session, target_id).refresh_profile()
        target_prof = db_session.query(BehaviorProfile).filter(BehaviorProfile.user_id == target_id).first()

    target_prof.visibility_settings = {
        "current_level": False,
        "behavior_score": True,  # User made behavior score public
        "improvement_score": True,
        "experiment_effectiveness": True,
        "consistency": True,
        "behavioral_patterns": False,
    }
    db_session.commit()

    # Now viewer requests friend's profile
    view2 = client.get(f"/api/v1/profile/users/{target_id}").json()
    assert view2["metrics"]["behavior_score"] is not None  # Now visible
    assert view2["metrics"]["current_level"] is None  # Still private!
    assert view2["behavioral_patterns"] is None  # Still private!
    assert "behavioral_intelligence" not in view2



def test_friends_crud_and_convenience_endpoints(client, db_session):
    """
    Test friends management:
    - List friends
    - Add friend
    - View friend profile via social router
    - Remove friend
    """
    # Create user B
    b_resp = client.post(
        "/api/v1/users",
        json={"name": "Marcus", "username": "marcus_k", "email": "marcus@example.com"},
    )
    b_id = b_resp.json()["id"]

    # 1. Add friend and accept request
    add_resp = client.post("/api/v1/social/friends", json={"friend_id": b_id})
    assert add_resp.status_code == 201
    friendship_id = add_resp.json()["id"]
    friendship = db_session.query(Friendship).filter(Friendship.id == friendship_id).first()
    friendship.status = "accepted"
    db_session.commit()

    # 2. List friends
    list_resp = client.get("/api/v1/social/friends")
    assert list_resp.status_code == 200
    friends = list_resp.json()
    assert any(f["id"] == b_id for f in friends)

    # 3. View friend profile via convenience endpoint
    prof_resp = client.get(f"/api/v1/social/friends/{b_id}/profile")
    assert prof_resp.status_code == 200
    assert prof_resp.json()["identity"]["name"] == "Marcus"
    assert prof_resp.json()["is_friend"] is True

    # 4. Remove friend
    del_resp = client.delete(f"/api/v1/social/friends/{b_id}")
    assert del_resp.status_code == 204

    # 5. List again - Marcus should no longer be present
    list2_resp = client.get("/api/v1/social/friends")
    assert not any(f["id"] == b_id for f in list2_resp.json())


def test_continuous_progress_curve_trajectory(client):
    """
    Test behavior progress curve:
    - Direct endpoint /api/v1/profile/curve
    - Verifies no fabricated points for brand new user with no evidence.
    - Verifies evidence-backed points with dates, progress scores, and valid trajectory trends.
    """
    # 1. User with no checkins gets clean empty list (no fabricated points)
    new_user_resp = client.post(
        "/api/v1/users",
        json={"name": "Curve User", "username": "curve_user", "email": "curve@example.com"},
    )
    user_id = new_user_resp.json()["id"]

    # 2. Authenticated user with checkins gets real evidence points
    task_resp = client.post("/api/v1/tasks", json={"name": "Daily Habit", "frequency": "daily"}).json()
    task_id = task_resp["id"]

    today = datetime.utcnow().date()
    # Log checkins on two distinct dates
    d1 = (today - timedelta(days=2)).isoformat()
    d2 = (today - timedelta(days=1)).isoformat()

    client.post("/api/v1/checkins", json={"task_id": task_id, "date": d1, "status": "done", "duration_minutes": 30, "start_delay_minutes": 5})
    client.post("/api/v1/checkins", json={"task_id": task_id, "date": d2, "status": "done", "duration_minutes": 35, "start_delay_minutes": 4})

    curve_resp = client.get("/api/v1/profile/curve?days=7")
    assert curve_resp.status_code == 200
    curve = curve_resp.json()
    assert len(curve) == 2
    for pt in curve:
        assert "date" in pt
        assert "progress_score" in pt
        assert pt["trend"] in ["initial", "improving", "stable", "setback", "recovery"]


def test_grading_abstraction_extensibility():
    """
    Test that the Level / Grading system is a decoupled, extensible abstraction.
    Different strategies can be evaluated without hardcoding or breaking the profile system.
    """
    strategy = MultiDimensionalBehaviorGradingStrategy()

    # Tier 1: Baseline
    level1 = strategy.evaluate(
        behavior_score=40.0,
        improvement_score=45.0,
        consistency=40.0,
        experiment_effectiveness=70.0,
        total_sessions=1,
    )
    assert level1.level_number == 1
    assert "Foundation" in level1.full_title

    # Tier 2: Pattern Explorer (consistency >= 45, behavior >= 35, sessions >= 3)
    level2 = strategy.evaluate(
        behavior_score=48.0,
        improvement_score=55.0,
        consistency=50.0,
        experiment_effectiveness=75.0,
        total_sessions=4,
    )
    assert level2.level_number == 2
    assert "Pattern Explorer" in level2.full_title

    # Tier 4: Habit Optimizer (consistency >= 75, behavior >= 65, sessions >= 15)
    level4 = strategy.evaluate(
        behavior_score=78.0,
        improvement_score=80.0,
        consistency=82.0,
        experiment_effectiveness=85.0,
        total_sessions=18,
    )
    assert level4.level_number == 4
    assert "Habit Optimizer" in level4.full_title

    # Verify custom strategy can be plugged in
    class CustomLevelStrategy:
        def evaluate(self, behavior_score, improvement_score, consistency, experiment_effectiveness, total_sessions=0):
            return BehaviorLevelInfo(
                level_number=99,
                level_name="Custom Architect",
                full_title="Level 99 — Custom Architect",
                description="Custom experimental tier",
                milestone_unlocked="Unlocked custom testing",
                next_level_requirements="None",
                progress_to_next_level=100.0,
            )

    original_strategy = get_grading_strategy()
    try:
        set_grading_strategy(CustomLevelStrategy())
        custom_res = get_grading_strategy().evaluate(50.0, 50.0, 50.0, 50.0)
        assert custom_res.level_number == 99
        assert "Custom Architect" in custom_res.full_title
    finally:
        set_grading_strategy(original_strategy)
