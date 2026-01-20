import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


class TestActivitiesEndpoints:
    """Test suite for activities endpoints"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"

    def test_get_activities_participants(self):
        """Test that activities include participants"""
        response = client.get("/activities")
        data = response.json()
        assert "participants" in data["Chess Club"]
        assert isinstance(data["Chess Club"]["participants"], list)
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_for_activity_success(self):
        """Test successfully signing up for an activity"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        # Verify participant was added
        assert email in activities["Chess Club"]["participants"]

    def test_signup_already_registered(self):
        """Test signing up when already registered"""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            f"/activities/NonExistent%20Club/signup?email=test@mergington.edu",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_success(self):
        """Test successfully unregistering from an activity"""
        email = "michael@mergington.edu"
        # First verify they are registered
        activities_before = client.get("/activities").json()
        assert email in activities_before["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        
        # Verify participant was removed
        activities_after = client.get("/activities").json()
        assert email not in activities_after["Chess Club"]["participants"]

    def test_unregister_not_registered(self):
        """Test unregistering when not registered"""
        response = client.post(
            f"/activities/Chess%20Club/unregister?email=notregistered@mergington.edu",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            f"/activities/NonExistent%20Club/unregister?email=test@mergington.edu",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestActivityData:
    """Test suite for activity data structure"""

    def test_all_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        for activity_name, activity in activities_data.items():
            for field in required_fields:
                assert field in activity, f"{activity_name} missing field: {field}"

    def test_participant_count_valid(self):
        """Test that participant count doesn't exceed max"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity in activities_data.items():
            assert len(activity["participants"]) <= activity["max_participants"], \
                f"{activity_name} has too many participants"

    def test_participants_are_emails(self):
        """Test that all participants have valid email format"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity in activities_data.items():
            for participant in activity["participants"]:
                assert "@" in participant, f"Invalid email: {participant}"
                assert "." in participant.split("@")[1], f"Invalid email domain: {participant}"
