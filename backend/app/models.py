
from sqlalchemy import Table, Column, Integer, String, Float, Date, DateTime, ForeignKey, CheckConstraint, ARRAY
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()
    


class Users(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, default="Anonymous User")
    birth_date = Column(Date, nullable=False)
    birth_location = Column(String, nullable=False)
    primary_residence = Column(String, nullable=False)
    current_location = Column(String, nullable=False)
    college = Column(String, nullable=False)
    educational_level = Column(String, nullable=False)
    parental_income = Column(Integer, nullable=False)
    primary_interest = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    religion = Column(String, nullable=False)
    race = Column(String, nullable=False)
    
    # Relationships
    payments = relationship("CompletedPayment", back_populates="user")
    
    __table_args__ = (
        CheckConstraint(
            "race IN ('American Indian or Alaska Native', 'Asian', 'Black or African American', "
            "'Hispanic or Latino', 'Middle Eastern or North African', "
            "'Native Hawaiian or Pacific Islander', 'White')"
        ),
        CheckConstraint("birth_date <= CURRENT_DATE"),
    )
    
event_entity_association = Table(
    'event_entity_association', Base.metadata,
    Column('event_id', Integer, ForeignKey('events.event_id'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.entity_id'), primary_key=True)
)


class Entity(Base):
    __tablename__ = 'entities'
    
    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_description = Column(String)
    
    events = relationship("Event", secondary='event_entity_association', back_populates="entities")

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'))
    
    text = Column(String, nullable=False)
    annotated_text = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    event_date = Column(Date)
    
    # Relationships
    user = relationship("Users")
    story = relationship("GeneratedStory", back_populates="events")
    entities = relationship("Entity", secondary='event_entity_association', back_populates="events")




class Friend(Base):
    __tablename__ = 'friends'
    
    user_id_left = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    user_id_right = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    
    __table_args__ = (
        CheckConstraint('user_id_left < user_id_right'),
    )

class Order(Base):
    __tablename__ = 'orders'
    
    order_id = Column(Integer, primary_key=True,autoincrement=True)
    amount = Column(Float, nullable=False)
    
    # Relationships
    payments = relationship("CompletedPayment", back_populates="order")
    
    __table_args__ = (
        CheckConstraint('amount > 0'),
    )

class Sessions(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)

    
    # Relationships
    payments = relationship("CompletedPayment", back_populates="session")
    transactions = relationship("InitiatedTransaction", back_populates="session",uselist=True)
    
    __table_args__ = (
        CheckConstraint('timestamp <= CURRENT_TIMESTAMP'),
    )
    
    def is_complete(self):
        # Check if there are any transactions with a generated story
        past_stories_count = sum(1 for t in self.transactions if t.generated_story and isinstance(t, PastStory))
        future_stories_count = sum(1 for t in self.transactions if t.generated_story and isinstance(t, FutureStory))
        lack = "past_story" if past_stories_count<1 else "future_story" if future_stories_count<1 else None
        return lack
    
    
class CompletedPayment(Base):
    __tablename__ = 'completed_payments'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), primary_key=True)
    
    # Relationships
    user = relationship("Users", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    session = relationship("Sessions", back_populates="payments")

class InitiatedTransaction(Base):
    __tablename__ = 'initiated_transactions'
    
    transaction_id = Column(String, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    type = Column(String)
    
    # Relationships
    session = relationship("Sessions", back_populates="transactions")
    api_call = relationship("APICall", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    sbert_call = relationship("SBERTCall", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    generated_story = relationship("GeneratedStory", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

    __mapper_args__ = {
        'polymorphic_identity': 'initiated_transaction',
        'polymorphic_on': type
    }


class APICall(InitiatedTransaction):
    __tablename__ = 'api_calls'
    
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), primary_key=True)
    prompt = Column(String, nullable=False)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="api_call")
    __mapper_args__ = {"polymorphic_identity": "api_call"}

class SBERTCall(InitiatedTransaction):
    __tablename__ = 'sbert_calls'
    
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), primary_key=True)
    corpus = Column(String, nullable=False)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="sbert_call")
    
    __table_args__ = (
        CheckConstraint('length(corpus) > 0'),
    )
    __mapper_args__ = {"polymorphic_identity": "sbert_call"}

class GeneratedStory(Base):
    __tablename__ = 'generated_stories'
    
    story_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), nullable=False)
    generated_story_text = Column(String, nullable=False)
    type = Column(String)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="generated_story")
    past_story = relationship("PastStory", back_populates="generated_story", uselist=False, cascade="all, delete-orphan")
    future_story = relationship("FutureStory", back_populates="generated_story", uselist=False, cascade="all, delete-orphan")
    identifications = relationship("Identified", back_populates="story", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="story", uselist=True, cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('length(generated_story_text) > 0'),
    )
    
    __mapper_args__ = {
        'polymorphic_identity': 'generated_story',
        'polymorphic_on': type
    }
    
class PastStory(GeneratedStory):
    __tablename__ = 'past_stories'
    
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    
    # Relationships
    generated_story = relationship("GeneratedStory", back_populates="past_story", cascade="all, delete")

    __mapper_args__ = {"polymorphic_identity": "past_story"}

class FutureStory(GeneratedStory):
    __tablename__ = 'future_stories'
    
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    wiki_pages = Column(ARRAY(String(255)), nullable=False)
    
    
    # Relationships
    generated_story = relationship("GeneratedStory", back_populates="future_story", cascade="all, delete")
    __mapper_args__ = {"polymorphic_identity": "future_story"}

class WikiReference(Base):
    #corresponds to the cohere wiki reference index
    __tablename__ = 'wiki_references'
    
    wiki_reference_id = Column(String, primary_key=True)
    text_corpus = Column(String, nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    
    
    # Relationships
    identifications = relationship("Identified", back_populates="wiki_reference")
    
class Identified(Base):
    __tablename__ = 'identified'
    
    wiki_reference_id = Column(String, ForeignKey('wiki_references.wiki_reference_id'), primary_key=True)
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    similarity = Column(Float, nullable=False)
    # Relationships
    wiki_reference = relationship("WikiReference", back_populates="identifications")
    story = relationship("GeneratedStory", back_populates="identifications")
