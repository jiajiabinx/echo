
from contextlib import contextmanager
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from psycopg2.extras import RealDictCursor
from app.models import Base, Sessions, GeneratedStory


load_dotenv()
engine = create_engine(os.getenv('DB_URI') )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = SessionLocal()


def init_db():
    """Initialize the database, creating all tables."""
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("Successfully created all tables.")
        
        # Create a session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create a test session to verify connection
        db = SessionLocal()
        try:
            # Try a simple query to verify everything is working
            db.execute(text("SELECT 1"))
            print("Successfully verified database connection.")
        except Exception as e:
            print(f"Error verifying database connection: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

@contextmanager
def get_db_connection():
    conn = engine.connect()
    try:
        yield conn.connection
    except Exception as e:
        conn.rollback()
        raise "Connection Error"
    finally:
        conn.close()
        

def insert_user(user_data):
    query = """
    INSERT INTO Users (display_name, birth_date, birth_location, primary_residence, current_location,
                       college, educational_level, parental_income, primary_interest,
                       profession, religion, race)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING *;
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, (
            user_data['display_name'], user_data['birth_date'], user_data['birth_location'], 
            user_data['primary_residence'], user_data['current_location'], user_data['college'],
            user_data['educational_level'], user_data['parental_income'], user_data['primary_interest'],
            user_data['profession'], user_data['religion'], user_data['race']
        ))
        user = cursor.fetchone()
        conn.commit()
    return user

def update_user(user_data):
    query = """
    UPDATE Users SET 
        display_name = %s,
        birth_date = %s,
        birth_location = %s,
        primary_residence = %s,
        current_location = %s,
        college = %s,
        educational_level = %s,
        parental_income = %s,
        primary_interest = %s,
        profession = %s,
        religion = %s,
        race = %s
    WHERE user_id = %s
    RETURNING *;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    user_data.get('display_name'), user_data.get('birth_date'), user_data.get('birth_location'),
                    user_data.get('primary_residence'), user_data.get('current_location'), user_data.get('college'),
                    user_data.get('educational_level'), user_data.get('parental_income'), user_data.get('primary_interest'),
                    user_data.get('profession'), user_data.get('religion'), user_data.get('race'), user_data.get('user_id')
                ))
                updated_user = cursor.fetchone()
                conn.commit()
        return updated_user
    except Exception as e:
        print(f"Error updating user: {e}")
        return None

def insert_friend(user_id_left, user_id_right):
    query = """
    INSERT INTO Friends (user_id_left, user_id_right)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (min(user_id_left, user_id_right), max(user_id_left, user_id_right)))
            friend = cursor.fetchone()
            conn.commit()
    
    if not friend:
        raise Exception("Friend relationship already exists or invalid user IDs.")
    
    return friend


def get_events_by_story_ids(story_ids: list[int]):
    
    query = f"SELECT * FROM Events WHERE story_id IN ({','.join(map(str, story_ids))});"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            events = cursor.fetchall()
    return events


def get_user_by_id(user_id):
    query = """
    SELECT * FROM Users WHERE user_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
    return user

def create_event(event):
    query = """
    INSERT INTO Events (user_id, story_id, text, annotated_text ,event_type, event_date)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING *;
    """ 
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (event.user_id, event.story_id, event.text, event.annotated_text, event.event_type, event.event_date))
            event = cursor.fetchone()
            conn.commit()
    return event
    


def get_random_users(exclude_ids, limit =5):
    exclude_ids_str = ','.join(map(str, exclude_ids))
    query = f"""
    SELECT * FROM Users 
    WHERE user_id NOT IN ({exclude_ids_str})
    ORDER BY RANDOM() LIMIT %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (limit,))
            random_users = cursor.fetchall()
    return random_users

def get_user_friends(user_id):
    query = """
    SELECT Users.* FROM Users
    INNER JOIN Friends ON (Users.user_id = Friends.user_id_left AND Friends.user_id_right = %s)
                        OR (Users.user_id = Friends.user_id_right AND Friends.user_id_left = %s);
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id, user_id))
            friends = cursor.fetchall()
    
    return friends

def delete_user(user_id):
    query = """
    DELETE FROM Users WHERE user_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            conn.commit()


def insert_order(amount):
    query = """
    INSERT INTO Orders (amount)
    VALUES (%s)
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, ( amount,))
            order = cursor.fetchone()
            conn.commit()
    return order


