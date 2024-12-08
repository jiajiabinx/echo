from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime
#from pydantic.validators import strict_datetime_validator, strict_date_validator
#Commented out because they are not used, and causing trouble with import


class IChingBaseModel(BaseModel):
    class Config:
        from_attributes = False    


class Users(IChingBaseModel):
    user_id: int
    display_name: str | None = "Anonymous User" 
    birth_date: date
    birth_location: str
    primary_residence: str
    current_location: str
    college: str
    educational_level: str
    parental_income: int
    primary_interest: str
    profession: str
    religion: str
    race: str

    @field_validator('race')
    @classmethod
    def validate_race(cls, v):
        valid_races = ['American Indian or Alaska Native', 'Asian', 'Black or African American', 
                       'Hispanic or Latino', 'Middle Eastern or North African', 
                       'Native Hawaiian or Pacific Islander', 'White']
        if v is not None and v not in valid_races:
            raise ValueError(f'Race must be one of {valid_races}')
        return v

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v):
        if v > date.today():
            raise ValueError('Birth date cannot be in the future')
        return v


class Friend(IChingBaseModel):
    user_id_left: int
    user_id_right: int


    @classmethod
    @model_validator(mode="before")
    def validate_user_ids(cls, values):
        if values['user_id_left'] >= values['user_id_right']:
            raise ValueError("user_id_left must be less than user_id_right")
        return values


class Order(IChingBaseModel):
    order_id: int
    amount: float = Field(gt=0)


class Session(IChingBaseModel):
    session_id: int
    timestamp: datetime

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        if v > datetime.now():
            raise ValueError('Timestamp cannot be in the future')
        return v


class CompletedPayment(IChingBaseModel):
    user_id: int
    order_id: int
    session_id: int


#Jia 
class InitiatedTransaction(IChingBaseModel):
    session_id: int
    transaction_id: str


class APICall(InitiatedTransaction):
    transaction_id: str
    prompt: str


class SBERTCall(InitiatedTransaction):
    transaction_id: str
    corpus: str
    
    @field_validator('corpus')
    @classmethod
    def validate_corpus(cls, v):
        if len(v) == 0:
            raise ValueError('Corpus must not be empty')
        return v

class GeneratedStory(IChingBaseModel):
    transaction_id: str
    generated_story_text: str
    story_id: int


class TempStory(GeneratedStory):

    @field_validator('generated_story_text')
    @classmethod
    def validate_generated_story_text(cls, v):
        if len(v) == 0:
            raise ValueError('Generated story text must not be empty')
        return v

class DisplayStory(GeneratedStory):
    references: str
    reference_summary: str



class Referred(IChingBaseModel):
    story_id: int
    transaction_id: str



class WikiReference(IChingBaseModel):
    wiki_page_id: str
    text_corpus: str
    url: str
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith('https://en.wikipedia.org/wiki/'):
            raise ValueError('URL must start with https://en.wikipedia.org/wiki/')
        return v
    
class Identified(IChingBaseModel):
    wiki_page_id: str
    story_id: int
    
    
    
### New schemas for the app (that is not in the database)

class UserCreate(IChingBaseModel):
    display_name: str | None = "Anonymous User"
    birth_date: date
    birth_location: str
    primary_residence: str
    current_location: str
    college: str
    educational_level: str
    parental_income: int
    primary_interest: str
    profession: str
    religion: str
    race: str

class FriendCreate(Friend):
    pass

class OrderCreate(IChingBaseModel):
    user_id: int
    amount: int = 5

class PaymentRequest(IChingBaseModel):
    user_id: int
    order_id: int
    
class HistoricalSession(IChingBaseModel): 
    timestamp: datetime
    generated_story_text: str
    references: str
    reference_summary: str
