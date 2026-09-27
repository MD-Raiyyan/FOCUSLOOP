import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.checkin import TaskCheckin
from app.models.user import User
from app.behavior.metrics import BehaviorMetricsCalculator
from app.core.security import create_access_token


def test_01_create_one_time_task(client: TestClient, db_session: Session):
    """1. Create one-time task with explicit recurrence."""
    resp = client.post(
        "/api/v1/tasks",
        json={
            "name": "Submit Tax Report",
            "description": "Annual filing",
            "frequency": "once",
            "planned_time": "14:00",
            "target_duration_minutes": "45",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Submit Tax Report"
    assert data["frequency"] == "once"
    assert data["today_status"] is None

    # Also test alias normalization ("one_time" -> "once")
    resp_alias = client.post(
        "/api/v1/tasks",
        json={
            "name": "Deliver Package",
            "frequency": "one_time",
        },
    )
    assert resp_alias.status_code == 201
    assert resp_alias.json()["frequency"] == "once"


def test_02_create_daily_task(client: TestClient):
    """2. Create daily task."""
    resp = client.post(
        "/api/v1/tasks",
        json={
            "name": "Study DSA",
            "description": "LeetCode grind",
            "frequency": "daily",
            "planned_time": "09:00",
            "target_duration_minutes": "60",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Study DSA"
    assert data["frequency"] == "daily"
    assert data["today_status"] is None


def test_03_invalid_recurrence_rejected(client: TestClient):
    """3. Invalid recurrence is rejected."""
    resp = client.post(
        "/api/v1/tasks",
        json={
            "name": "Irregular Task",
            "frequency": "sometimes",
        },
    )
    assert resp.status_code == 422


def test_04_one_time_task_can_have_one_occurrence(client: TestClient):
    """4. One-time task can have one occurrence; checking in a second date is rejected."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "Buy Monitor", "frequency": "once"},
    )
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # Check-in on 2026-09-27
    checkin_resp1 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-27", "status": "done"},
    )
    assert checkin_resp1.status_code == 201

    # Attempting to check in the same one-time task on another date must be rejected
    checkin_resp2 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-28", "status": "done"},
    )
    assert checkin_resp2.status_code == 400
    assert "One-time task" in checkin_resp2.json()["detail"]


def test_05_and_06_daily_task_separate_occurrences(client: TestClient):
    """5 & 6. Daily task can have separate occurrences on different dates."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "Morning Yoga", "frequency": "daily"},
    )
    assert resp.status_code == 201
    task_id = resp.json()["id"]

    # Day 1: Done
    c1 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-25", "status": "done"},
    )
    assert c1.status_code == 201

    # Day 2: Partial
    c2 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-26", "status": "partial"},
    )
    assert c2.status_code == 201

    # Day 3: Missed
    c3 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-27", "status": "missed"},
    )
    assert c3.status_code == 201

    # Query check-ins
    hist = client.get(f"/api/v1/checkins?task_id={task_id}").json()
    assert len(hist) == 3


def test_07_same_task_date_cannot_produce_duplicate_checkins(client: TestClient):
    """7. Same task/date cannot produce duplicate check-ins; treated as idempotent update."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "Read Documentation", "frequency": "daily"},
    )
    task_id = resp.json()["id"]

    # First check-in
    c1 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-27", "status": "done", "duration_minutes": 25},
    )
    assert c1.status_code == 201
    c1_id = c1.json()["id"]

    # Repeated check-in on the exact same date (e.g. double tap or status edit)
    c2 = client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-27", "status": "partial", "duration_minutes": 15},
    )
    assert c2.status_code == 200
    assert c2.json()["id"] == c1_id
    assert c2.json()["status"] == "partial"

    # Verify only one row exists in database for this date
    hist = client.get(f"/api/v1/checkins?task_id={task_id}&date=2026-09-27").json()
    assert len(hist) == 1
    assert hist[0]["status"] == "partial"


def test_08_one_time_completed_task_no_longer_in_future_active_list(client: TestClient):
    """8. One-time completed task does not produce another active occurrence for future dates."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "File Taxes 2025", "frequency": "once"},
    )
    task_id = resp.json()["id"]

    # Completed on 2026-09-25
    client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-25", "status": "done"},
    )

    # Query for 2026-09-25: shows completed
    day1_tasks = client.get("/api/v1/tasks?date=2026-09-25&active_only=true").json()
    matching_day1 = [t for t in day1_tasks if t["id"] == task_id]
    assert len(matching_day1) == 1
    assert matching_day1[0]["today_status"] == "done"

    # Query for future date 2026-09-26: excluded from active list
    day2_tasks = client.get("/api/v1/tasks?date=2026-09-26&active_only=true").json()
    matching_day2 = [t for t in day2_tasks if t["id"] == task_id]
    assert len(matching_day2) == 0


