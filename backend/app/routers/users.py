from fastapi import APIRouter, HTTPException
from typing import List
from app import database, schemas

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)



@router.get("/{user_id}", response_model=schemas.Users)
async def get_user(user_id: int) -> schemas.Users:
    try:
        user = database.get_user_by_id(user_id)
        if user and not user.get('display_name'):
            user['display_name'] = "Anonymous User " +user['user_id']
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/", response_model=schemas.Users)
async def create_user(user: schemas.UserCreate) -> schemas.Users:
    try:
        created_user = database.insert_user(user.dict())
        return created_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/{user_id}")
async def update_user(user_id: int, user: schemas.UserCreate):
    try:
        user_data = user.model_dump()
        user_data['user_id'] = user_id  # Ensure user_id is in the dictionary
        updated_user = database.update_user(user_data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found or failed to update")
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating user info: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    try:
        database.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))