# User-related endpoints 
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy import select, insert
import datetime

from app.models import User, UserCreate, Token
from app.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.database import database, users

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Get token (login)
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Create user
@router.post("/", response_model=User)
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    # Check if user already exists
    query = select(users).where(
        (users.c.email == user.email) | (users.c.username == user.username)
    )
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )
    
    # Create new user with explicit values for all required fields
    current_time = datetime.datetime.utcnow()
    hashed_password = get_password_hash(user.password)

    query = insert(users).values(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        disabled=False,
        created_at=current_time
    )
    user_id = await database.execute(query)
    
    # Add background task to send welcome email
    background_tasks.add_task(send_welcome_email, user.email)
    
    # Return created user
    created_user = await database.fetch_one(
        select(users).where(users.c.id == user_id)
    )
    return created_user

# Get current user info
@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Send welcome email (background task)
async def send_welcome_email(email: str):
    # In a real application, this would send an actual email
    print(f"Sending welcome email to {email}")
    # Simulate delay
    import asyncio
    await asyncio.sleep(2)
    print(f"Welcome email sent to {email}")