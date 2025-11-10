"""
Tests for the FastAPI application endpoints.
"""
import pytest
from fastapi import status


class TestRootEndpoint:
    """Test cases for the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test cases for the activities endpoint."""

    def test_get_activities_success(self, client):
        """Test successful retrieval of activities."""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities

    def test_activities_structure(self, client):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] == 12

    def test_activities_initial_participants(self, client):
        """Test that activities have initial participants."""
        response = client.get("/activities")
        activities = response.json()
        
        chess_participants = activities["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupEndpoint:
    """Test cases for the signup endpoint."""

    def test_signup_success(self, client, sample_email, sample_activity):
        """Test successful signup for an activity."""
        response = client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert sample_email in result["message"]
        assert sample_activity in result["message"]

    def test_signup_adds_participant(self, client, sample_email, sample_activity):
        """Test that signup actually adds participant to the activity."""
        # Signup
        client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        participants = activities[sample_activity]["participants"]
        assert sample_email in participants

    def test_signup_duplicate_participant(self, client, sample_activity):
        """Test that duplicate signup is prevented."""
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(f"/activities/{sample_activity}/signup?email={existing_email}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_nonexistent_activity(self, client, sample_email):
        """Test signup for non-existent activity returns 404."""
        response = client.post(f"/activities/Nonexistent Activity/signup?email={sample_email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_signup_url_encoded_activity_name(self, client, sample_email):
        """Test signup with URL-encoded activity name."""
        activity_name = "Programming Class"
        encoded_name = "Programming%20Class"
        
        response = client.post(f"/activities/{encoded_name}/signup?email={sample_email}")
        assert response.status_code == status.HTTP_200_OK

    def test_signup_multiple_different_participants(self, client, sample_activity):
        """Test signing up multiple different participants."""
        emails = ["test1@mergington.edu", "test2@mergington.edu", "test3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/{sample_activity}/signup?email={email}")
            assert response.status_code == status.HTTP_200_OK
        
        # Verify all participants were added
        response = client.get("/activities")
        activities = response.json()
        participants = activities[sample_activity]["participants"]
        
        for email in emails:
            assert email in participants


class TestUnregisterEndpoint:
    """Test cases for the unregister endpoint."""

    def test_unregister_success(self, client, sample_activity):
        """Test successful unregistration from an activity."""
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(f"/activities/{sample_activity}/unregister?email={existing_email}")
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "message" in result
        assert existing_email in result["message"]
        assert sample_activity in result["message"]

    def test_unregister_removes_participant(self, client, sample_activity):
        """Test that unregister actually removes participant from the activity."""
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # Unregister
        client.delete(f"/activities/{sample_activity}/unregister?email={existing_email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        participants = activities[sample_activity]["participants"]
        assert existing_email not in participants

    def test_unregister_participant_not_registered(self, client, sample_activity, sample_email):
        """Test unregistering participant who isn't registered."""
        response = client.delete(f"/activities/{sample_activity}/unregister?email={sample_email}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        result = response.json()
        assert "not signed up" in result["detail"].lower()

    def test_unregister_nonexistent_activity(self, client, sample_email):
        """Test unregister from non-existent activity returns 404."""
        response = client.delete(f"/activities/Nonexistent Activity/unregister?email={sample_email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_signup_then_unregister_cycle(self, client, sample_email, sample_activity):
        """Test complete cycle of signup and unregister."""
        # Sign up
        signup_response = client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        assert signup_response.status_code == status.HTTP_200_OK
        
        # Verify signup
        response = client.get("/activities")
        activities = response.json()
        assert sample_email in activities[sample_activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{sample_activity}/unregister?email={sample_email}")
        assert unregister_response.status_code == status.HTTP_200_OK
        
        # Verify unregister
        response = client.get("/activities")
        activities = response.json()
        assert sample_email not in activities[sample_activity]["participants"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_email_format(self, client, sample_activity):
        """Test signup with invalid email format."""
        invalid_email = "not-an-email"
        response = client.post(f"/activities/{sample_activity}/signup?email={invalid_email}")
        # Note: FastAPI doesn't validate email format by default, so this should still work
        assert response.status_code == status.HTTP_200_OK

    def test_empty_email(self, client, sample_activity):
        """Test signup with empty email."""
        response = client.post(f"/activities/{sample_activity}/signup?email=")
        # Should still work since we don't have email validation
        assert response.status_code == status.HTTP_200_OK

    def test_special_characters_in_email(self, client, sample_activity):
        """Test signup with special characters in email."""
        special_email = "test+special@mergington.edu"
        response = client.post(f"/activities/{sample_activity}/signup?email={special_email}")
        assert response.status_code == status.HTTP_200_OK

    def test_case_sensitivity_activity_names(self, client, sample_email):
        """Test that activity names are case sensitive."""
        # Should fail with different case
        response = client.post(f"/activities/chess club/signup?email={sample_email}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_participant_count_consistency(self, client, sample_email, sample_activity):
        """Test that participant count remains consistent."""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[sample_activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        
        # Check count increased
        response = client.get("/activities")
        new_count = len(response.json()[sample_activity]["participants"])
        assert new_count == initial_count + 1
        
        # Unregister
        client.delete(f"/activities/{sample_activity}/unregister?email={sample_email}")
        
        # Check count back to original
        response = client.get("/activities")
        final_count = len(response.json()[sample_activity]["participants"])
        assert final_count == initial_count

    def test_multiple_activities_independence(self, client, sample_email):
        """Test that operations on one activity don't affect others."""
        # Sign up for Chess Club
        client.post(f"/activities/Chess Club/signup?email={sample_email}")
        
        # Check that Programming Class is unaffected
        response = client.get("/activities")
        activities = response.json()
        
        assert sample_email in activities["Chess Club"]["participants"]
        assert sample_email not in activities["Programming Class"]["participants"]
        assert sample_email not in activities["Gym Class"]["participants"]