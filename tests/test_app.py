"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Test GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data


class TestSignup:
    """Test POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert "newstudent@mergington.edu" in chess_club["participants"]
    
    def test_signup_duplicate_email_returns_400(self, reset_activities):
        """Test that duplicate signup returns 400 error"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_returns_404(self, reset_activities):
        """Test that signup for non-existent activity returns 404 error"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestUnregister:
    """Test DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_participant_success(self, reset_activities):
        """Test successful unregistration from an activity"""
        # michael@mergington.edu is in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        chess_club = activities_response.json()["Chess Club"]
        assert "michael@mergington.edu" not in chess_club["participants"]
    
    def test_unregister_nonexistent_participant_returns_400(self, reset_activities):
        """Test that unregistering a non-existent participant returns 400 error"""
        response = client.delete(
            "/activities/Chess Club/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_returns_404(self, reset_activities):
        """Test that unregistering from non-existent activity returns 404 error"""
        response = client.delete(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestEdgeCases:
    """Test edge cases and workflows"""
    
    def test_signup_then_unregister_workflow(self, reset_activities):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/signup?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
    
    def test_multiple_signups_for_different_activities(self, reset_activities):
        """Test signing up for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for Tennis Club
        response1 = client.post(
            f"/activities/Tennis Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Tennis Club"]["participants"]
        assert email in data["Programming Class"]["participants"]
