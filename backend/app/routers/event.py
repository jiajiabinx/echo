from fastapi import APIRouter, Query
from app import database, schemas
from pydantic import BaseModel
from app.dependencies import nlp, get_embeddings, tsne
from typing import List
from datetime import date
import random
import numpy as np

router = APIRouter(
    prefix="/api",
    tags=["event"]
)


class ProcessEventRequest(BaseModel):
    text: str
    user_id: int
    story_id: int
  

class ProcessedEvent(BaseModel):
    user_id: int  
    story_id: int
    
    text: str
    annotated_text: str
    """ Sample text that includes entity annotation
    
    Ex:
    [PERSON]John[/PERSON] is a [JOB]doctor[/JOB].
    
    """
    
    event_type: str
    event_date: date | None = None
    
class EventVisual(ProcessedEvent):
    event_id: int    
    coordinates: List[float] #x,y,z coordinates
    event_type: str
    future_ind: bool



@router.post("/eventprocess")
async def process_event(request: ProcessEventRequest) -> List[ProcessedEvent]:
    doc = nlp(request.text)
    events = []
    for sentence in doc.sents:
       labeled_sentence = ""
       last_end = 0
       sentence_start = sentence.start_char
       for ent in sentence.ents:
           start = ent.start_char - sentence_start
           end = ent.end_char - sentence_start
           labeled_sentence += sentence.text[last_end:start]
           labeled_entity = f"[{ent.label_}]{ent.text}[/{ent.label_}]"
           labeled_sentence += labeled_entity
           last_end = end
           
       labeled_sentence += sentence.text[last_end:]
       labeled_sentence = labeled_sentence.rstrip("\n")
       event = {
                "user_id": request.user_id,
                "story_id": request.story_id,
                "annotated_text": labeled_sentence,
                "text": sentence.text,
                "event_type": random.choice(["career", "personal", "education", "social", "serendipity"]), #to be done 
                # "event_date": date.today() #to be done
            }
       events.append(event)
    return events 

        
        
@router.post("/event")
async def create_event(events: List[ProcessedEvent]) -> List[schemas.Event]:
    created_events = []
    for event in events:
        created_event = database.create_event(event)
        created_events.append(created_event)
    return created_events

@router.get("/event")
async def get_events(user_id: int, story_ids: List[int] = Query(...,description = 'List of story ids')) -> List[EventVisual]:
    assert len(story_ids) > 0, "story_ids must be provided"
    
    events = database.get_events_by_story_ids(story_ids)
    events = [schemas.Event(**event) for event in events if event["user_id"] == user_id]
    
    if len(events) < 3:
        return []
    
    embeddings = np.array([get_embeddings(event.text) for event in events])
    tsne_result = tsne.fit_transform(embeddings)
    tsne_result = tsne_result.tolist()
    event_visuals = [
        EventVisual(
            user_id=event.user_id,
            story_id=event.story_id,
            text=event.text,
            future_ind=True,
            annotated_text=event.annotated_text,
            event_type=event.event_type,
            event_date=event.event_date,
            event_id=event.event_id,
            coordinates=coordinates
        )
        for event, coordinates in zip(events, tsne_result)
    ]

    return event_visuals