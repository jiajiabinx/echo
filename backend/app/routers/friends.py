from fastapi import APIRouter, HTTPException
from app import models, schemas
from typing import List

router = APIRouter(
    prefix="/api/friends",
    tags=["friends"]
)

@router.post("/", response_model=schemas.Friend)
async def add_friend(friend: schemas.FriendCreate) -> schemas.Friend:
    try:
        created_friend = models.insert_friend(friend.user_id_left, friend.user_id_right)
        return created_friend
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    
    
@router.get("/{user_id}", response_model=List[schemas.Users])
async def get_friends(user_id: int) -> List[schemas.Users]:
    try:
        friends = models.get_user_friends(user_id)
        return friends
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discover/{user_id}", response_model=List[schemas.Users])
async def discover_friends(user_id: int) -> List[schemas.Users]:
    try:
        friends_ids = [friend['user_id'] for friend in models.get_user_friends(user_id)]
        exclude_ids = friends_ids + [user_id]
        discoverable_users = models.get_random_users(exclude_ids, limit=5)
        return discoverable_users
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))