from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app import database, schemas
import json
import os
import uuid
import anthropic
from app import dependencies


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
    temp_story_text = dependencies.generate_temp_story(user_str)
    api_call_transaction_id = uuid.uuid4()
    api_call = database.record_APICall(api_call_transaction_id, payment_token.session_id, "fake_placeholder_prompt")
    _ = database.insert_temp_story(api_call_transaction_id, temp_story_text)
    temp_story = database.get_temp_story(_["story_id"])
    temp_story = schemas.TempStory(**temp_story)
    
    #do a fake sbert call
    sbert_call_transaction_id = uuid.uuid4()
    sbert_call = database.record_sbert_call(sbert_call_transaction_id, payment_token.session_id, user_str)
    #find referennce
    matches = dependencies.get_similar_stories(temp_story_text, 5)
    matches =sorted(matches, key=lambda x: x["score"], reverse=True)
    
    #filter for human
    wiki_references_ids = []
    similarity_scores = []
    for match in matches:
        page = dependencies.wiki.page(match["metadata"]["title"])
        if dependencies.filter_for_human(page):
            wiki_reference = database.insert_wiki_reference(match["id"], match["metadata"]["text"], match["metadata"]["url"], match["metadata"]["title"])
            wiki_references_ids.append(match["id"])
            similarity_scores.append(match["score"])
    
    #record referred relationship
    referred_relationships = database.record_referred_relationship(temp_story.story_id, sbert_call_transaction_id)

    #record identified relationships
    identified_relationships = database.record_identified_relationships(temp_story.story_id, wiki_references_ids, similarity_scores)
    
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
    You will use the biography of similar historical figures to weave a short predictive fortune using the life trajectories of the three historical figures.
    You will not mention the historical figures in the story.
    The story should be 1000 words or less.
    You do not need to respond with pleasantry. \n """
    
    
    transaction_id = uuid.uuid4()
    database.record_APICall(transaction_id, payment_token.session_id, system_prompt)

    wiki_references = database.get_identified_references_by_session_id(payment_token.session_id)
    wiki_references = [schemas.WikiReference(**r) for r in wiki_references]
    wiki_references_texts, wiki_references_titles = dependencies.process_wiki_references(wiki_references)
    
    
    biography = database.get_temp_story_by_session_id(payment_token.session_id)
    biography = schemas.TempStory(**biography)
    
    
    response = dependencies.open_ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "This is the biography of the person: " + biography.generated_story_text},
            {"role": "user", "content": "These are the historical figures that are most similar to the person in question: " + wiki_references_texts}
        ]
    )
    story_text = response.choices[0].message.content
     
    #generate story
    display_story = database.insert_display_story(transaction_id, story_text,wiki_references_titles)
    display_story = schemas.DisplayStory(**display_story)
    return display_story


@router.get("/")
async def get_story(story_id: int, story_type: str):
    if story_type == "display":
        display_story = database.get_display_story(story_id)
        display_story = schemas.DisplayStory(**display_story)
        return display_story
    elif story_type == "biography":
        temp_story = database.get_temp_story(story_id)
        temp_story = schemas.TempStory(**temp_story)
        return temp_story
    else:
        raise HTTPException(status_code=400, detail="Invalid story type")





