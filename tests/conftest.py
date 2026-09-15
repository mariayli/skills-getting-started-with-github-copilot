"""Pytest configuration and shared fixtures for testing the FastAPI application"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a FastAPI TestClient for making requests to the app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store the original activities dictionary at fixture creation
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for varsity and JV levels",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn and practice tennis skills with friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": ["jordan@mergington.edu", "casey@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and mixed media techniques",
            "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["isabella@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and improv exercises",
            "schedule": "Thursdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["marcus@mergington.edu", "ava@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills through competitive debate",
            "schedule": "Tuesdays and Thursdays, 4:30 PM - 6:00 PM",
            "max_participants": 14,
            "participants": ["ryan@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore various scientific disciplines",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 22,
            "participants": ["noah@mergington.edu", "grace@mergington.edu"]
        }
    }
    
    # Clear the current activities and restore to original state
    activities.clear()
    activities.update(deepcopy(original_activities))
    
    yield activities
    
    # Reset after test completes
    activities.clear()
    activities.update(deepcopy(original_activities))


@pytest.fixture
def sample_email():
    """Provide a standard test email for reuse across tests"""
    return "test@mergington.edu"


@pytest.fixture
def new_student_email():
    """Provide a new student email not in any activity by default"""
    return "newstudent@mergington.edu"
