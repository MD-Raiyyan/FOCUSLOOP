import pytest
from datetime import datetime, timedelta
from app.core.security import create_access_token, hash_token, verify_password
from app.models.user import User
from app.models.auth import RefreshSession
from app.models.behavior import BehaviorProfile
from app.models.task import Task


def test_user_registration(client, db_session):
    """
    Test user registration:
    1. Valid registration succeeds with 201 Created.
    2. Issues access_token and persistent refresh_token.
    3. Password and password hash are NEVER exposed in response.
    4. Password hash in database is Argon2id.
    5. Default behavior profile with privacy defaults is initialized.
    """
    reg_payload = {
        "name": "Jordan Lee",
        "username": "jordan_focus",
        "email": "jordan@focusloop.com",
        "password": "SuperSecretPassword123!",
        "timezone": "America/Chicago",
    }
    resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201
    data = resp.json()

    # Response validation
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert "password" not in data
    assert "password_hash" not in data

    user_info = data["user"]
    assert user_info["email"] == "jordan@focusloop.com"
    assert user_info["username"] == "jordan_focus"
    assert user_info["name"] == "Jordan Lee"
    assert "password" not in user_info
    assert "password_hash" not in user_info

    # Verify database storage
    db_user = db_session.query(User).filter(User.email == "jordan@focusloop.com").first()
    assert db_user is not None
    assert db_user.password_hash.startswith("$argon2id$")
    assert verify_password("SuperSecretPassword123!", db_user.password_hash) is True

    # Verify default profile and privacy settings initialized
    prof = db_session.query(BehaviorProfile).filter(BehaviorProfile.user_id == db_user.id).first()
    assert prof is not None
    assert prof.visibility_settings["behavior_score"] is False
    assert prof.visibility_settings["current_level"] is False
    assert prof.visibility_settings["improvement_score"] is True

    # Verify server-side refresh session recorded
    session_count = db_session.query(RefreshSession).filter(RefreshSession.user_id == db_user.id).count()
    assert session_count >= 1


def test_duplicate_registration_rejected(client):
    """Test that duplicate email or username is rejected."""
    payload = {
        "email": "duplicate@focusloop.com",
        "username": "dupe_user",
        "password": "Password12345!",
    }
    # First registration
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Duplicate email
    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


def test_user_login_flow(client):
    """
    Test login flow:
    - Correct password returns tokens
    - Incorrect password returns 401
    - Non-existent user returns 401
    - Case-insensitive email normalization
    """
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@focusloop.com",
            "username": "alice",
            "password": "AliceSecurePassword88!",
        },
    )

    # 1. Successful login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ALICE@focusloop.com", "password": "AliceSecurePassword88!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["user"]["email"] == "alice@focusloop.com"

    # 2. Incorrect password
    bad_pwd_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@focusloop.com", "password": "WrongPassword!"},
    )
    assert bad_pwd_resp.status_code == 401
    assert "Invalid email or password" in bad_pwd_resp.json()["detail"]

    # 3. Non-existent user
    non_existent = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@focusloop.com", "password": "AnyPassword!"},
    )
    assert non_existent.status_code == 401


