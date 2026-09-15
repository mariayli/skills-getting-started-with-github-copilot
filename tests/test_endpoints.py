"""Tests for FastAPI application endpoints"""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect_to_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client, reset_activities):
        """Test that GET /activities returns HTTP 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client, reset_activities):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_all_activities(self, client, reset_activities):
        """Test that all activities are returned"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Tennis Club", "Art Studio", "Drama Club", "Debate Team", "Science Club"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in activities

    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_participants_are_emails(self, client, reset_activities):
        """Test that participants are email strings"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client, reset_activities, new_student_email):
        """Test successful signup of a new student"""
        activity_name = "Chess Club"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_student_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_student_email in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert new_student_email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities, sample_email):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student(self, client, reset_activities, sample_email):
        """Test that signup fails for student already in activity"""
        activity_name = "Chess Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Test that multiple different students can signup for same activity"""
        activity_name = "Programming Class"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all students are in the activity
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity_name]["participants"]
        
        for email in emails:
            assert email in participants

    def test_signup_student_in_different_activities(self, client, reset_activities):
        """Test that a student can signup for multiple different activities"""
        student_email = "athlete@mergington.edu"
        activities_list = ["Chess Club", "Basketball Team", "Tennis Club"]
        
        for activity_name in activities_list:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": student_email}
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        for activity_name in activities_list:
            assert student_email in activities[activity_name]["participants"]

    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with URL-encoded email containing special characters"""
        activity_name = "Art Studio"
        email = "test+tag@mergington.edu"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify email with special characters is preserved
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities, sample_email):
        """Test successful unregistration of a student"""
        activity_name = "Chess Club"
        
        # First signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Then unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": sample_email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert sample_email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities, sample_email):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": sample_email}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregister fails for student not in activity"""
        activity_name = "Drama Club"
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_does_not_affect_other_participants(self, client, reset_activities):
        """Test that unregistering one student doesn't affect others in same activity"""
        activity_name = "Gym Class"
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Signup all students
        for email in students:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Unregister one student
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": students[1]}
        )
        assert response.status_code == 200
        
        # Verify correct student was removed and others remain
        activities_response = client.get("/activities")
        activities = activities_response.json()
        participants = activities[activity_name]["participants"]
        
        assert students[0] in participants
        assert students[1] not in participants
        assert students[2] in participants

    def test_unregister_with_special_characters_in_email(self, client, reset_activities):
        """Test unregister with URL-encoded email containing special characters"""
        activity_name = "Science Club"
        email = "researcher+test@mergington.edu"
        
        # Signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify email was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_signup_and_unregister_cycle(self, client, reset_activities):
        """Test full cycle: signup, unregister, signup again"""
        activity_name = "Debate Team"
        email = "debater@mergington.edu"
        
        # Signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Signup again (should succeed since they were unregistered)
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify final state
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
