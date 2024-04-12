"""
Purpose: 
    Summarize article data with OpenAI gpt-3.5-turbo.

Inputs:
    No script inputs.
    Article data and already summarized URLs are loaded with constants.

Description:
    The script completes the following steps:
    1. Loads downloaded news article text data from the past few days.
    2. Loads a set of URLs for articles that have already been summarized.
        2a. URLs that have already been summarized are excluded.
    3. Uses OpenAI (gpt-3.5-turbo) to summarize articles (temperature=0).
        3a. The summary and API call information (tokens utilized, date created, etc)
            are combined with the existing record and saved to a new file for that day
        3b. The URL is stored in a file cache for that day.

Usage:
    python 002_summarize_article_data.py

Output:
    The script creates (or appends to) two new-line delimited files for the day it is run.
    1. LINKS_FILE (.txt): Each line contains a URL that has been summarized
    2. SUMMARY_FILE (.jsonl): Each line contains a dictionary record for a specific article.
        Will contain details about the article such as title, author, text, etc. as well as
        a summary of that article, and information about the OpenAI call.

Author: Matthew DeVerna
"""

import datetime
import json

import os

from tenacity import retry, stop_after_attempt, wait_random_exponential

# Set up OpenAI client
from openai import OpenAI

api_key = os.environ["OPENAI_OSOME_API_KEY"]
openai_client = OpenAI(api_key=api_key)

from reliable_db.utils import (
    collect_last_x_files,
    get_nested_attr,
    trim_text_to_token_limit,
)

# Make sure we are in the proper directory for the relative output dirs/files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != CURR_DIR:
    os.chdir(CURR_DIR)

PROMPT1 = (
    "As a helpful AI assistant, your task will be to summarize text from a news article, "
    "which may contain incomplete sentences, HTML tags, and non-textual elements. "
    "Begin by cleansing the text of any irrelevant content or formatting issues. "
    "Then, craft a concise, neutral summary of the main news article, highlighting key "
    "facts: who, what, when, where, and why. Aim for a one-paragraph summary without "
    "editorializing or subjective interpretation. Adhere strictly to these instructions for an accurate, unbiased summary."
)

# Input dataframe
ARTICLE_RECORDS_DIR = "../../data/article_data/article_results"

# Output files
SUMMARIES_DIR = "../../data/article_data/article_results_summarized"
DOWNLOADED_LINKS_DIR = "../../data/article_data/summarized_links"
os.makedirs(SUMMARIES_DIR, exist_ok=True)
os.makedirs(DOWNLOADED_LINKS_DIR, exist_ok=True)
SUMMARY_FILE = "article_results_summarized.jsonl"
LINKS_FILE = "links.txt"

# Number of days to consider for url cache
NUM_DAYS = 14


# Decorator applies exponentially backoffs to the function, retrying up to six times
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def summarize(article_text, model="gpt-3.5-turbo", raw=True):
    """
    Summarize article text.

    Parameters:
    ------------
    - article_text (str): raw article text scraped from the web.
    - model (str): An OpenAI chat completions model (default = gpt-3.5-turbo)
    - raw (bool): True (default): returns the OpenAI ChatCompletion object directly.
        False: return the summary text only.

    Returns
    ------------
    - If raw == True (default): returns the OpenAI ChatCompletion object directly.
    - If raw == False: return the summary text only.
    """
    try:
        messages = [
            {"role": "system", "content": PROMPT1},
            {"role": "user", "content": f"Article text: {article_text}."},
        ]
        response = openai_client.chat.completions.create(
            model=model, messages=messages, temperature=0
        )
        if raw:
            return response
        content = response.choices[0].message.content
        return content
    except Exception as e:
        print(f"Error: {e}")
        raise


def parse_response(response):
    """
    Parses the OpenAI ChatCompletions response object to extract
    specific keys into a simplified dictionary.

    Parameters:
    ------------
    - response: A OpenAI ChatCompletions response object from OpenAI gpt-3.5-turbo

    Returns:
    -----------
    - clean_response (dict): a parsed version of response
        - keys are:
            - article_summary (str) : text response from OpenAI model
            - finish_reason (str) : why the model stopped. ("stop" is what we want)
            - total_tokens (int): total number of tokens processed in query
            - completion_tokens (int): number of tokens utilized for completiong
            - prompt_tokens (int): number of tokens utilized in prompt
            - time_created (int): unix timestamp of when the query was called
            - model (str): name of the model utilized
    """
    # Initialize the simplified dictionary
    clean_response = {"article_summary": None, "finish_reason": None}

    # Extract the message response
    if hasattr(response, "choices") and len(response.choices) > 0:
        clean_response["article_summary"] = get_nested_attr(
            response.choices[0], ["message", "content"], None
        )
        clean_response["finish_reason"] = get_nested_attr(
            response.choices[0], ["finish_reason"], None
        )

    # Extract query details. Token counts assigned as zero if not found
    clean_response["total_tokens"] = get_nested_attr(
        response, ["usage", "total_tokens"], 0
    )
    clean_response["completion_tokens"] = get_nested_attr(
        response, ["usage", "completion_tokens"], 0
    )
    clean_response["prompt_tokens"] = get_nested_attr(
        response, ["usage", "prompt_tokens"], 0
    )
    clean_response["time_created"] = get_nested_attr(response, ["created"], None)
    clean_response["model"] = get_nested_attr(response, ["model"], None)

    return clean_response


