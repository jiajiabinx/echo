from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app import database, schemas
import json
import os
import uuid
import anthropic


router = APIRouter(
    prefix="/api/story",
    tags=["story"]
)

@router.post('/yunsuan')
async def yun_suan(payment_token: schemas.CompletedPayment) -> schemas.TempStory:
    check = database.check_payment(payment_token.user_id, 
                                 payment_token.session_id, 
                                 payment_token.order_id)
    if not check:
        raise HTTPException(status_code=400, detail="Payment not found")
    ##get biography    
    #record a fake api call
    #later will implement an actual api call
    user = database.get_user_by_id(payment_token.user_id)
    user = schemas.Users(**user)
    user_str = json.dumps(user.model_dump(mode="json"))
    api_call_transaction_id = uuid.uuid4()
    api_call = database.record_APICall(api_call_transaction_id, payment_token.session_id, "fake_placeholder_prompt")
    _ = database.insert_temp_story(api_call_transaction_id, user_str)
    temp_story = database.get_temp_story(_["story_id"])
    temp_story = schemas.TempStory(**temp_story)
    
    #do a fake sbert call
    sbert_call_transaction_id = uuid.uuid4()
    sbert_call = database.record_sbert_call(sbert_call_transaction_id, payment_token.session_id, user_str)
    #find referennce
    
    wiki_references = database.get_random_wiki_references(3)
    wiki_reference_ids = [r["wiki_page_id"] for r in wiki_references]
    #record referred relationship
    referred_relationships = database.record_referred_relationship(temp_story.story_id, sbert_call_transaction_id)

    #record identified relationships
    identified_relationships = database.record_identified_relationships(temp_story.story_id, wiki_reference_ids)
    
    return temp_story

@router.post("/tuisuan")
async def tui_suan(payment_token: schemas.CompletedPayment) -> schemas.DisplayStory:
    check = database.check_payment(payment_token.user_id, 
                                 payment_token.session_id, 
                                 payment_token.order_id)
    if not check:
        raise HTTPException(status_code=400, detail="Payment not found")
   
    #record api call
    
    system_prompt = """Pretend that you are a fortune teller. 
    You will be given a biography of a person. 
    You will use your vast knowledge of human history and pattern finding skills to write a short predictive story about their life.
    Pretend that the three historical figure and their stories are some of the most similar life trajectories to the person in question.
    You will use the biography to determine which three historical figures are most similar to the person in question.
    You will then use the biography to weave a short predictive fortune using the life trajectories of the three historical figures.
    The story should be 1000 words or less.
    You do not need to respond with pleasantry. \n """
    
    # from transformers import pipeline
    
    # t2t_pipe = pipeline("text2text-generation", model="google/flan-t5-large")
    
    transaction_id = uuid.uuid4()
    database.record_APICall(transaction_id, payment_token.session_id, system_prompt)

    wiki_references = database.get_identified_references_by_session_id(payment_token.session_id)

    biography = database.get_temp_story_by_session_id(payment_token.session_id)
    biography = schemas.TempStory(**biography)
    
    wiki_references = [schemas.WikiReference(**r).model_dump(mode="json") for r in wiki_references]
    wiki_references_str = json.dumps(wiki_references)
    
    # client = anthropic.Anthropic(
    #     api_key=os.environ["CLAUDE_API_KEY"],
    # )
    
    # message = client.messages.create(
    # model="claude-3-5-sonnet-20240620",
    # max_tokens=1000,
    # temperature=0,
    # system=system_prompt,
    # messages=[
    #     {
    #         "role": "user",
    #         "content": [
    #             {
    #                 "type": "text",
    #                 "text": biography.generated_story_text
    #             },
    #             {
    #                 "type": "text",
    #                 "text": wiki_references_str
    #             }
    #         ]
    #     }
    # ]
    # )
    # story_text = message.content[0].text
    
    story_text =  'test test test test'
    
    #generate story
    display_story = database.insert_display_story(transaction_id, wiki_references_str, "", story_text)
    display_story = schemas.DisplayStory(**display_story)
    return display_story


@router.get("/{story_id}")
async def get_story(story_id: int) -> schemas.DisplayStory:
    display_story = database.get_display_story(story_id)
    display_story = schemas.DisplayStory(**display_story)
    return display_story

@router.get("/biography")
async def get_biography(story_id: int) -> schemas.TempStory:
    temp_story = database.get_temp_story(story_id)
    temp_story = schemas.TempStory(**temp_story)
    return temp_story