def check_order_exists(order_id):
    query = """
    SELECT * FROM Orders WHERE order_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (order_id,))
            order = cursor.fetchone()
    return order is not None



def create_session_for_order():
    query = """
    INSERT INTO Sessions (timestamp)
    VALUES (CURRENT_TIMESTAMP)
    RETURNING session_id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            session_id = cursor.fetchone()
            conn.commit()
    return session_id


def create_completed_payment(user_id, order_id, session_id):
    query = """
    INSERT INTO Completed_Payments (user_id, order_id, session_id)
    VALUES (%s, %s, %s)
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id, order_id, session_id))
            completed_payment = cursor.fetchone()
            conn.commit()
    return completed_payment

def record_payment(user_id, order_id):
    if not check_order_exists(order_id):
        raise Exception("Order not found.")
    
    session_id = create_session_for_order()
    
    completed_payment = create_completed_payment(user_id, order_id, session_id)
    
    return completed_payment
        
            

def get_user_historical_sessions(user_id):
    query = """
    SELECT * 
    FROM Users, Completed_Payments, Sessions, Initiated_Transactions, Generated_Stories, Display_Stories
    WHERE Users.user_id = %s
    AND Completed_Payments.user_id = Users.user_id 
    AND Completed_Payments.session_id = Sessions.session_id
    AND Initiated_Transactions.session_id = Completed_Payments.session_id
    AND Generated_Stories.story_id = Display_Stories.story_id
    AND Generated_Stories.transaction_id = Initiated_Transactions.transaction_id;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id,))
            history = cursor.fetchall()
    return history

    
def record_APICall(transaction_id, session_id, prompt):
    record_transaction_query = """
    INSERT INTO Initiated_Transactions (transaction_id, session_id, type)
    VALUES (%s, %s, %s);
    """
    record_API_call_query = """
    INSERT INTO API_Calls (transaction_id, prompt)
    VALUES (%s, %s);
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(record_transaction_query, (transaction_id, session_id, "api_call"))
            cursor.execute(record_API_call_query, (transaction_id, prompt))
            conn.commit()
    return transaction_id

def record_sbert_call(transaction_id, session_id, corpus):
    
    record_transaction_query = """
    INSERT INTO Initiated_Transactions (transaction_id, session_id, type)
    VALUES (%s, %s, %s);
    """
    record_sbert_call_query = """
    INSERT INTO SBERT_Calls (transaction_id, corpus)
    VALUES (%s, %s);
    """
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(record_transaction_query, (transaction_id, session_id, "sbert_call"))
            cursor.execute(record_sbert_call_query, (transaction_id, corpus))
            conn.commit()
    return transaction_id

def insert_past_story(transaction_id, generated_story_text):
    generated_story_query = """
    INSERT INTO Generated_Stories (transaction_id, generated_story_text, type)
    VALUES (%s, %s, 'past_story')
    RETURNING *;
    """
    past_story_query = """
    INSERT INTO Past_Stories (story_id)
    VALUES (%s)
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(generated_story_query, (transaction_id, generated_story_text))
            generated_story = cursor.fetchone()
            cursor.execute(past_story_query, (generated_story['story_id'],))
            past_story = cursor.fetchone()
            conn.commit()
    return past_story

def insert_future_story(transaction_id, generated_story_text, wiki_pages_titles ):
    generated_story_query = """
    INSERT INTO Generated_Stories (transaction_id, generated_story_text, type)
    VALUES (%s, %s, 'future_story')
    RETURNING *;
    """ 
    future_story_query = """
    INSERT INTO Future_Stories (story_id,wiki_pages)
    VALUES (%s, %s);
    """
    get_story_query = """
    SELECT * FROM Generated_Stories, Future_Stories
    WHERE Future_Stories.story_id = %s
    AND Generated_Stories.story_id = Future_Stories.story_id;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(generated_story_query, (transaction_id, generated_story_text,))
            generated_story = cursor.fetchone()
            cursor.execute(future_story_query, (generated_story['story_id'], wiki_pages_titles))
            cursor.execute(get_story_query, (generated_story['story_id'],))
            future_story = cursor.fetchone()
            conn.commit()
    return future_story

def get_all_stories_by_user_id(user_id):
    query = """
    SELECT * 
    FROM Generated_Stories, Initiated_Transactions, Completed_Payments
    WHERE Initiated_Transactions.transaction_id = Generated_Stories.transaction_id
    AND Completed_Payments.session_id = Initiated_Transactions.session_id
    AND Completed_Payments.user_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id,))
            stories = cursor.fetchall()
    return stories