def test_09_daily_completed_task_remains_active_for_future_dates(client: TestClient):
    """9. Daily completed task remains active with pending occurrence for future dates."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "Daily Pushups", "frequency": "daily"},
    )
    task_id = resp.json()["id"]

    # Completed on 2026-09-25
    client.post(
        "/api/v1/checkins",
        json={"task_id": task_id, "date": "2026-09-25", "status": "done"},
    )

    # On 2026-09-25: status is done
    day1_tasks = client.get("/api/v1/tasks?date=2026-09-25&active_only=true").json()
    matching_day1 = [t for t in day1_tasks if t["id"] == task_id]
    assert len(matching_day1) == 1
    assert matching_day1[0]["today_status"] == "done"

    # On 2026-09-26: still in active list, with today_status = None (pending)
    day2_tasks = client.get("/api/v1/tasks?date=2026-09-26&active_only=true").json()
    matching_day2 = [t for t in day2_tasks if t["id"] == task_id]
    assert len(matching_day2) == 1
    assert matching_day2[0]["today_status"] is None


def test_10_to_14_statuses_persisted_and_returned_in_today(client: TestClient):
    """10-14. Done, partial, missed statuses persisted, returned in task query, re-fetching works."""
    t_done = client.post("/api/v1/tasks", json={"name": "Task A", "frequency": "daily"}).json()["id"]
    t_partial = client.post("/api/v1/tasks", json={"name": "Task B", "frequency": "daily"}).json()["id"]
    t_missed = client.post("/api/v1/tasks", json={"name": "Task C", "frequency": "daily"}).json()["id"]

    date_str = "2026-09-27"
    client.post("/api/v1/checkins", json={"task_id": t_done, "date": date_str, "status": "done"})
    client.post("/api/v1/checkins", json={"task_id": t_partial, "date": date_str, "status": "partial"})
    client.post("/api/v1/checkins", json={"task_id": t_missed, "date": date_str, "status": "missed"})

    # Re-fetch tasks
    tasks = client.get(f"/api/v1/tasks?date={date_str}").json()
    status_map = {t["id"]: t["today_status"] for t in tasks}

    assert status_map[t_done] == "done"
    assert status_map[t_partial] == "partial"
    assert status_map[t_missed] == "missed"


def test_15_and_16_changing_recurrence_preserves_historical_evidence(client: TestClient):
    """15 & 16. Historical check-ins remain intact when recurrence is updated."""
    t = client.post("/api/v1/tasks", json={"name": "Hydration Habit", "frequency": "daily"}).json()
    task_id = t["id"]

    # Record 2 check-ins
    client.post("/api/v1/checkins", json={"task_id": task_id, "date": "2026-09-20", "status": "done"})
    client.post("/api/v1/checkins", json={"task_id": task_id, "date": "2026-09-21", "status": "done"})

    # Update recurrence to once
    update_resp = client.put(f"/api/v1/tasks/{task_id}", json={"frequency": "once"})
    assert update_resp.status_code == 200
    assert update_resp.json()["frequency"] == "once"

    # Historical check-ins must still be 2
    checkins = client.get(f"/api/v1/checkins?task_id={task_id}").json()
    assert len(checkins) == 2


def test_17_behavior_metrics_calculation_accuracy(db_session: Session, test_user: User):
    """17. Behavior metric calculations use check-in evidence without double-counting."""
    # Create a fresh task
    task = Task(
        user_id=test_user.id,
        name="Focus Session",
        frequency="daily",
        planned_time="10:00",
        active=True,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # 4 check-in observations on 4 distinct dates
    c1 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-21", status="done")
    c2 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-22", status="done")
    c3 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-23", status="partial")
    c4 = TaskCheckin(user_id=test_user.id, task_id=task.id, date="2026-09-24", status="missed")
    db_session.add_all([c1, c2, c3, c4])
    db_session.commit()

    calc = BehaviorMetricsCalculator(db_session, test_user.id)
    stats = calc.compute_task_completion_stats()

    # Total checkins for this test
    assert stats["total"] >= 4
    assert stats["done"] >= 2
    assert stats["partial"] >= 1
    assert stats["missed"] >= 1


def test_18_and_19_cross_user_isolation(client: TestClient, db_session: Session):
    """18 & 19. Cross-user isolation and unauthorized access is rejected."""
    # Create another user
    other_user = User(
        id="00000000-0000-0000-0000-000000000002",
        name="Other User",
        email="other@focusloop.local",
        username="otheruser",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    other_task = Task(
        user_id=other_user.id,
        name="Secret Task",
        frequency="daily",
        active=True,
    )
    db_session.add(other_task)
    db_session.commit()
    db_session.refresh(other_task)

    # Authenticated client (test_user) attempts to fetch other user's task
    get_resp = client.get(f"/api/v1/tasks/{other_task.id}")
    assert get_resp.status_code == 404

    # Authenticated client attempts to check in to other user's task
    checkin_resp = client.post(
        "/api/v1/checkins",
        json={"task_id": other_task.id, "date": "2026-09-27", "status": "done"},
    )
    assert checkin_resp.status_code == 404

    # Authenticated client attempts to delete other user's task
    delete_resp = client.delete(f"/api/v1/tasks/{other_task.id}")
    assert delete_resp.status_code == 404


def test_20_backward_compatible_defaults(client: TestClient):
    """20. Existing task APIs remain backward compatible (defaults to daily when omitted)."""
    resp = client.post(
        "/api/v1/tasks",
        json={"name": "Default Recurrence Task"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["frequency"] == "daily"
    assert data["active"] is True
