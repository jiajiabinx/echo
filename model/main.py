import csv
import spacy
import wikipedia
import re
import logging
from datasets import Dataset
import json
from pathlib import Path
import time
from datetime import datetime

# Set up logging
log_filename = f"log/wikipedia_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)

# Load spaCy model
logger.info("Loading spaCy model")
nlp = spacy.load("en_core_web_sm")

def fetch_wikipedia_article_by_curid(curid):
    try:
        logger.info(f"Fetching Wikipedia page for curid: {curid}")
        page = wikipedia.page(pageid=curid)
        logger.info(f"Successfully fetched page: {page.title}")
        return page
    except wikipedia.exceptions.PageError:
        logger.error(f"Page not found for curid: {curid}")
        return None
    except wikipedia.exceptions.DisambiguationError as e:
        logger.error(f"Disambiguation error for curid: {curid}, options: {e.options}")
        return None
    except Exception as e:
        logger.error(f"An error occurred for curid: {curid}, error: {str(e)}")
        return None

def clean_wikipedia_content(content):
    # Remove section titles (e.g., == Biography ==)
    cleaned_content = re.sub(r'==+\s*[^=]+\s*==+', '', content)
    
    # Replace multiple consecutive newlines with a single space
    cleaned_content = re.sub(r'\n+', ' ', cleaned_content)
    
    # Replace multiple consecutive spaces with a single space
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    
    # Remove any leading or trailing whitespace
    cleaned_content = cleaned_content.strip()
    
    return cleaned_content

def process_text(text):
    # Clean the content to remove section titles and excess whitespace
    cleaned_text = clean_wikipedia_content(text)
    
    logger.info(f"Processing text of length: {len(cleaned_text)} characters")
    doc = nlp(cleaned_text)
    results = []

    for i, sent in enumerate(doc.sents):
        sentence = sent.text.strip()
        
        # Skip empty sentences or sentences that are just whitespace
        if not sentence:
            continue

        # Extract entities and their syntactic roles
        entities_with_roles = [
            {'entity': ent.text, 'label': ent.label_, 'syntactic_role': ent.root.dep_}
            for ent in sent.ents
        ]

        # Extract date entities
        date_entities = [ent.text for ent in sent.ents if ent.label_ == "DATE"]
        date_string = ", ".join(date_entities) if date_entities else None

        # Find the main verb (predicate) and get its lemma
        predicate_lemma = None
        for token in sent:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                predicate_lemma = token.lemma_
                break
        if predicate_lemma is None:
            continue
        else:
            results.append({
                'text': sentence,
                'predicate_lemma': predicate_lemma,
                'entities_with_roles': entities_with_roles,
                'narrative_sequence': i,
                'date': date_string
            })

    logger.info(f"Processed {len(results)} sentences with predicates")
    return results

def list_of_dicts_to_dict_of_lists(list_of_dicts):
    # Initialize a dictionary to store the result
    dict_of_lists = {}
    
    # If the list is empty, return an empty dictionary
    if not list_of_dicts:
        return dict_of_lists
    
    # Get all keys from the first dictionary
    keys = list_of_dicts[0].keys()
    
    # Initialize empty lists for each key
    for key in keys:
        dict_of_lists[key] = []
    
    # Append values from each dictionary to the corresponding list
    for d in list_of_dicts:
        for key in keys:
            dict_of_lists[key].append(d.get(key, None))
    
    return dict_of_lists

def main():
    start_time = time.time()
    logger.info("Starting Wikipedia processing script")
    
    # Create directory for dataset if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Open the CSV file
    csv_path = 'data/cross-verified-database.csv'
    logger.info(f"Opening CSV file: {csv_path}")
    
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            batch_size = 100  # Define the batch size
            batch = []
            batch_count = 0
            max_rows = 5  # Limit the number of rows to process
            row_count = 0
            processed_count = 0
            skipped_count = 0

            for row in reader:
                if row_count >= max_rows:
                    logger.info(f"Reached max rows limit ({max_rows})")
                    break

                row_count += 1
                logger.info(f"Processing row {row_count}: {row.get('name', 'Unknown')}")

                if row['death']:  # Check if death date is not null
                    curid = row['curid']
                    name = row['name']
                    page = fetch_wikipedia_article_by_curid(curid)

                    if page:
                        # Process the entire page content
                        processed_sentences = process_text(page.content)
                        sentence_count = len(processed_sentences)
                        logger.info(f"Extracted {sentence_count} sentences with predicates from page: {name}")
                        
                        for sentence_info in processed_sentences:
                            sentence_info['curid'] = curid
                            sentence_info['name'] = name
                            batch.append(sentence_info)

                            if len(batch) >= batch_size:
                                logger.info(f"Saving batch {batch_count} with {len(batch)} sentences")
                                # Convert list of dictionaries to dictionary of lists
                                batch_dict = list_of_dicts_to_dict_of_lists(batch)
                                # Create a Hugging Face Dataset
                                dataset = Dataset.from_dict(batch_dict)
                                # Save the dataset to disk
                                save_path = f"data/wikipedia_srl_dataset_batch_{batch_count}"
                                dataset.save_to_disk(save_path)
                                logger.info(f"Saved batch to {save_path}")
                                batch_count += 1
                                batch = []  # Reset the batch
                        
                        processed_count += 1
                    else:
                        logger.warning(f"Could not fetch Wikipedia page for {name} (curid: {curid})")
                        skipped_count += 1
                else:
                    logger.info(f"Skipping {row.get('name', 'Unknown')} - no death date")
                    skipped_count += 1

            # Save any remaining data in the last batch
            if batch:
                logger.info(f"Saving final batch {batch_count} with {len(batch)} sentences")
                # Convert list of dictionaries to dictionary of lists
                batch_dict = list_of_dicts_to_dict_of_lists(batch)
                # Create a Hugging Face Dataset
                dataset = Dataset.from_dict(batch_dict)
                # Save the dataset to disk
                save_path = f"data/wikipedia_srl_dataset_batch_{batch_count}"
                dataset.save_to_disk(save_path)
                logger.info(f"Saved batch to {save_path}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Script completed in {elapsed_time:.2f} seconds")
            logger.info(f"Total rows processed: {row_count}")
            logger.info(f"Successfully processed: {processed_count}")
            logger.info(f"Skipped: {skipped_count}")
            logger.info(f"Total batches saved: {batch_count + (1 if batch else 0)}")
            
    except Exception as e:
        logger.error(f"An error occurred during execution: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()