def get_future_story(story_id):
    query = """
    SELECT * 
    FROM Display_Stories, Generated_Stories
    WHERE Display_Stories.story_id = Generated_Stories.story_id
    AND Display_Stories.story_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (story_id,))
            future_story = cursor.fetchone()
    return future_story


def record_identified_relationships(story_id, wiki_reference_ids,similarity_scores):
    query = """
    INSERT INTO Identified (story_id, wiki_reference_id, similarity)
    VALUES (%s, %s, %s)
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            for r,s in zip(wiki_reference_ids,similarity_scores):
                cursor.execute(query, (story_id, r,s))  
            identified_relationships = cursor.fetchall()
            conn.commit()
    return identified_relationships
  
        
def check_payment(user_id, session_id, order_id):
    query = """
    SELECT Sessions.session_id
    FROM Completed_Payments, Sessions
    WHERE Sessions.session_id = Completed_Payments.session_id
    AND Completed_Payments.user_id = :user_id
    AND Completed_Payments.session_id = :session_id
    AND Completed_Payments.order_id = :order_id;
    """
    payment_complete, lack = None, None
    with db_session.begin():
        result = db_session.execute(text(query), {'user_id': user_id, 'session_id': session_id, 'order_id': order_id}).fetchone()
        if result:
            payment_complete = True
            session = db_session.query(Sessions).filter(Sessions.session_id == result[0]).first()
            lack = session.is_complete()
            return payment_complete, lack    
    return None, None

def get_past_story_by_session_id(session_id):
    query = """
        SELECT *
        FROM Past_Stories, Generated_Stories, Initiated_Transactions
        WHERE Generated_Stories.story_id = Past_Stories.story_id
        AND Generated_Stories.transaction_id = Initiated_Transactions.transaction_id
        AND Initiated_Transactions.session_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (session_id,))
            past_story = cursor.fetchone()
    return past_story


def get_story_by_story_id(story_id):
    query = """
    SELECT * FROM  Generated_Stories
    WHERE Generated_Stories.story_id = %s;
    """ 
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (story_id,))
            story = cursor.fetchone()
    return story
    
    
def get_future_story_by_session_id(session_id):
    query = """
        SELECT * 
        FROM Future_Stories, Generated_Stories, Initiated_Transactions
        WHERE Future_Stories.story_id = Generated_Stories.story_id
        AND Generated_Stories.transaction_id = Initiated_Transactions.transaction_id
        AND Initiated_Transactions.session_id = %s
        );
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (session_id,))
            story = cursor.fetchone()
    return story

def get_identified_references_by_future_story_id(future_story_id):
    query = """
    SELECT *
    FROM  Generated_Stories, Identified, Wiki_References
    WHERE Identified.story_id = Generated_Stories.story_id
    AND Wiki_References.wiki_reference_id = Identified.wiki_reference_id
    AND Generated_Stories.story_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (future_story_id,))
            references = cursor.fetchall()
    return references

def get_identified_references_by_session_id(session_id):
    query ="""
    SELECT DISTINCT Wiki_References.*
    FROM  Initiated_Transactions, Generated_Stories, Identified, Wiki_References
    WHERE Initiated_Transactions.transaction_id = Generated_Stories.transaction_id
    AND Identified.story_id = Generated_Stories.story_id
    AND Wiki_References.wiki_reference_id = Identified.wiki_reference_id
    AND Initiated_Transactions.session_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (session_id,))
            identified_references = cursor.fetchall()
    return identified_references

def get_past_story(story_id):
    query = """
    SELECT 
        ts.story_id,
        gs.transaction_id,
        gs.generated_story_text
    FROM Past_Stories ts, Generated_Stories gs
    WHERE ts.story_id = gs.story_id
    AND ts.story_id = %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (story_id,))
            past_story = cursor.fetchone()
    return past_story

def get_random_wiki_references(n):
    query = """
    SELECT * FROM Wiki_References ORDER BY RANDOM() LIMIT %s;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (n,))
            wiki_references = cursor.fetchall()
    return wiki_references

def insert_wiki_reference(wiki_reference_id, text_corpus, url, title):
    query = """
    INSERT INTO wiki_references (wiki_reference_id, text_corpus, url, title)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (wiki_reference_id) DO NOTHING
    RETURNING *;
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (wiki_reference_id, text_corpus, url, title))
            wiki_reference = cursor.fetchone()
            conn.commit()
    return wiki_reference


def delete_story(story_id):
    try:
        story = db_session.query(GeneratedStory).filter(GeneratedStory.story_id == story_id).first()
        db_session.delete(story)
        db_session.commit()
        return {"message": "Story and its related sub-story, event, and identified relationships have been deleted."}
    except Exception as e:
        db_session.rollback()
        raise e


if __name__ == "__main__":
    init_db()