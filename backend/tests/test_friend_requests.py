import pytest
from app.core.security import create_access_token
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.user import User
from app.models.social import Friendship


@pytest.fixture
def user_a_client(client):
    """Client authenticated as User A (test_user from conftest)."""
    return client


@pytest.fixture
def make_user_client(db_session):
    """Helper fixture to create an authenticated client for an arbitrary user."""
    def _make(user: User):
        token = create_access_token(user_id=user.id)
        test_client = TestClient(fastapi_app)
        test_client.headers["Authorization"] = f"Bearer {token}"
        return test_client
    return _make


def test_username_lookup(client, db_session):
    # Create target user with username
    target = User(
        name="Elena Rostova",
        email="elena@example.com",
        username="elena_r",
        bio="Deep work enthusiast",
        avatar_url="https://example.com/elena.jpg",
        is_active=True,
    )
    db_session.add(target)
    db_session.commit()

    # 1. Lookup with '@' prefix
    resp = client.get("/api/v1/social/lookup?username=@elena_r")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == target.id
    assert data["name"] == "Elena Rostova"
    assert data["username"] == "elena_r"
    assert data["bio"] == "Deep work enthusiast"
    assert data["avatar_url"] == "https://example.com/elena.jpg"
    assert data["relationship_status"] == "none"
    # Privacy check: No PII exposed
    assert "email" not in data
    assert "password_hash" not in data
    assert "behavior_score" not in data

    # 2. Lookup without '@' prefix and uppercase
    resp2 = client.get("/api/v1/social/lookup?username=ELENA_R")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == target.id

    # 3. Lookup alias /find
    resp3 = client.get("/api/v1/social/find?username=@elena_r")
    assert resp3.status_code == 200
    assert resp3.json()["id"] == target.id

    # 4. Lookup non-existent username -> 404
    resp4 = client.get("/api/v1/social/lookup?username=@nobody_here_xyz")
    assert resp4.status_code == 404

    # 5. Lookup empty username -> 400
    resp5 = client.get("/api/v1/social/lookup?username=@")
    assert resp5.status_code == 400

    # 6. Lookup self -> relationship_status == 'self'
    me_resp = client.get("/api/v1/auth/me").json()
    my_username = me_resp["username"]
    resp6 = client.get(f"/api/v1/social/lookup?username=@{my_username}")
    assert resp6.status_code == 200
    assert resp6.json()["relationship_status"] == "self"


def test_send_friend_request_pending_state(client, db_session, make_user_client):
    # Create User B
    user_b = User(
        name="Bob Builder",
        email="bob@example.com",
        username="bob_b",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)
    client_b = make_user_client(user_b)

    # 1. User A sends friend request by username
    send_resp = client.post("/api/v1/social/friends", json={"username": "@bob_b"})
    assert send_resp.status_code == 201
    friendship_data = send_resp.json()
    assert friendship_data["status"] == "pending"
    assert friendship_data["friend_id"] == user_b.id

    # 2. Check that neither user has confirmed friends yet
    friends_a = client.get("/api/v1/social/friends").json()
    assert not any(f["id"] == user_b.id for f in friends_a)
    friends_b = client_b.get("/api/v1/social/friends").json()
    assert len(friends_b) == 0

    # 3. Check outgoing requests for User A
    out_resp = client.get("/api/v1/social/requests/outgoing")
    assert out_resp.status_code == 200
    outgoing = out_resp.json()
    assert any(o["friend_id"] == user_b.id for o in outgoing)

    # 4. Check incoming requests for User B
    in_resp = client_b.get("/api/v1/social/requests/incoming")
    assert in_resp.status_code == 200
    incoming = in_resp.json()
    assert len(incoming) == 1
    assert incoming[0]["username"] == "explorer"

    # 5. Check lookup relationship status reflects pending state
    lookup_from_a = client.get("/api/v1/social/lookup?username=@bob_b").json()
    assert lookup_from_a["relationship_status"] == "outgoing_request"

    lookup_from_b = client_b.get("/api/v1/social/lookup?username=@explorer").json()
    assert lookup_from_b["relationship_status"] == "incoming_request"


