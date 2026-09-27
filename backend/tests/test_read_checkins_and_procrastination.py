from datetime import datetime


def test_get_checkins_read_flow(client):
    # 1. Create a test task
    task_resp = client.post(
        "/api/v1/tasks",
        json={"name": "Algorithm Deep Work", "planned_time": "09:00", "category": "Focus"},
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # 2. Record a check-in
    checkin_create_payload = {
        "task_id": task_id,
        "date": "2026-09-26",
        "status": "done",
        "duration_minutes": 52,
        "start_delay_minutes": 4,
        "notes": "Finished graph search algorithm",
    }
    checkin_resp = client.post("/api/v1/checkins", json=checkin_create_payload)
    assert checkin_resp.status_code == 201
    created_checkin = checkin_resp.json()
    checkin_id = created_checkin["id"]

    # 3. Read check-in history via GET /api/v1/checkins
    history_resp = client.get("/api/v1/checkins")
    assert history_resp.status_code == 200
    checkin_list = history_resp.json()
    assert isinstance(checkin_list, list)
    assert len(checkin_list) >= 1

    # Verify that the created record is present with all required fields
    match = next((c for c in checkin_list if c["id"] == checkin_id), None)
    assert match is not None, "Created checkin should be present in GET /api/v1/checkins response"
    assert match["task_id"] == task_id
    assert match["date"] == "2026-09-26"
    assert match["status"] == "done"
    assert match["duration_minutes"] == 52
    assert match["start_delay_minutes"] == 4
    assert match["notes"] == "Finished graph search algorithm"
    assert "created_at" in match
    assert "user_id" in match

    # 4. Test optional filters supported by backend (date, task_id)
    date_filtered = client.get("/api/v1/checkins?date=2026-09-26").json()
    assert any(c["id"] == checkin_id for c in date_filtered)

    task_filtered = client.get(f"/api/v1/checkins?task_id={task_id}").json()
    assert any(c["id"] == checkin_id for c in task_filtered)


def test_get_procrastination_read_flow(client):
    # 1. Create a test task for context
    task_resp = client.post(
        "/api/v1/tasks",
        json={"name": "Report Drafting", "planned_time": "14:00"},
    )
    task_id = task_resp.json()["id"]

    # 2. Start a procrastination episode
    start_payload = {
        "task_id": task_id,
        "started_at": datetime.utcnow().isoformat(),
        "trigger_reason": "Mindful Delay Check",
        "notes": "Felt resistance to starting draft",
    }
    start_resp = client.post("/api/v1/procrastination/start", json=start_payload)
    assert start_resp.status_code == 201
    event_id = start_resp.json()["id"]

    # 3. End the episode
    end_payload = {
        "ended_at": datetime.utcnow().isoformat(),
        "trigger_reason": "Mindful Delay Check",
        "notes": "Ended pause after 2-minute reset",
    }
    end_resp = client.post(f"/api/v1/procrastination/{event_id}/end", json=end_payload)
    assert end_resp.status_code == 200
    ended_event = end_resp.json()
    assert ended_event["id"] == event_id
    assert ended_event["ended_at"] is not None

    # 4. Read historical episodes via GET /api/v1/procrastination
    history_resp = client.get("/api/v1/procrastination")
    assert history_resp.status_code == 200
    events_list = history_resp.json()
    assert isinstance(events_list, list)
    assert len(events_list) >= 1

    # Verify that the ended event is present with all required fields
    match = next((e for e in events_list if e["id"] == event_id), None)
    assert match is not None, "Ended event should be present in GET /api/v1/procrastination response"
    assert match["task_id"] == task_id
    assert match["user_confirmed"] is True
    assert match["trigger_reason"] == "Mindful Delay Check"
    assert match["notes"] == "Ended pause after 2-minute reset"
    assert match["started_at"] is not None
    assert match["ended_at"] is not None
    assert "duration_seconds" in match
    assert "id" in match
    assert "user_id" in match
