# Pydantic models 
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
# from pydantic import BaseModel, Field, EmailStr

# User models
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    disabled: bool = False
    created_at: datetime

class User(UserBase):
    id: int
    disabled: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Item models
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True