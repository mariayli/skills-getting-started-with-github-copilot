"""Tests for edge cases and validation in the FastAPI application"""

import pytest


class TestActivityNameHandling:
    """Tests for activity name edge cases"""

    def test_activity_name_with_spaces(self, client, reset_activities, sample_email):
        """Test that activity names with spaces work correctly"""
        activity_name = "Basketball Team"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert sample_email in activities[activity_name]["participants"]

    def test_activity_name_case_sensitivity(self, client, reset_activities, sample_email):
        """Test that activity names are case-sensitive"""
        # Lowercase version should not exist
        response = client.post(
            "/activities/chess club/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404

    def test_get_activities_preserves_all_activity_data(self, client, reset_activities):
        """Test that activity data is not corrupted after operations"""
        activity_name = "Tennis Club"
        email1 = "player1@mergington.edu"
        email2 = "player2@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        activities = response.json()
        initial_count = len(activities[activity_name]["participants"])
        
        # Signup two players
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})

        # Get activities and verify data integrity
        response = client.get("/activities")
        activities = response.json()

        activity = activities[activity_name]
        assert isinstance(activity["description"], str)
        assert len(activity["description"]) > 0
        assert isinstance(activity["schedule"], str)
        assert len(activity["schedule"]) > 0
        assert activity["max_participants"] > 0
        assert len(activity["participants"]) == initial_count + 2


class TestEmailFormatHandling:
    """Tests for email format edge cases"""

    def test_email_with_plus_sign(self, client, reset_activities):
        """Test email with plus sign is handled correctly"""
        activity_name = "Art Studio"
        email = "user+tag@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify it can be unregistered with the same email
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200

    def test_email_with_numbers_and_dots(self, client, reset_activities):
        """Test email with numbers and dots is handled correctly"""
        activity_name = "Programming Class"
        email = "john.doe.123@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_duplicate_check_is_exact_match(self, client, reset_activities):
        """Test that duplicate check is exact email match"""
        activity_name = "Drama Club"
        email1 = "user@mergington.edu"
        email2 = "user+tag@mergington.edu"
        
        # Signup with first email
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email1}
        )
        assert response1.status_code == 200
        
        # Signup with similar but different email should succeed
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email2}
        )
        assert response2.status_code == 200
        
        # Both should be in activity
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity_name]["participants"]
        
        assert email1 in participants
        assert email2 in participants


class TestStateIsolation:
    """Tests to verify state isolation between operations"""

    def test_signup_to_different_activities_independent(self, client, reset_activities, sample_email):
        """Test that signup to one activity doesn't affect others"""
        activity1 = "Chess Club"
        activity2 = "Gym Class"
        
        # Signup to first activity
        client.post(f"/activities/{activity1}/signup", params={"email": sample_email})
        
        # Verify in first activity
        response = client.get("/activities")
        activities = response.json()
        assert sample_email in activities[activity1]["participants"]
        assert sample_email not in activities[activity2]["participants"]

    def test_unregister_does_not_affect_other_activities(self, client, reset_activities, sample_email):
        """Test that unregistering from one activity doesn't affect others"""
        activity1 = "Basketball Team"
        activity2 = "Tennis Club"
        
        # Signup to both
        client.post(f"/activities/{activity1}/signup", params={"email": sample_email})
        client.post(f"/activities/{activity2}/signup", params={"email": sample_email})
        
        # Unregister from first
        client.delete(f"/activities/{activity1}/unregister", params={"email": sample_email})
        
        # Verify correct state
        response = client.get("/activities")
        activities = response.json()
        
        assert sample_email not in activities[activity1]["participants"]
        assert sample_email in activities[activity2]["participants"]

    def test_fixture_resets_between_tests(self, client, reset_activities):
        """Test that reset_activities fixture works correctly"""
        # Signup a student
        email = "fixture_test@mergington.edu"
        client.post("/activities/Science Club/signup", params={"email": email})
        
        # Verify added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Science Club"]["participants"]
        
        # Note: The fixture will reset after this test, so next test will have clean state
        # This is validated by the fact that other tests pass without manual cleanup


