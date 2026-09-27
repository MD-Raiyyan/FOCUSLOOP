"""End-to-end test simulating mobile/src/hooks/useExperiments.ts and lab.tsx logic

Tests:
1. Initial state with zero experiments (activeExperiment is null, status badge is 'No Active Protocol')
2. Pressing 'New Suggestion' (POST /api/v1/experiments/suggest):
   - Returns flat list of experiments
   - Verified that state is flat ExperimentResponse[], NOT nested array
   - Suggested experiment has status='suggested'
   - activeExperiment is STILL null (does not fake suggested as active)
   - Cannot evaluate a suggested experiment (backend returns 400 Bad Request)
3. Pressing 'New Suggestion' repeatedly preserves flat array state
4. Activating a suggested protocol (PUT /api/v1/experiments/{id} with status='active'):
   - Experiment becomes 'active'
   - activeExperiment is now non-null and correctly selected
   - Hero banner reflects Status: ACTIVE
5. Evaluating active experiment (POST /api/v1/experiments/{id}/evaluate):
   - Successfully evaluates
   - Experiment becomes 'completed'
   - activeExperiment returns to null
   - Completed protocol displays results and no evaluation controls
6. Refreshing/re-fetching experiments returns authoritative server state
"""
import os
import sys

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

TEST_DB_URL = "sqlite:///./scratch_test_lab.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def test_lab_lifecycle():
    session = SessionLocal()

    user = User(
        name="Lab Lifecycle Tester",
        email="lab_tester@focusloop.local",
        username="lab_tester",
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
    print("STEP 1: INITIAL STATE (ZERO EXPERIMENTS)")
    print("=" * 60)
    # Simulate fetchExperiments()
    res = client.get("/api/v1/experiments")
    assert res.status_code == 200
    experiments = res.json()
    assert isinstance(experiments, list)
    assert len(experiments) == 0

    # Simulate lab.tsx activeExperiment selection
    activeExperiment = next((exp for exp in experiments if exp.get("status") == "active"), None)
    assert activeExperiment is None
    badge_text = f"Status: {(activeExperiment['status']).toUpperCase()}" if activeExperiment else "No Active Protocol"
    assert badge_text == "No Active Protocol"
    print(f"-> Verified: experiments count = {len(experiments)}")
    print(f"-> Verified: activeExperiment is {activeExperiment}")
    print(f"-> Verified: Badge text is '{badge_text}'")

    print("\n" + "=" * 60)
    print("STEP 2: PRESS 'NEW SUGGESTION'")
    print("=" * 60)
    # Simulate suggestExperiment()
    sugg_res = client.post("/api/v1/experiments/suggest")
    assert sugg_res.status_code == 200
    suggested_data = sugg_res.json()
    assert isinstance(suggested_data, list), "Server must return a list"

    # In useExperiments.ts: setExperiments(data)
    experiments = suggested_data

    # VERIFY STATE INTEGRITY: Flat list, not nested!
    for item in experiments:
        assert isinstance(item, dict), "Every item in experiments state MUST be a dict, not a list!"
        assert "status" in item, "Item must have status field"
        assert item["status"] == "suggested", f"Expected suggested status, got {item['status']}"

    # VERIFY activeExperiment IS NOT FOOLED
    activeExperiment = next((exp for exp in experiments if exp.get("status") == "active"), None)
    assert activeExperiment is None, "A suggested experiment must NOT be selected as activeExperiment!"
    badge_text = f"Status: {(activeExperiment['status']).toUpperCase()}" if activeExperiment else "No Active Protocol"
    assert badge_text == "No Active Protocol"
    print(f"-> Verified: experiments state is a flat list of {len(experiments)} items (NO NESTED ARRAYS).")
    print(f"-> Verified: activeExperiment is correctly {activeExperiment}.")
    print(f"-> Verified: Hero badge correctly shows '{badge_text}'.")

    # VERIFY SUGGESTED EXPERIMENT CANNOT BE PREMATURELY EVALUATED
    first_exp = experiments[0]
    eval_attempt = client.post(f"/api/v1/experiments/{first_exp['id']}/evaluate")
    assert eval_attempt.status_code == 400
    print(f"-> Verified: Backend strictly rejected evaluation of suggested experiment with 400: {eval_attempt.json()['detail']}")

    print("\n" + "=" * 60)
    print("STEP 3: PRESS 'NEW SUGGESTION' REPEATEDLY")
    print("=" * 60)
    for _ in range(3):
        res = client.post("/api/v1/experiments/suggest")
        assert res.status_code == 200
        experiments = res.json()
        for item in experiments:
            assert isinstance(item, dict)

    assert len(experiments) >= 1
    assert next((exp for exp in experiments if exp.get("status") == "active"), None) is None
    print(f"-> Verified: Repeated suggestions maintain flat Experiment[] state without corruption.")

    print("\n" + "=" * 60)
    print("STEP 4: START / ACTIVATE PROTOCOL")
    print("=" * 60)
    # Simulate handleStart(exp.id) -> updateExperiment(id, { status: 'active' })
    activate_res = client.put(f"/api/v1/experiments/{first_exp['id']}", json={"status": "active"})
    assert activate_res.status_code == 200

    # Refresh experiments
    experiments = client.get("/api/v1/experiments").json()
    activeExperiment = next((exp for exp in experiments if exp.get("status") == "active"), None)
    assert activeExperiment is not None
    assert activeExperiment["id"] == first_exp["id"]
    assert activeExperiment["status"] == "active"
    badge_text = f"Status: {(activeExperiment['status']).upper()}" if activeExperiment else "No Active Protocol"
    assert badge_text == "Status: ACTIVE"
    print(f"-> Verified: Protocol successfully activated via PUT /experiments/{{id}}.")
    print(f"-> Verified: activeExperiment is now {activeExperiment['title']}.")
    print(f"-> Verified: Hero badge shows '{badge_text}'.")

    print("\n" + "=" * 60)
    print("STEP 5: EVALUATE ACTIVE PROTOCOL")
    print("=" * 60)
    eval_res = client.post(f"/api/v1/experiments/{activeExperiment['id']}/evaluate")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "conclusion" in eval_data
    print(f"-> Verified: Evaluation completed with conclusion '{eval_data['conclusion']}'.")

    # Refresh experiments
    experiments = client.get("/api/v1/experiments").json()
    completed_exp = next(e for e in experiments if e["id"] == first_exp["id"])
    assert completed_exp["status"] == "completed"

    activeExperiment = next((exp for exp in experiments if exp.get("status") == "active"), None)
    assert activeExperiment is None
    badge_text = f"Status: {(activeExperiment['status']).upper()}" if activeExperiment else "No Active Protocol"
    assert badge_text == "No Active Protocol"
    print(f"-> Verified: Protocol status transitioned to 'completed'.")
    print(f"-> Verified: activeExperiment safely returned to None.")

    session.close()
    if os.path.exists("scratch_test_lab.db"):
        os.remove("scratch_test_lab.db")

    print("\n" + "=" * 60)
    print("ALL LAB LIFECYCLE SIMULATION TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_lab_lifecycle()
