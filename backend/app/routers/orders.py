from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app import database, schemas

router = APIRouter(
    prefix="/api/orders",
    tags=["orders"]
)

class OrderResponse(BaseModel):
    redirect_url: str
    amount: int
    order_id: int

class SessionResponse(BaseModel):
    session_id: int

@router.post("/")
async def create_order(order: schemas.OrderCreate) -> OrderResponse:
    order = database.insert_order(order.amount)
    redirect_url = '/confirm'
    return OrderResponse(redirect_url=redirect_url, amount=order['amount'], order_id=order['order_id'])