from fastapi import FastAPI, Request, Path, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from app.routers import users, friends, orders, payments, dashboard, auth, story
from pydantic import BaseModel
from app import schemas,models
from typing import List

app = FastAPI()

base_url = "http://127.0.0.1:8000"

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.get("/dashboard/{user_id}")
async def get_dashboard(request: Request, user_id: int):
    return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user_id": user_id,
                "base_url": base_url 
            }
        )
    
@app.get("/story")   
async def get_story_loading_page(
    request: Request
    ):
    return templates.TemplateResponse(
            "story_loading.html",
            {"request": request,
             "base_url": base_url}
        )

@app.get("/story/{story_id}")
async def get_story(request: Request,story_id:int):
    
    display_story = models.get_display_story(story_id)
    temp_story = models.get_temp_story(story_id)
    user_id = request.query_params.get("user_id")
    wiki_references = models.get_identified_references_by_display_story_id(story_id)
    wiki_references = [schemas.WikiReference(**r).model_dump(mode="json") for r in wiki_references]
    return templates.TemplateResponse(
            "story.html",
            {
                "request": request,
                "generated_story": display_story["generated_story_text"],
                "wiki_references": wiki_references,
                "user_id": user_id,
                "base_url": base_url
            }
        )

@app.get("/confirm")
async def confirm_order(request: Request):
    amount = request.query_params.get('amount')
    order_id = request.query_params.get('order_id')
    return templates.TemplateResponse(
        "payment_confirm.html",
        {"request": request, 
         "amount": amount, 
         "order_id": order_id,
         "base_url": base_url}
    )

# Include routers for the API
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(story.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8111)