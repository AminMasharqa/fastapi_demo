# Item endpoints tests 
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import metadata, database

client = TestClient(app)

# Setup test database and user
@pytest.fixture(autouse=True)
async def setup_database():
    # Create an in-memory SQLite database for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    metadata.create_all(test_engine)
    
    # Override the database URL to use the test database
    database.url = "sqlite:///:memory:"
    
    # Connect to the test database
    await database.connect()
    
    # Run the tests
    yield
    
    # Disconnect from the test database
    await database.disconnect()

# Fixture to create a test user and get a token
@pytest.fixture
def user_token():
    # Create a test user
    client.post(
        "/users/",
        json={
            "email": "itemtest@example.com",
            "username": "itemtestuser",
            "password": "password123"
        }
    )
    
    # Login to get token - use form data, not JSON
    response = client.post(
        "/users/token",
        data={
            "username": "itemtestuser",
            "password": "password123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Debug information
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Return the token
    return response.json().get("access_token")

# Fixture to create a test user with items
@pytest.fixture
def user_with_items(user_token):
    # Create some test items for the user
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create first item
    client.post(
        "/items/",
        json={
            "title": "Test Item 1",
            "description": "This is test item 1"
        },
        headers=headers
    )
    
    # Create second item
    client.post(
        "/items/",
        json={
            "title": "Test Item 2",
            "description": "This is test item 2"
        },
        headers=headers
    )
    
    # Return the token and headers for further tests
    return {"token": user_token, "headers": headers}

# Test creating an item
def test_create_item(user_token):
    response = client.post(
        "/items/",
        json={
            "title": "New Item",
            "description": "This is a new item"
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Item"
    assert data["description"] == "This is a new item"
    assert "id" in data
    assert "owner_id" in data
    assert "created_at" in data

# Test creating an item without authentication
def test_create_item_without_auth():
    response = client.post(
        "/items/",
        json={
            "title": "Unauthorized Item",
            "description": "This should fail"
        }
    )
    assert response.status_code == 401

# Test getting all items for a user
def test_read_items(user_with_items):
    response = client.get(
        "/items/",
        headers=user_with_items["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # Should have at least the two items we created
    
    # Check the content of the items
    assert any(item["title"] == "Test Item 1" for item in data)
    assert any(item["title"] == "Test Item 2" for item in data)

# Test getting a specific item
def test_read_item(user_with_items):
    # First, get all items to find an ID
    response = client.get(
        "/items/",
        headers=user_with_items["headers"]
    )
    items = response.json()
    item_id = items[0]["id"]
    
    # Get the specific item
    response = client.get(
        f"/items/{item_id}",
        headers=user_with_items["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert "title" in data
    assert "description" in data
    assert "owner_id" in data

# Test getting a non-existent item
def test_read_nonexistent_item(user_token):
    response = client.get(
        "/items/9999",  # Assuming this ID doesn't exist
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404

# Test getting an item that belongs to another user
def test_read_other_user_item(user_with_items):
    # Create another user
    client.post(
        "/users/",
        json={
            "email": "otheruser@example.com",
            "username": "otheruser",
            "password": "password123"
        }
    )
    
    # Login as other user
    response = client.post(
        "/users/token",
        data={
            "username": "otheruser",
            "password": "password123"
        }
    )
    other_token = response.json()["access_token"]
    
    # Get all items for the first user to find an ID
    response = client.get(
        "/items/",
        headers=user_with_items["headers"]
    )
    items = response.json()
    item_id = items[0]["id"]
    
    # Try to access the item as the other user
    response = client.get(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 404  # Should not find the item

# Test updating an item
def test_update_item(user_with_items):
    # Get all items to find an ID
    response = client.get(
        "/items/",
        headers=user_with_items["headers"]
    )
    items = response.json()
    item_id = items[0]["id"]
    
    # Update the item
    response = client.put(
        f"/items/{item_id}",
        json={
            "title": "Updated Item",
            "description": "This item has been updated"
        },
        headers=user_with_items["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Updated Item"
    assert data["description"] == "This item has been updated"
    
    # Verify the update by getting the item again
    response = client.get(
        f"/items/{item_id}",
        headers=user_with_items["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Item"

# Test deleting an item
def test_delete_item(user_with_items):
    # Get all items to find an ID
    response = client.get(
        "/items/",
        headers=user_with_items["headers"]
    )
    items = response.json()
    item_id = items[0]["id"]
    
    # Delete the item
    response = client.delete(
        f"/items/{item_id}",
        headers=user_with_items["headers"]
    )
    assert response.status_code == 204
    
    # Verify the item is deleted
    response = client.get(
        f"/items/{item_id}",
        headers=user_with_items["headers"]
    )
    assert response.status_code == 404