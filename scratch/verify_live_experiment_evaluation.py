"""Live verification script demonstrating Phase 1: Time-bounded Experiment Measurement.

Demonstrates:
1. User has historical evidence (30+ days ago) with high delay (55 mins).
2. Experiment 1 becomes active (start_date: 2026-09-10, end_date: 2026-09-15).
3. Pre-experiment baseline window (2026-09-03 to 2026-09-09) captures 3 observations with avg delay 35 mins.
   Historical evidence (55 mins) is completely ignored and does not dilute baseline.
4. Experiment-period observations (2026-09-10, 11, 12) are created with avg delay 12 mins.
5. Evaluation calculates after_value (12 mins) strictly from the experiment window.
   Conclusion: positive (delay reduced by 23 mins, -65.7% shift).
6. Result is persisted in database and linked to experiment.
7. A second experiment with a different observation window (2026-09-20 to 2026-09-25) cannot
   reuse Experiment 1's observation data.
"""
import os
import sys
import json

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.core.security import create_access_token

TEST_DB_URL = "sqlite:///./scratch_verify_experiments.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def run_verification():
    session = SessionLocal()

    # Create dedicated verification user
    user = User(
        name="Verification User",
        email="verify_exp@focusloop.local",
        username="verify_exp_user",
        timezone="UTC",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(user_id=user.id)
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {token}"

    print("=" * 60)
    print("STEP 1: CREATING HISTORICAL EVIDENCE (30+ DAYS AGO)")
    print("=" * 60)
    # Create task
    t_resp = client.post("/api/v1/tasks", json={"name": "Deep Work Coding", "planned_time": "09:00"})
    task_id = t_resp.json()["id"]

    # 10 checkins from 40 days ago with heavy delay (55m)
    for i in range(10):
        client.post("/api/v1/checkins", json={
            "task_id": task_id,
            "date": f"2026-08-{10+i:02d}",
            "status": "done",
            "duration_minutes": 45,
            "start_delay_minutes": 55,
        })
    print(f"Created 10 historical checkins from August 2026 with 55m start delay.")

    print("\n" + "=" * 60)
    print("STEP 2: PRE-EXPERIMENT BASELINE EVIDENCE (7-DAY PRE-WINDOW)")
    print("=" * 60)
    # Baseline window for experiment starting 2026-09-10 is [2026-09-03 .. 2026-09-09]
    for d, del_min in [("2026-09-04", 35), ("2026-09-06", 35), ("2026-09-08", 35)]:
        client.post("/api/v1/checkins", json={
            "task_id": task_id,
            "date": d,
            "status": "done",
            "duration_minutes": 45,
            "start_delay_minutes": del_min,
        })
    print("Created 3 pre-experiment checkins (Sep 4, 6, 8) with 35m delay.")

    print("\n" + "=" * 60)
    print("STEP 3: CREATE & ACTIVATE EXPERIMENT 1")
    print("=" * 60)
    exp1_resp = client.post("/api/v1/experiments", json={
        "title": "5-Minute Initiation Gateway",
        "description": "Start immediately with 5-minute commitment",
        "hypothesis": "Low initiation barrier reduces delay",
        "start_date": "2026-09-10",
        "end_date": "2026-09-15",
        "target_metric": "average_start_delay_minutes",
    })
    exp1 = exp1_resp.json()
    exp1_id = exp1["id"]
    print(f"Experiment 1 created: ID={exp1_id}, status={exp1['status']}, start={exp1['start_date']}, end={exp1['end_date']}")

    print("\n" + "=" * 60)
    print("STEP 4: LOG EXPERIMENT-WINDOW OBSERVATIONS (SEP 10..15)")
    print("=" * 60)
    # Log 3 checkins during Experiment 1 with low delay (12m)
    for d, del_min in [("2026-09-10", 12), ("2026-09-12", 12), ("2026-09-14", 12)]:
        client.post("/api/v1/checkins", json={
            "task_id": task_id,
            "date": d,
            "status": "done",
            "duration_minutes": 45,
            "start_delay_minutes": del_min,
        })
    print("Created 3 observations during experiment (Sep 10, 12, 14) with 12m delay.")

    print("\n" + "=" * 60)
    print("STEP 5: EVALUATE EXPERIMENT 1")
    print("=" * 60)
    eval1_resp = client.post(f"/api/v1/experiments/{exp1_id}/evaluate")
    eval1 = eval1_resp.json()
    print("EVALUATION RESULT 1:")
    print(json.dumps(eval1, indent=2))
    assert eval1["before_value"] == 35.0, f"Expected before_value 35.0, got {eval1['before_value']}"
    assert eval1["after_value"] == 12.0, f"Expected after_value 12.0, got {eval1['after_value']}"
    assert eval1["change_value"] == -23.0
    assert eval1["percent_change"] == -65.7
    assert eval1["conclusion"] == "positive"
    print("-> VERIFIED: Baseline was 35.0 (NOT the 55m old history).")
    print("-> VERIFIED: After was 12.0 (strictly from Sep 10..15).")
    print("-> VERIFIED: Conclusion is positive (-65.7% shift).")

    print("\n" + "=" * 60)
    print("STEP 6: CREATE EXPERIMENT 2 WITH FUTURE WINDOW (SEP 20..25)")
    print("=" * 60)
    exp2_resp = client.post("/api/v1/experiments", json={
        "title": "Evening Scheduling Shift",
        "description": "Shift focus block to evening",
        "hypothesis": "Evening has higher focus",
        "start_date": "2026-09-20",
        "end_date": "2026-09-25",
        "target_metric": "average_start_delay_minutes",
    })
    exp2_id = exp2_resp.json()["id"]

    eval2_resp = client.post(f"/api/v1/experiments/{exp2_id}/evaluate")
    eval2 = eval2_resp.json()
    print("EVALUATION RESULT 2 (NO OBSERVATIONS IN SEP 20..25):")
    print(json.dumps(eval2, indent=2))
    assert eval2["after_value"] is None, f"Expected after_value None, got {eval2['after_value']}"
    assert eval2["conclusion"] == "inconclusive"
    print("-> VERIFIED: Experiment 2 CANNOT reuse Experiment 1's observations!")
    print("-> VERIFIED: after_value is None and conclusion is 'inconclusive' (zero data safety).")

    # Clean up scratch test db
    session.close()
    if os.path.exists("scratch_verify_experiments.db"):
        os.remove("scratch_verify_experiments.db")

    print("\n" + "=" * 60)
    print("ALL LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
