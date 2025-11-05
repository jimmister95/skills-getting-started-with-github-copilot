from copy import deepcopy
try:
    import pytest  # type: ignore
except Exception:
    # Minimal fallback so editors/linters without pytest won't error;
    # the fixture decorator simply returns the original function.
    class _PytestFallback:
        def fixture(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = _PytestFallback()

from fastapi.testclient import TestClient

import src.app as app_mod


@pytest.fixture(autouse=True)
def reset_activities():
    # Preserve original activities and restore after each test to avoid cross-test pollution
    original = deepcopy(app_mod.activities)
    yield
    app_mod.activities.clear()
    app_mod.activities.update(original)


@pytest.fixture()
def client():
    return TestClient(app_mod.app)


def test_get_activities(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    # Ensure a known activity exists
    assert "Chess Club" in data


def test_signup_and_unregister(client):
    email = "teststudent@mergington.edu"
    activity = "Chess Club"

    # Ensure email not present initially
    res = client.get("/activities")
    assert email not in res.json()[activity]["participants"]

    # Sign up
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    assert "Signed up" in res.json().get("message", "")

    # Verify present
    res = client.get("/activities")
    assert email in res.json()[activity]["participants"]

    # Unregister
    res = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    assert "Removed" in res.json().get("message", "")

    # Verify removed
    res = client.get("/activities")
    assert email not in res.json()[activity]["participants"]


def test_duplicate_signup_returns_400(client):
    email = "dup@mergington.edu"
    activity = "Programming Class"

    # First signup ok
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200

    # Second signup should fail
    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 400


def test_unregister_nonexistent_returns_404(client):
    email = "noone@mergington.edu"
    activity = "Gym Class"

    # Ensure not present
    res = client.get("/activities")
    assert email not in res.json()[activity]["participants"]

    # Attempt to remove
    res = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 404