def test_accept_friend_request_flow(client, db_session, make_user_client):
    user_b = User(
        name="Clara Oswald",
        email="clara@example.com",
        username="clara_o",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)
    client_b = make_user_client(user_b)

    # User A sends request to User B
    send_resp = client.post("/api/v1/social/friends", json={"friend_id": user_b.id})
    assert send_resp.status_code == 201
    friendship_id = send_resp.json()["id"]

    # User B accepts the request
    accept_resp = client_b.post(f"/api/v1/social/requests/{friendship_id}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"

    # Both users now appear in each other's friends list
    friends_a = client.get("/api/v1/social/friends").json()
    assert any(f["id"] == user_b.id and f["friendship_status"] == "accepted" for f in friends_a)

    friends_b = client_b.get("/api/v1/social/friends").json()
    assert any(f["username"] == "explorer" and f["friendship_status"] == "accepted" for f in friends_b)

    # Social profile is accessible and is_friend is True
    prof_resp = client.get(f"/api/v1/social/friends/{user_b.id}/profile")
    assert prof_resp.status_code == 200
    assert prof_resp.json()["is_friend"] is True

    # Lookup now shows 'friends'
    lookup = client.get("/api/v1/social/lookup?username=@clara_o").json()
    assert lookup["relationship_status"] == "friends"


def test_decline_friend_request_flow(client, db_session, make_user_client):
    user_b = User(
        name="David Smith",
        email="david@example.com",
        username="david_s",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)
    client_b = make_user_client(user_b)

    # User A sends request to David
    send_resp = client.post("/api/v1/social/friends", json={"username": "david_s"})
    friendship_id = send_resp.json()["id"]

    # David declines
    dec_resp = client_b.post(f"/api/v1/social/requests/{friendship_id}/decline")
    assert dec_resp.status_code == 204

    # Friendship record is deleted
    assert db_session.query(Friendship).filter(Friendship.id == friendship_id).first() is None

    # Neither user has incoming/outgoing or friends
    assert len(client_b.get("/api/v1/social/requests/incoming").json()) == 0
    assert len(client.get("/api/v1/social/requests/outgoing").json()) == 0
    assert not any(f["id"] == user_b.id for f in client.get("/api/v1/social/friends").json())


def test_cancel_outgoing_request_flow(client, db_session, make_user_client):
    user_b = User(
        name="Frank Castle",
        email="frank@example.com",
        username="frank_c",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)

    # User A sends request
    send_resp = client.post("/api/v1/social/friends", json={"username": "frank_c"})
    friendship_id = send_resp.json()["id"]

    # User A cancels their own outgoing request
    cancel_resp = client.delete(f"/api/v1/social/requests/{friendship_id}")
    assert cancel_resp.status_code == 204

    # Request deleted
    assert db_session.query(Friendship).filter(Friendship.id == friendship_id).first() is None


def test_mutual_request_auto_accept(client, db_session, make_user_client):
    user_b = User(
        name="Grace Hopper",
        email="grace@example.com",
        username="grace_h",
        is_active=True,
    )
    db_session.add(user_b)
    db_session.commit()
    db_session.refresh(user_b)
    client_b = make_user_client(user_b)

    # User A sends request to Grace (pending)
    send_a = client.post("/api/v1/social/friends", json={"username": "grace_h"})
    assert send_a.json()["status"] == "pending"

    # Grace sends request to User A -> automatically upgrades to accepted!
    send_b = client_b.post("/api/v1/social/friends", json={"username": "explorer"})
    assert send_b.json()["status"] == "accepted"

    # Both confirmed friends
    assert any(f["id"] == user_b.id for f in client.get("/api/v1/social/friends").json())
    assert any(f["username"] == "explorer" for f in client_b.get("/api/v1/social/friends").json())


def test_unauthorized_accept_prevented(client, db_session, make_user_client):
    user_b = User(
        name="Target B",
        email="tb@example.com",
        username="target_b",
        is_active=True,
    )
    user_c = User(
        name="Intruder C",
        email="tc@example.com",
        username="intruder_c",
        is_active=True,
    )
    db_session.add_all([user_b, user_c])
    db_session.commit()
    client_c = make_user_client(user_c)

    # User A sends request to User B
    send_resp = client.post("/api/v1/social/friends", json={"username": "target_b"})
    friendship_id = send_resp.json()["id"]

    # User C attempts to accept A's request to B -> 403 Forbidden!
    hack_resp = client_c.post(f"/api/v1/social/requests/{friendship_id}/accept")
    assert hack_resp.status_code == 403

    # User A (initiator) attempts to accept own request -> 403 Forbidden!
    self_accept = client.post(f"/api/v1/social/requests/{friendship_id}/accept")
    assert self_accept.status_code == 403
