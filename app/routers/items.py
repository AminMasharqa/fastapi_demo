# Item-related endpoints 
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select, insert, update, delete

from app.models import Item, ItemCreate
from app.auth import get_current_active_user
from app.dependencies import check_item_owner
from app.database import database, items
from app.models import User

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

# Create item
@router.post("/", response_model=Item)
async def create_item(
    item: ItemCreate, current_user: User = Depends(get_current_active_user)
):
    query = insert(items).values(
        title=item.title,
        description=item.description,
        owner_id=current_user.id,
    )
    item_id = await database.execute(query)
    created_item = await database.fetch_one(
        select([items]).where(items.c.id == item_id)
    )
    return created_item

# Get all items for current user
@router.get("/", response_model=List[Item])
async def read_items(current_user: User = Depends(get_current_active_user)):
    query = select([items]).where(items.c.owner_id == current_user.id)
    return await database.fetch_all(query)

# Get item by ID
@router.get("/{item_id}", response_model=Item)
async def read_item(item_id: int, current_user: User = Depends(get_current_active_user)):
    query = select([items]).where(
        (items.c.id == item_id) & (items.c.owner_id == current_user.id)
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Update item
@router.put("/{item_id}", response_model=Item)
async def update_item(
    item_id: int,
    item_data: ItemCreate,
    item = Depends(check_item_owner),
):
    query = (
        update(items)
        .where(items.c.id == item_id)
        .values(title=item_data.title, description=item_data.description)
    )
    await database.execute(query)
    updated_item = await database.fetch_one(
        select([items]).where(items.c.id == item_id)
    )
    return updated_item

# Delete item
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    item = Depends(check_item_owner),
):
    query = delete(items).where(items.c.id == item_id)
    await database.execute(query)
    return None