def test_protected_routes_require_authentication(client):
    """
    Test that endpoints operating on private user data require authentication:
    - Missing token -> 401
    - Garbage token -> 401
    - Expired token -> 401
    """
    # 1. Missing Authorization header
    resp_no_auth = client.get("/api/v1/profile/me", headers={"Authorization": ""})
    assert resp_no_auth.status_code == 401
    assert "Authentication required" in resp_no_auth.json()["detail"]

    # 2. Invalid / malformed token
    resp_bad_auth = client.get("/api/v1/profile/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert resp_bad_auth.status_code == 401
    assert "Invalid or expired access token" in resp_bad_auth.json()["detail"]

    # 3. Expired token
    expired_token = create_access_token(
        user_id="any-user-id",
        expires_delta=timedelta(seconds=-10),
    )
    resp_expired = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_expired.status_code == 401


def test_identity_isolation_on_profile_me(client):
    """
    Test that /profile/me strictly determines user from token context:
    - User A token -> User A profile
    - User B token -> User B profile
    - Cannot override identity using user_id query parameters.
    """
    # Register User A
    a_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "usera@test.com", "username": "usera", "name": "User A", "password": "Password123!"},
    ).json()
    token_a = a_resp["access_token"]
    id_a = a_resp["user"]["id"]

    # Register User B
    b_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "userb@test.com", "username": "userb", "name": "User B", "password": "Password123!"},
    ).json()
    token_b = b_resp["access_token"]
    id_b = b_resp["user"]["id"]

    # 1. Requesting as User A
    resp_a = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200
    assert resp_a.json()["identity"]["id"] == id_a
    assert resp_a.json()["identity"]["name"] == "User A"

    # 2. Requesting as User B
    resp_b = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    assert resp_b.json()["identity"]["id"] == id_b
    assert resp_b.json()["identity"]["name"] == "User B"

    # 3. User A attempts to pass ?user_id=id_b to /profile/me
    resp_hijack = client.get(
        f"/api/v1/profile/me?user_id={id_b}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_hijack.status_code == 200
    # Must still resolve to User A!
    assert resp_hijack.json()["identity"]["id"] == id_a


def test_persistent_session_and_refresh_flow(client):
    """
    Test persistent authentication:
    - Access token expires
    - Client uses refresh_token to obtain a new access_token
    - New access token provides continued access without user re-logging in
    """
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "persistent@focusloop.com", "password": "PersistentPassword123!"},
    ).json()

    refresh_token = reg["refresh_token"]

    # 1. Refresh with valid token
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_token_data = refresh_resp.json()
    new_access_token = new_token_data["access_token"]
    assert new_access_token is not None

    # 2. Use new access token to query /profile/me
    me_resp = client.get(
        "/api/v1/profile/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["identity"]["email"] == "persistent@focusloop.com"

    # 3. Refresh with bogus token fails
    bad_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "totally-bogus-refresh-token"},
    )
    assert bad_refresh.status_code == 401


def test_logout_revokes_persistent_session(client):
    """
    Test explicit logout:
    - User logs out with refresh_token
    - Session is marked revoked in backend
    - Subsequent refresh requests with that token are rejected
    """
    login_data = client.post(
        "/api/v1/auth/register",
        json={"email": "logout_test@focusloop.com", "password": "Password12345!"},
    ).json()

    refresh_token = login_data["refresh_token"]
    access_token = login_data["access_token"]

    # 1. Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Successfully logged out"

    # 2. Refresh with the revoked token must fail
    revoked_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert revoked_refresh.status_code == 401
    assert "revoked" in revoked_refresh.json()["detail"].lower()


def test_resource_ownership_and_cross_user_isolation(client, db_session):
    """
    Security Test:
    Verify User A cannot access, modify, or delete User B's private tasks.
    """
    user_a = client.post(
        "/api/v1/auth/register",
        json={"email": "owner_a@test.com", "password": "Password1234!"},
    ).json()
    token_a = user_a["access_token"]
    id_a = user_a["user"]["id"]

    user_b = client.post(
        "/api/v1/auth/register",
        json={"email": "owner_b@test.com", "password": "Password1234!"},
    ).json()
    token_b = user_b["access_token"]

    # User B creates a private task
    task_b = client.post(
        "/api/v1/tasks",
        json={"name": "User B Secret Project"},
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    task_b_id = task_b["id"]

    # 1. User A tries to GET User B's task -> 404 Not Found (ownership isolation)
    get_res = client.get(
        f"/api/v1/tasks/{task_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_res.status_code == 404

    # 2. User A tries to DELETE User B's task -> 404 Not Found
    del_res = client.delete(
        f"/api/v1/tasks/{task_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_res.status_code == 404

    # 3. User A views User B's social profile -> only public metrics allowed
    social_res = client.get(
        f"/api/v1/profile/users/{user_b['user']['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert social_res.status_code == 200
    social_data = social_res.json()
    # Behavior Score and Current Level must be None (protected by backend privacy)
    assert social_data["metrics"]["behavior_score"] is None
    assert social_data["metrics"]["current_level"] is None
    assert "behavioral_intelligence" not in social_data


def test_inactive_user_blocked(client, db_session):
    """
    Test that an inactive user cannot log in or make API calls with an active token.
    """
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "inactive@focusloop.com", "password": "Password123!"},
    ).json()
    token = reg["access_token"]
    user_id = reg["user"]["id"]

    # Deactivate the user in database
    db_user = db_session.query(User).filter(User.id == user_id).first()
    db_user.is_active = False
    db_session.commit()

    # 1. API request with token fails with 403 Forbidden
    resp = client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "User account is inactive" in resp.json()["detail"]

    # 2. Login fails with 403 Forbidden
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@focusloop.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 403
    assert "inactive" in login_resp.json()["detail"].lower()
