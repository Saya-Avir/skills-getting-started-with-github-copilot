import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def snapshot_activities():
    """Snapshot and restore module-level activities to keep tests isolated."""
    original = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original)


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    # Arrange
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert {"description", "schedule", "max_participants", "participants"}.issubset(
        set(data["Chess Club"].keys())
    )


def test_signup_success(client):
    # Arrange
    activity = "Chess Club"
    email = "newstudent@example.com"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    response = client.post(f"/activities/{quote(activity, safe='')}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity]["participants"]
    assert response.json() == {"message": f"Signed up {email} for {activity}"}


def test_signup_duplicate(client):
    # Arrange
    activity = "Chess Club"
    existing = app_module.activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{quote(activity, safe='')}/signup", params={"email": existing})

    # Assert
    assert response.status_code == 400
    assert "detail" in response.json()


def test_signup_activity_not_found(client):
    # Arrange
    activity = "NoSuchClub"
    email = "someone@example.com"

    # Act
    response = client.post(f"/activities/{quote(activity, safe='')}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_remove_participant_success(client):
    # Arrange
    activity = "Programming Class"
    email = app_module.activities[activity]["participants"][0]
    assert email in app_module.activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{quote(activity, safe='')}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity]["participants"]
    assert response.json() == {"message": f"Removed {email} from {activity}"}


def test_remove_participant_not_member(client):
    # Arrange
    activity = "Programming Class"
    email = "not.member@example.com"
    if email in app_module.activities[activity]["participants"]:
        app_module.activities[activity]["participants"].remove(email)

    # Act
    response = client.delete(f"/activities/{quote(activity, safe='')}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_remove_from_nonexistent_activity(client):
    # Arrange
    activity = "NoClub"
    email = "someone@example.com"

    # Act
    response = client.delete(f"/activities/{quote(activity, safe='')}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
