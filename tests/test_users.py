import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from databases import Database, DatabaseURL
import os

from app.main import app
from app.database import metadata, database

client = TestClient(app)

@pytest.fixture(autouse=True)
async def setup_database():
    # Create a unique in-memory database URL for each test
    test_db_url = "sqlite:///:memory:"
    
    # Create an in-memory SQLite database for testing
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Store original URL and connection state
    original_url = database.url
    was_connected = database.is_connected
    
    if was_connected:
        await database.disconnect()
    
    # Drop all tables if they exist
    metadata.drop_all(test_engine)
    
    # Create tables with updated schema
    metadata.create_all(test_engine)
    
    # Override the database URL
    database.url = DatabaseURL(test_db_url)
    
    # Connect to the test database
    await database.connect()
    
    yield
    
    # Disconnect from the test database
    await database.disconnect()
    
    # Restore original URL and connection if needed
    database.url = original_url
    if was_connected:
        await database.connect()

# Helper functions for common test operations
def create_test_user(email="test@example.com", username="testuser", password="password123"):
    """Helper to create a user and return the response"""
    return client.post(
        "/users/",
        json={
            "email": email,
            "username": username,
            "password": password
        }
    )

def get_user_token(username="testuser", password="password123"):
    """Helper to get auth token for a user"""
    response = client.post(
        "/users/token",
        data={
            "username": username,
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_user_registration_and_authentication():
    """
    Test covering user registration and authentication:
    - Registration with validation
    - Login and token generation
    - Profile retrieval with token
    """
    # Test basic registration
    response = create_test_user(
        email="test@example.com", 
        username="testuser", 
        password="securepass123"
    )
    assert response.status_code == 200, f"Failed to create user: {response.json()}"
    user_data = response.json()
    assert user_data["email"] == "test@example.com"
    assert user_data["username"] == "testuser"
    assert "id" in user_data
    
    # Test duplicate email registration
    response = create_test_user(
        email="test@example.com", 
        username="another_user", 
        password="password123"
    )
    assert response.status_code == 400
    assert "registered" in response.json().get("detail", "").lower()
    
    # Test duplicate username registration
    response = create_test_user(
        email="another@example.com", 
        username="testuser", 
        password="password123"
    )
    assert response.status_code == 400
    assert "registered" in response.json().get("detail", "").lower()
    
    # Test login with valid credentials
    response = client.post(
        "/users/token",
        data={
            "username": "testuser",
            "password": "securepass123"
        }
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]
    
    # Test login with invalid credentials
    response = client.post(
        "/users/token",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    
    # Test profile retrieval with valid token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    profile = response.json()
    assert profile["email"] == "test@example.com"
    assert profile["username"] == "testuser"
    
    # Test profile retrieval with invalid token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401