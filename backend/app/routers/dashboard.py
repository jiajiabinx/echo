from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app import database


router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory="templates")


class SessionHistory(BaseModel):
    generated_story_text: str
    story_id: int
    transaction_id: str
    timestamp: datetime
    
@router.get("/history/{user_id}")
async def get_story_history(user_id: int) -> List[SessionHistory]:
    session_history = database.get_user_historical_sessions(user_id)
    return session_history