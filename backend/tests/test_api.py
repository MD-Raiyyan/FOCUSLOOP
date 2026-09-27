from datetime import datetime, timedelta


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "FocusLoop" in data["project"]


def test_users_api(client):
    # Test getting default user
    me_resp = client.get("/api/v1/users/me")
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert "id" in user_data
    assert user_data["name"] == "FocusLoop Explorer"

    # Test creating custom user
    create_resp = client.post(
        "/api/v1/users",
        json={"name": "Alex", "email": "alex@example.com", "timezone": "America/New_York"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["name"] == "Alex"


def test_tasks_crud(client):
    # 1. Create a task
    create_resp = client.post(
        "/api/v1/tasks",
        json={
            "name": "Write Thesis Intro",
            "description": "Draft the background section",
            "category": "Deep Work",
            "planned_time": "10:00",
            "target_duration_minutes": "45",
            "frequency": "daily",
        },
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    task_id = task["id"]
    assert task["name"] == "Write Thesis Intro"

    # 2. Get tasks list
    list_resp = client.get("/api/v1/tasks")
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert any(t["id"] == task_id for t in tasks)

    # 3. Update task
    update_resp = client.put(f"/api/v1/tasks/{task_id}", json={"name": "Write Thesis Abstract"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Write Thesis Abstract"

    # 4. Delete task
    del_resp = client.delete(f"/api/v1/tasks/{task_id}")
    assert del_resp.status_code == 204


def test_checkins_and_procrastination_flow(client):
    # Create task first
    task_resp = client.post(
        "/api/v1/tasks",
        json={"name": "Evening Review", "planned_time": "19:00"},
    )
    task_id = task_resp.json()["id"]

    # 1. Log a Procrastination session
    proc_resp = client.post(
        "/api/v1/procrastination/start",
        json={
            "task_id": task_id,
            "trigger_reason": "feeling overwhelmed",
            "notes": "Opened phone instinctively",
        },
    )
    assert proc_resp.status_code == 201
    event = proc_resp.json()
    event_id = event["id"]

    # End procrastination session
    end_resp = client.post(
        f"/api/v1/procrastination/{event_id}/end",
        json={"trigger_reason": "felt ready after small breath"},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["id"] == event_id

    # 2. Record checkin
    checkin_resp = client.post(
        "/api/v1/checkins",
        json={
            "task_id": task_id,
            "date": "2026-09-25",
            "status": "done",
            "duration_minutes": 25,
            "start_delay_minutes": 15,
            "notes": "Finished after short delay",
        },
    )
    assert checkin_resp.status_code == 201
    assert checkin_resp.json()["status"] == "done"

    # 3. Ingest screen usage
    screen_resp = client.post(
        "/api/v1/screen-usage",
        json={
            "app_identifier": "com.instagram.android",
            "app_name": "Instagram",
            "category": "Social",
            "started_at": datetime.utcnow().isoformat(),
            "ended_at": (datetime.utcnow() + timedelta(minutes=12)).isoformat(),
            "duration_seconds": 720,
        },
    )
    assert screen_resp.status_code == 201


def test_behavior_engine_and_experiments(client):
    # Create a task and checkin
    task = client.post("/api/v1/tasks", json={"name": "Morning Code", "planned_time": "09:00"}).json()
    client.post(
        "/api/v1/checkins",
        json={
            "task_id": task["id"],
            "date": "2026-09-25",
            "status": "done",
            "duration_minutes": 40,
            "start_delay_minutes": 5,
        },
    )

    # Behavior summary
    summary_resp = client.get("/api/v1/behavior/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert "completion_rate" in summary
    assert "average_start_delay_minutes" in summary

    # Suggest experiments
    sugg_resp = client.post("/api/v1/experiments/suggest")
    assert sugg_resp.status_code == 200
    experiments = sugg_resp.json()
    assert len(experiments) > 0

    exp_id = experiments[0]["id"]

    # Activate experiment first (only active experiments can be evaluated)
    activate_resp = client.put(f"/api/v1/experiments/{exp_id}", json={"status": "active"})
    assert activate_resp.status_code == 200

    # Evaluate experiment
    eval_resp = client.post(f"/api/v1/experiments/{exp_id}/evaluate")
    assert eval_resp.status_code == 200
    result = eval_resp.json()
    assert "metric_name" in result
    assert "conclusion" in result


def test_ai_explanation_endpoint(client):
    resp = client.post(
        "/api/v1/chat/explain",
        json={"question": "Why do I feel sluggish in the afternoon?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "explanation" in data
    assert "deterministic_context" in data
    assert data["tone"] == "compassionate_analytical"
