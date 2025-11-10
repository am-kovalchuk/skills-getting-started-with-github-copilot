"""
Test to verify proper test isolation with deep copy.
"""
import pytest
from src.app import activities


class TestTestIsolation:
    """Test cases to verify that tests are properly isolated."""

    def test_participant_list_isolation_first(self, client):
        """Test that modifies participant list - should not affect other tests."""
        # Add a participant to Chess Club
        response = client.post("/activities/Chess Club/signup?email=isolation_test1@test.com")
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        activities_data = response.json()
        assert "isolation_test1@test.com" in activities_data["Chess Club"]["participants"]
        
        # Check initial count
        chess_participants = activities_data["Chess Club"]["participants"]
        assert len(chess_participants) >= 3  # Initial 2 + our addition

    def test_participant_list_isolation_second(self, client):
        """Test that should start with fresh data despite previous test modifications."""
        # This test should start with fresh participant lists
        response = client.get("/activities")
        activities_data = response.json()
        
        # Should only have the initial participants, not the ones from previous test
        chess_participants = activities_data["Chess Club"]["participants"]
        assert "isolation_test1@test.com" not in chess_participants
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2  # Only initial participants

    def test_multiple_activity_isolation(self, client):
        """Test that modifications to multiple activities are isolated."""
        # Modify multiple activities
        client.post("/activities/Chess Club/signup?email=multi_test1@test.com")
        client.post("/activities/Programming Class/signup?email=multi_test2@test.com")
        client.post("/activities/Gym Class/signup?email=multi_test3@test.com")
        
        # Verify all were added
        response = client.get("/activities")
        activities_data = response.json()
        
        assert "multi_test1@test.com" in activities_data["Chess Club"]["participants"]
        assert "multi_test2@test.com" in activities_data["Programming Class"]["participants"]
        assert "multi_test3@test.com" in activities_data["Gym Class"]["participants"]

    def test_isolation_after_multiple_modifications(self, client):
        """Test that starts fresh after previous test modified multiple activities."""
        response = client.get("/activities")
        activities_data = response.json()
        
        # Should not contain any participants from previous test
        assert "multi_test1@test.com" not in activities_data["Chess Club"]["participants"]
        assert "multi_test2@test.com" not in activities_data["Programming Class"]["participants"]
        assert "multi_test3@test.com" not in activities_data["Gym Class"]["participants"]
        
        # Should have initial state
        assert len(activities_data["Chess Club"]["participants"]) == 2
        assert len(activities_data["Programming Class"]["participants"]) == 2
        assert len(activities_data["Gym Class"]["participants"]) == 2

    def test_unregister_isolation(self, client):
        """Test that unregister operations are also properly isolated."""
        # Remove an initial participant
        response = client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        activities_data = response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Chess Club"]["participants"]) == 1

    def test_isolation_after_unregister(self, client):
        """Test that previous unregister operations don't affect this test."""
        response = client.get("/activities")
        activities_data = response.json()
        
        # Should have initial state restored, including the participant removed in previous test
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Chess Club"]["participants"]) == 2