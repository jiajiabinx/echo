from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict
from app import database, schemas
from app.routers import users
from app.dependencies import templates

router = APIRouter(
)

class LoginForm(BaseModel):
    user_id: int

class LoginResponse(BaseModel):
    status: str
    redirect_url: str

class SignupResponse(BaseModel):
    status: str
    user_id: int
    message: str

@router.get("/")
async def show_login_page(request: Request) :
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(login_form: LoginForm)-> LoginResponse:
    try:
        # Verify user exists
        user =  database.get_user_by_id(login_form.user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return LoginResponse(
            status="success",
            redirect_url=f"/dashboard/{login_form.user_id}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signup")
async def signup(sign_up_form: schemas.UserCreate) -> SignupResponse:

    user = database.insert_user(sign_up_form.dict())
    return SignupResponse(
        status="success",
        user_id=user['user_id'],
        message="User created successfully"
    )

