import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# Keep an original snapshot so tests can restore state
ORIGINAL = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def restore_activities():
    # Before each test - restore the in-memory activities dict
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL))
    yield
    # After test - restore again (defensive)
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL))


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # spot-check a few known activities
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_and_prevent_duplicate():
    activity = "Chess Club"
    email = "tester@school.edu"

    # Sign up should succeed
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email in activities[activity]["participants"]

    # Signing up the same email again should fail with 400
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp2.status_code == 400
    body = resp2.json()
    assert "already signed up" in body.get("detail", "").lower()

    # Ensure the participant only appears once
    assert activities[activity]["participants"].count(email) == 1


def test_unregister_existing_and_nonexistent():
    activity = "Chess Club"
    # michael@mergington.edu is in the initial data
    email = "michael@mergington.edu"

    # Unregister existing participant
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert email not in activities[activity]["participants"]

    # Unregistering again should return 400
    resp2 = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert resp2.status_code == 400
    body = resp2.json()
    assert "not signed up" in body.get("detail", "").lower()
