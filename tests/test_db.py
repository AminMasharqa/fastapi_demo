import pytest
import asyncio
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String
from sqlalchemy.pool import StaticPool
from databases import Database, DatabaseURL

from app.database import metadata, database, engine

@pytest.mark.asyncio
async def test_db_connection():
    """Test that we can connect to the database and create tables."""
    # Use a file-based SQLite database for testing
    test_db_url = "sqlite:///./test_temp.db"
    
    # Create test engine
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    
    # Drop all tables first to ensure a clean state
    metadata.drop_all(test_engine)
    
    # Create tables
    metadata.create_all(test_engine)
    
    # Connect database to the same URL
    original_url = database.url
    database.url = DatabaseURL(test_db_url)
    await database.connect()
    
    try:
        # Verify tables exist
        query = text("SELECT name FROM sqlite_master WHERE type='table';")
        result = await database.fetch_all(query)
        tables = [row['name'] for row in result]
        
        print("Tables in database:", tables)
        assert "users" in tables, "Users table not created"
        
        # Use a unique username for testing
        import uuid
        unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
        
        # Try to insert a test user with proper syntax
        await database.execute(
            "INSERT INTO users (email, username, hashed_password) VALUES (:email, :username, :hashed_password)",
            values={
                "email": f"{unique_username}@example.com",
                "username": unique_username,
                "hashed_password": "fakehash"
            }
        )
        
        # Verify user was inserted
        users = await database.fetch_all("SELECT * FROM users")
        print("Users in database:", users)
        assert len(users) > 0, "User not inserted correctly"
        
    finally:
        # Disconnect and restore original URL
        await database.disconnect()
        database.url = original_url
        
        # Clean up - remove test database file
        import os
        try:
            os.remove("./test_temp.db")
        except:
            pass