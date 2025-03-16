
from fastapi.templating import Jinja2Templates
import cohere
import os
import dotenv
import json
from pinecone.grpc import PineconeGRPC as pinecone
from openai import OpenAI
from openai import BadRequestError
import wikipediaapi
import logging
import absl.logging
import spacy
from sklearn.manifold import TSNE

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF logging
logging.getLogger('absl').setLevel(logging.ERROR)  # Suppress absl logging
absl.logging.set_verbosity(absl.logging.ERROR)  # Suppress absl logging
logging.root.removeHandler(absl.logging._absl_handler)  # Remove absl handler
nlp = spacy.load("en_core_web_sm")
tsne = TSNE(n_components=3, random_state=42, perplexity=3) #n_components is the number of dimensions to reduce to


dotenv.load_dotenv()
wiki = wikipediaapi.Wikipedia(user_agent="echo-project-1",language='en')


pc = pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))
templates = Jinja2Templates(directory="templates")
deepseek_ai_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),base_url="https://api.deepseek.com")
open_ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def generate_past_story(user_str):
    json_str = user_str.replace('""', '"')
    user = json.loads(json_str)    
    fields_to_include = [
    "display_name",'birth_date', 'birth_location', 'primary_residence', 'current_location',
    'college', 'educational_level', 'parental_income', 'primary_interest',
    'profession', 'religion', 'race'
    ]

    clean_str = ", ".join(f"{field.replace('_', ' ')}: {user[field]}" 
                            for field in fields_to_include)

    messages = [
    {"role": "system", "content": "You are a wikipedia writer. You are given some basic information of a person and you are asked to write a wikipedia page about them. "},
    {"role": "user", "content": "This is the basic information of the person: " + clean_str},
    {"role": "user", "content": "Be factual. Do not include any other inferred information in the article."},
    {"role": "user", "content": "Break the article into paragraphs with a maximum of 250 words per paragraph."},
    {"role": "user", "content": "With parental income, do not include the numerical income in the article. Just mention the income level."}
    ]
    response = deepseek_ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )
    story_text = response.choices[0].message.content
    story_text = clean_story_text(story_text)
    return story_text

def clean_story_text(story_text):
    # Split into paragraphs first
    paragraphs = story_text.split('\n\n')
    
    clean_paragraphs = []
    for paragraph in paragraphs:
        # Split paragraph into sentences
        sentences = paragraph.split('.')
        # Clean sentences in this paragraph
        clean_sentences = [
            s.strip() 
            for s in sentences 
            if s.strip() and not s.strip().startswith(('#', '*'))
        ]
        # Rejoin sentences in this paragraph
        if clean_sentences:
            clean_paragraphs.append('. '.join(clean_sentences))
    
    # Rejoin paragraphs with double newlines
    return '\n\n'.join(clean_paragraphs)

def deepseek_check(content):
    try:
        response = open_ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Check if the following content contains any sensitive information: " + content}],
            stream=False
        )
    except BadRequestError as e:
        if e.code == 400 and "Content Exists Risk" in str(e):
            return True
        else:
            raise e
    return False


def get_similar_stories(story_text, n):
    paragraphs = break_down_story(story_text)
    embeddings = [get_embeddings(paragraph) for paragraph in paragraphs]
    all_matches = []
    for paragraph in embeddings:
        response = index.query(paragraph, top_k=n,include_metadata=True)
        all_matches.extend(response.matches)
    return all_matches

def break_down_story(story_text):
    paragraphs = story_text.split("\n")
    return paragraphs
    
def get_embeddings(text):
    co = cohere.Client(os.getenv("COHERE_API_KEY"))
    response = co.embed(
        texts=[text],
        model='multilingual-22-12'
    )
    return response.embeddings[0]
    
def filter_for_human(wiki_page):
    categories = list(wiki_page.categories.keys())
    str_categories = " ".join(categories)
    if "People " in str_categories or "Person" in str_categories:
        return True
    return False

def get_full_wiki_page(title):
    page = wiki.page(title)
    sections = get_all_sections(page.sections)
    full_page_text = "\n".join(sections)
    return full_page_text

def get_all_sections(sections,level=0):
    result = []
    for s in sections:
        if s.title in ["See also", "References", "External links", "Further reading", "Notes and references", "Bibliography", "Sources", "Literature", "Footnotes", "Works cited", "Citations", "Photo gallery", "Quotations", "External media", "Related topics", "Related articles", "Further reading", "References", "External links", "Further reading", "Notes and references", "Bibliography", "Sources", "Literature", "Footnotes", "Works cited", "Citations", "Photo gallery", "Quotations", "External media", "Related topics", "Related articles", "Further reading", "References", "External links", "Further reading", "Notes and references", "Bibliography", "Sources", "Literature", "Footnotes", "Works cited", "Citations", "Photo gallery", "Quotations", "External media", "Related topics", "Related articles", "Further reading"]:
            break
        result.append("%s: %s - %s" % ("*" * (level + 1), s.title, s.text))
        result.extend(get_all_sections(s.sections, level + 1))
    return result

def process_wiki_references(wiki_references):
    seen = set()
    wiki_references_full_text = ""
    wiki_references_titles = []

    for wiki_reference in wiki_references:
        if wiki_reference.title not in seen:
            seen.add(wiki_reference.title)
            full_text = get_full_wiki_page(wiki_reference.title)
            wiki_references_full_text += "\n" + full_text
            wiki_references_titles.append(wiki_reference.title)
            
            
            
    return wiki_references_full_text, wiki_references_titles



if __name__ == "__main__":
    story_text ="Born in Suzhou, China, Jiajiabinx has developed a strong interest in the intersection of artificial intelligence (AI) and art, blending technology with creative expression. Currently pursuing an MBA, Jiajiabinx is focused on exploring innovative ways to integrate AI into artistic and business practices\n\nGrowing up in a family with a modest income, Jiajiabinx developed a passion for learning and creativity from an early age. After completing secondary education, Jiajiabinx moved to the United States to attend Williams College, a prestigious liberal arts institution. At Williams, Jiajiabinx earned a Bachelor’s degree, laying the foundation for a career that combines analytical thinking with artistic exploration\n\nJiajiabinx’s primary interest lies in the intersection of AI and art, exploring how artificial intelligence can be used to enhance artistic expression and innovation. This unique blend of interests reflects Jiajiabinx’s commitment to bridging the gap between technology and creativity\n\nThe move from Suzhou to New York has allowed Jiajiabinx to immerse in a diverse cultural environment, further enriching personal and professional perspectives. Jiajiabinx continues to reside in New York, where the vibrant art and tech scenes provide ample opportunities for growth and exploration"
    matches = get_similar_stories(story_text, 15)
    matches =sorted(matches, key=lambda x: x["score"], reverse=True)
    wiki_references_ids = []
    for match in matches:
        page = wiki.page(match["metadata"]["title"])
        if filter_for_human(page):
            print(page.title)
            print(match["score"])
            



