# Dependency injection functions 
from fastapi import Depends, HTTPException, status
from app.auth import get_current_active_user
from app.models import User
from app.database import database, items
from sqlalchemy import select

# Check if current user is item owner
async def check_item_owner(
    item_id: int, current_user: User = Depends(get_current_active_user)
):
    query = select([items]).where(
        (items.c.id == item_id) & (items.c.owner_id == current_user.id)
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or you don't have permission",
        )
    return item