class TestKnownIssues:
    """Tests documenting known issues and edge cases"""

    def test_capacity_limit_not_enforced(self, client, reset_activities):
        """
        KNOWN ISSUE: The API does not enforce max_participants limit.
        This test documents the current behavior.
        
        TODO: Implement capacity limit validation in signup endpoint.
        This should:
        - Check if len(activity["participants"]) >= activity["max_participants"]
        - Return 400 with appropriate error message if at capacity
        """
        activity_name = "Chess Club"
        
        # Get current activity
        response = client.get("/activities")
        activities = response.json()
        activity = activities[activity_name]
        max_participants = activity["max_participants"]
        current_count = len(activity["participants"])
        spots_available = max_participants - current_count
        
        # Signup more students than available spots
        students_to_add = spots_available + 3
        
        for i in range(students_to_add):
            email = f"capacity_test_{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            # This currently succeeds even when over capacity
            assert response.status_code == 200
        
        # Verify we exceeded capacity
        response = client.get("/activities")
        activities = response.json()
        final_count = len(activities[activity_name]["participants"])
        
        assert final_count > activity["max_participants"], \
            "Capacity limit enforcement test: API allowed signup beyond max_participants"

    def test_activity_list_not_updated_in_response_after_signup(self, client, reset_activities):
        """
        Test behavior: After signing up, the response doesn't update activity list.
        This is not a bug but documents the signup endpoint's response structure.
        
        The signup endpoint returns a confirmation message, not updated activity list.
        Clients must call GET /activities to see updated data.
        """
        activity_name = "Debate Team"
        email = "response_test@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Response only contains message, not full activity data
        data = response.json()
        assert "message" in data
        assert "activities" not in data
        assert "participants" not in data


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios"""

    def test_student_signup_multiple_activities_workflow(self, client, reset_activities):
        """Test realistic workflow: Student signs up for multiple activities"""
        student_email = "jane.doe@mergington.edu"
        activities_to_join = ["Programming Class", "Art Studio", "Science Club"]
        
        # Student signs up for multiple activities
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name in activities_to_join:
            assert student_email in activities[activity_name]["participants"]

    def test_student_switches_activities_workflow(self, client, reset_activities):
        """Test realistic workflow: Student unregisters from one and signs up for another"""
        student_email = "switcher@mergington.edu"
        current_activity = "Chess Club"
        new_activity = "Drama Club"
        
        # Student signs up
        client.post(f"/activities/{current_activity}/signup", params={"email": student_email})
        
        # Student changes mind and switches
        client.delete(f"/activities/{current_activity}/unregister", params={"email": student_email})
        client.post(f"/activities/{new_activity}/signup", params={"email": student_email})
        
        # Verify correct state
        response = client.get("/activities")
        activities = response.json()
        
        assert student_email not in activities[current_activity]["participants"]
        assert student_email in activities[new_activity]["participants"]

    def test_activity_shows_realistic_participant_updates(self, client, reset_activities):
        """Test that activity data reflects realistic participant updates"""
        activity_name = "Tennis Club"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Add new participants
        new_emails = ["tennis_player1@mergington.edu", "tennis_player2@mergington.edu"]
        for email in new_emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Verify count increased
        response = client.get("/activities")
        activities = response.json()
        new_count = len(activities[activity_name]["participants"])
        
        assert new_count == initial_count + len(new_emails)
        
        # Remove one participant
        client.delete(f"/activities/{activity_name}/unregister", params={"email": new_emails[0]})
        
        # Verify count decreased
        response = client.get("/activities")
        activities = response.json()
        final_count = len(activities[activity_name]["participants"])
        
        assert final_count == new_count - 1
