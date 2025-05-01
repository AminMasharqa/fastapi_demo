# Database connection 
import databases
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, MetaData
import datetime
import os

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime
import datetime

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Database connection
database = databases.Database(DATABASE_URL)

# SQLAlchemy metadata
metadata = MetaData()

# Define tables
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("hashed_password", String),
    Column("disabled", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.datetime.utcnow)
)

items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, index=True),
    Column("description", Text, nullable=True),
    Column("owner_id", Integer, ForeignKey("users.id")),
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
)

# SQLAlchemy engine
engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create all tables
async def init_db():
    metadata.create_all(engine)