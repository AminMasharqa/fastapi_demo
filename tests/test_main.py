# Main app tests 
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI Demo"}

def test_create_user():
    # Create a test user
    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data

def test_login():
    # Login with the test user
    response = client.post(
        "/users/token",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_create_item():
    # Login and get token
    token = test_login()
    
    # Create an item
    response = client.post(
        "/items/",
        json={
            "title": "Test Item",
            "description": "This is a test item"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert "id" in data
    assert "owner_id" in data
    return data["id"]

def test_read_items():
    # Login and get token
    token = test_login()
    
    # Get items
    response = client.get(
        "/items/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one item (from test_create_item)
    assert len(data) > 0

def test_read_item():
    # Login and get token
    token = test_login()
    
    # Create an item and get its ID
    item_id = test_create_item()
    
    # Get the item
    response = client.get(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Test Item"

def test_update_item():
    # Login and get token
    token = test_login()
    
    # Create an item and get its ID
    item_id = test_create_item()
    
    # Update the item
    response = client.put(
        f"/items/{item_id}",
        json={
            "title": "Updated Item",
            "description": "This item has been updated"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Updated Item"
    assert data["description"] == "This item has been updated"

def test_delete_item():
    # Login and get token
    token = test_login()
    
    # Create an item and get its ID
    item_id = test_create_item()
    
    # Delete the item
    response = client.delete(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Try to get the deleted item
    response = client.get(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404