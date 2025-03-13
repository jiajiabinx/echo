from fastapi import APIRouter, HTTPException
from app import database, schemas, models
import json
import uuid
from app import dependencies


router = APIRouter(
    prefix="/api",
    tags=["story"]
)


@router.get("/story")
async def get_stories(story_id: int | None = None, user_id: int | None = None) -> list[schemas.GeneratedStory]:
    assert story_id or user_id, "Either story_id or user_id must be provided"
    if story_id:
        story = database.get_story_by_story_id(story_id)
        return [story]
    elif user_id:
        stories = database.get_all_stories_by_user_id(user_id)
        return stories

@router.delete("/story")
async def get_stories(story_id: int ):
   return database.delete_story(story_id)


@router.post('/yunsuan')
async def yun_suan(payment_token: schemas.CompletedPayment) -> schemas.TempStory:
    payment_complete, lack = database.check_payment(payment_token.user_id, 
                                 payment_token.session_id, 
                                 payment_token.order_id)

    if not payment_complete:
        raise HTTPException(status_code=400, detail="Payment not found")
    elif not lack:
        raise HTTPException(status_code=400, detail=f"Order fullfilled")
    elif lack != "past_story":
        raise HTTPException(status_code=400, detail=f"Temp story already generated, generate future story instead - go to /api/tuisuan endpoint")

    user = database.get_user_by_id(payment_token.user_id)
    user = schemas.Users(**user)
    user_str = json.dumps(user.model_dump(mode="json"))
    
    sbert_call_transaction_id = uuid.uuid4()
    sbert_call = database.record_sbert_call(sbert_call_transaction_id, payment_token.session_id, user_str)
    past_story_text = dependencies.generate_past_story(user_str)
      
    ##get biography    

    _ = database.insert_past_story(sbert_call_transaction_id, past_story_text)
    past_story = database.get_past_story(_["story_id"])
    past_story = schemas.TempStory(**past_story)
    
    #do a sbert call

    #find referennce
    matches = dependencies.get_similar_stories(past_story_text, 5)
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
    
    #record identified relationships
    identified_relationships = database.record_identified_relationships(past_story.story_id, wiki_references_ids, similarity_scores)
    
    return past_story

    

@router.post("/tuisuan")
async def tui_suan(payment_token: schemas.CompletedPayment) -> schemas.DisplayStory:
    payment_complete, lack = database.check_payment(payment_token.user_id, 
                                 payment_token.session_id, 
                                 payment_token.order_id)

    if not payment_complete:
        raise HTTPException(status_code=400, detail="Payment not found")
    elif not lack:
        raise HTTPException(status_code=400, detail=f"Order fullfilled")
    elif lack != "future_story": 
        raise HTTPException(status_code=400, detail=f"Display story already generated, generate past story first - go to /api/tuisuan endpoint")

 
    system_prompt = """You will be given a biography of a person. 
    You will use your vast knowledge of human history and pattern finding skills to write a short predictive story about their life.
    You will use the biography of similar historical figures to write out future looking narrative for the person using the life trajectories of the three historical figures.
    You will not mention the historical figures in the story.
    Stay factual and concise and don't add literary embellishments.
    The story should be 1000 words or less.
    You do not need to respond with pleasantry. \n """
    
    
    transaction_id = uuid.uuid4()
    database.record_APICall(transaction_id, payment_token.session_id, system_prompt)

    wiki_references = database.get_identified_references_by_session_id(payment_token.session_id)

            
    wiki_references = [schemas.WikiReference(**r) for r in wiki_references]
    wiki_references_texts, wiki_references_titles = dependencies.process_wiki_references(wiki_references)
    
    
    biography = database.get_past_story_by_session_id(payment_token.session_id)
    biography = schemas.TempStory(**biography)
    
    response = dependencies.open_ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "This is the biography of the person: " + biography.generated_story_text},
            {"role": "user", "content": "These are the historical figures that are most similar to the person in question: " + wiki_references_texts}
        ]
    )
    
    
    story_text = response.choices[0].message.content
     
    #generate story
    future_story = database.insert_future_story(transaction_id, story_text,wiki_references_titles)
    future_story = schemas.DisplayStory(**future_story)
    
    return future_story







