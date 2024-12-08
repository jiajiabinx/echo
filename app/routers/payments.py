from fastapi import APIRouter, HTTPException
from app import models, schemas

router = APIRouter(
    prefix="/api/payments",
    tags=["payments"]
)
    
@router.post("/confirm")
async def record_payment(payment: schemas.PaymentRequest)->schemas.CompletedPayment:
    try:
        completed_payment = models.record_payment(payment.user_id, payment.order_id)
        #return {"message": "Payment recorded successfully"}
        completed_payment = schemas.CompletedPayment(**completed_payment)
        return completed_payment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))