def load_downloaded_links(files):
    """
    Extract URLs from processed article links.

    Parameters
    ----------
    - files (List(str)): List of full paths to link files

    Returns
    ---------
    (list): A list of article urls.
    """
    try:
        urls = set()
        for file in files:
            with open(file, "r") as f:
                for line in f:
                    urls.add(line.rstrip())
        return urls
    except Exception as e:
        print("PROBLEM LOADING EXISTING LINKS!!")
        print(e)
        return set()


def load_article_records(path):
    """
    Load article records to process from a JSONL file.

    Parameters
    ----------
    - path (str): The path to the JSONL file

    Returns
    -------
    list: A list of article records
    """
    try:
        with open(path, "r") as f:
            records = [json.loads(line) for line in f]
            return records
    except Exception as e:
        print("PROBLEM LOADING ARTICLE RECORDS!!")
        print(e)
        return []


def summarize_articles(article_records):
    """
    Summarize a list of downloaded articles with OpenAI.
    - Loads article records from the past few days
    - Skips articles that have already been summarized
    - Saves each article record in a new-line delimited JSON file
    - If a new article is summarized, it is cached to be skipped later

    Parameters
    ----------
    - article_records (list): A list of records for news articles.

    Returns
    -------
    None
    - Summarized article records are saved in a new-line delimited JSON file.
    - Summarized links are cached to be skipped later.
    """
    print("Setting output filenames...")
    today_str = datetime.date.today().strftime("%Y_%m_%d")
    summaries_fp = os.path.join(SUMMARIES_DIR, f"{today_str}__{SUMMARY_FILE}")
    links_fp = os.path.join(DOWNLOADED_LINKS_DIR, f"{today_str}__{LINKS_FILE}")

    # Load downloaded links to skip, if any
    print("Loading cached URLs that have already been summarized...")
    files = collect_last_x_files(path=DOWNLOADED_LINKS_DIR, max_paths=NUM_DAYS)
    downloaded_links_set = load_downloaded_links(files)
    print(f"Number of URLs in cache: {len(downloaded_links_set)}")

    # Open output files for new records and links cache
    with open(summaries_fp, "a") as f_art, open(links_fp, "a") as f_links:
        try:
            num_records = len(article_records)
            print(f"Begin summarizing {num_records} articles...")
            for idx, article in enumerate(article_records, start=1):

                print(f"Processing article {idx}/{num_records}")

                link = article["link"]
                print(f"\t- URL: {link}")
                if link in downloaded_links_set:
                    print("\t- Already summarized, skipping")
                    continue

                # Extract article text, ensure it is not too long for OpenAI
                article_text = article["text"]
                trimmed_text = trim_text_to_token_limit(article_text)

                # Make request, parse response and add to the record
                response = summarize(article_text=trimmed_text, raw=True)
                parsed_response = parse_response(response)
                article.update(parsed_response)

                # Save article record
                json_line = f"{json.dumps(article)}\n"
                f_art.write(json_line)

                # Save the downloaded link in the cache
                f_links.write(f"{link}\n")

        except Exception as e:
            print(f"Error processing URL <{article['link']}>: {e}")
            print("-" * 50)

    return


if __name__ == "__main__":
    print("-" * 50)
    print("Start article summarization script.")
    print("-" * 50)

    print("Prompt:")
    print(PROMPT1)
    print("-" * 50)

    # Load data
    article_record_files = collect_last_x_files(
        path=ARTICLE_RECORDS_DIR, max_paths=NUM_DAYS
    )
    print("Article files to be processed:", *article_record_files, sep="\n- ")
    print("-" * 50)

    # Extract records that we may need to process
    article_records = []
    for file in article_record_files:
        article_records.extend(load_article_records(file))
    print(f"Number of records: {len(article_records)}")
    print("-" * 50)

    # Process records, skipping those we already have
    summarize_articles(article_records)
    print("--- Script Complete ---")
