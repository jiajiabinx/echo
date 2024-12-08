
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, CheckConstraint
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

class Session(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    
    # Relationships
    payments = relationship("CompletedPayment", back_populates="session")
    transactions = relationship("InitiatedTransaction", back_populates="session")
    
    __table_args__ = (
        CheckConstraint('timestamp <= CURRENT_TIMESTAMP'),
    )

class CompletedPayment(Base):
    __tablename__ = 'completed_payments'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), primary_key=True)
    
    # Relationships
    user = relationship("Users", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    session = relationship("Session", back_populates="payments")

class InitiatedTransaction(Base):
    __tablename__ = 'initiated_transactions'
    
    transaction_id = Column(String, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    
    # Relationships
    session = relationship("Session", back_populates="transactions")
    api_call = relationship("APICall", back_populates="transaction", uselist=False)
    sbert_call = relationship("SBERTCall", back_populates="transaction", uselist=False)
    generated_story = relationship("GeneratedStory", back_populates="transaction", uselist=False)

class APICall(InitiatedTransaction):
    __tablename__ = 'api_calls'
    
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), primary_key=True)
    prompt = Column(String, nullable=False)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="api_call")
    __mapper_args__ = {"polymorphic_identity": "APICall", "polymorphic_load": "inline"}

class SBERTCall(InitiatedTransaction):
    __tablename__ = 'sbert_calls'
    
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), primary_key=True)
    corpus = Column(String, nullable=False)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="sbert_call")
    
    __table_args__ = (
        CheckConstraint('length(corpus) > 0'),
    )
    __mapper_args__ = {"polymorphic_identity": "SBERTCall", "polymorphic_load": "inline"}

class GeneratedStory(Base):
    __tablename__ = 'generated_stories'
    
    story_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), nullable=False)
    generated_story_text = Column(String, nullable=False)
    
    # Relationships
    transaction = relationship("InitiatedTransaction", back_populates="generated_story")
    temp_story = relationship("TempStory", back_populates="original_story", uselist=False)
    display_story = relationship("DisplayStory", back_populates="original_story", uselist=False)
    references = relationship("Referred", back_populates="story")
    identifications = relationship("Identified", back_populates="story")

class TempStory(GeneratedStory):
    __tablename__ = 'temp_stories'
    
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    generated_story_text = Column(String, nullable=False)
    
    # Relationships
    original_story = relationship("TempStory", back_populates="temp_story")
    
    __table_args__ = (
        CheckConstraint('length(generated_story_text) > 0'),
    )
    
    __mapper_args__ = {"polymorphic_identity": "user", "polymorphic_load": "inline"}

class DisplayStory(GeneratedStory):
    __tablename__ = 'display_stories'
    
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    generated_story_text = Column(String, nullable=False)
    references = Column(String, nullable=False)
    reference_summary = Column(String, nullable=False)
    
    # Relationships
    original_story = relationship("GeneratedStory", back_populates="display_story")
    __mapper_args__ = {"polymorphic_identity": "DisplayStory", "polymorphic_load": "inline"}

class Referred(Base):
    __tablename__ = 'referred'
    
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    transaction_id = Column(String, ForeignKey('initiated_transactions.transaction_id'), primary_key=True)
    
    # Relationships
    story = relationship("GeneratedStory", back_populates="references")

class WikiReference(Base):
    __tablename__ = 'wiki_references'
    
    wiki_page_id = Column(String, primary_key=True)
    text_corpus = Column(String, nullable=False)
    url = Column(String, nullable=False)
    
    # Relationships
    identifications = relationship("Identified", back_populates="wiki_reference")
    
    __table_args__ = (
        CheckConstraint("url LIKE 'https://en.wikipedia.org/wiki/%'"),
    )

class Identified(Base):
    __tablename__ = 'identified'
    
    wiki_page_id = Column(String, ForeignKey('wiki_references.wiki_page_id'), primary_key=True)
    story_id = Column(Integer, ForeignKey('generated_stories.story_id'), primary_key=True)
    
    # Relationships
    wiki_reference = relationship("WikiReference", back_populates="identifications")
    story = relationship("GeneratedStory", back_populates="identifications")
    