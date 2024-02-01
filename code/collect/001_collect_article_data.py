"""
Purpose: 
    Fetch and processes news articles from various domains using SERP API
    and newspaper3k.

Inputs:
    No script inputs.
    A dataframe with domains and associated Google News publication tokens is
    loaded with constants specified below.

Description:
    The script completes the following steps:
    1. Loads the dataframe with domains and associated Google News publication tokens
    2. Fetches news data from Google news for each domain using the SERP API
        2a. The returned response is stored in a new-line delimited JSON file
    3. Processes each article to extract detailed information using newspaper3k
        3a. The article details are stored in a new-line delimited JSON file


    The script iterates through domains listed in a DataFrame, fetches news data using the SERP API, 
    and then processes each article to extract detailed information using newspaper3k. It includes 
    functions for handling each step of the process and a main function that orchestrates the workflow.

Usage:
    python collect_articles.py

Output:
    The script creates two output new-line delimited JSON files.
    1. SERP_FILE: Each line contains results from the Serp API. Will contain multiple URLs for
        a specific domain.
    2. ARTICLE_FILE: Each line contains a dictionary for a specific URL. Will contain details
        about the article such as title, author, text, etc.

Author: Matthew DeVerna
"""
import datetime
import json
import os
import random
import time

import pandas as pd

# from fake_useragent import UserAgent
from serpapi import GoogleSearch

# from newspaper import Config
from newspaper import Article

# from reliable_db.cookies import COOKIES_MAP
from reliable_db.serp_models import SerpGnewsArticle
from reliable_db.utils import get_class_property_dict, get_dict_val
from reliable_db.utils import collect_last_x_files, random_wait

# Make sure we are in the proper directory for the relative output dirs/files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != CURR_DIR:
    os.chdir(CURR_DIR)


# Input dataframe
SERP_CLEAN_DIR = "../../data/article_data/serp_clean"
DOWNLOADED_LINKS_DIR = "../../data/article_data/downloaded_links"
os.makedirs(DOWNLOADED_LINKS_DIR, exist_ok=True)

# Output files
ARTICLE_RECORDS_DIR = "../../data/article_data/article_results"
os.makedirs(ARTICLE_RECORDS_DIR, exist_ok=True)
ARTICLE_FILE = "article_results.jsonl"
LINKS_FILE = "links.txt"

# Number of days to consider for url cache
NUM_DAYS = 4


def download_article_text(url):
    """
    Use newspaper3k to download the text of an article specified by the url.

    Parameters
    ----------
    - url (str): The URL of the article to download

    Returns
    -------
    article_text (str): The text of the article
    """
    try:
        n3k_article = Article(url)
        n3k_article.download()
        n3k_article.parse()
        return n3k_article.text
    except Exception as e:
        print(f"Error downloading article text: {url}")
        print(e)
        return ""


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


def process_articles(article_records):
    """
    Process a list of articles returned by the SERP API.
    - Downloads the article text, adds it to the article record we already have from SERP
    - Skips articles that have already been downloaded
    - Saves each article record in a new-line delimited JSON file
    - If a new article is downloaded, it is cached to be skipped later

    Parameters
    ----------
    - article_records (list): A list of records for news articles.

    Returns
    -------
    None
    - Downloaded article records are saved in a new-line delimited JSON file.
    - Downloaded links are cached to be skipped later.
    """
    today_str = datetime.date.today().strftime("%Y_%m_%d")
    article_fp = os.path.join(ARTICLE_RECORDS_DIR, f"{today_str}__{ARTICLE_FILE}")
    links_fp = os.path.join(DOWNLOADED_LINKS_DIR, f"{today_str}__{LINKS_FILE}")

    # Load downloaded links to skip, if any
    files = collect_last_x_files(DOWNLOADED_LINKS_DIR, NUM_DAYS)
    downloaded_links_set = load_downloaded_links(files)

    # Open output files for new records and links cache
    with open(article_fp, "a") as f_art, open(links_fp, "a") as f_links:
        try:
            num_records = len(article_records)
            for idx, article in enumerate(article_records, start=1):
                # Be nice, wait on all but first call
                if idx != 1:
                    random_wait()

                print(f"Processing article {idx}/{num_records}")

                link = article["link"]
                print(f"\t- URL: {link}")
                if link in downloaded_links_set:
                    print("\t- Already processed, skipping")
                    continue

                # Download article text, add it to the record
                article["text"] = download_article_text(link)

                # Save article record
                json_line = f"{json.dumps(article)}\n"
                f_art.write(json_line)

                # Save the downloaded link in the cache
                f_links.write(f"{link}\n")

        except Exception as e:
            print(f"Error processing URL <{article['link']}>: {e}")
            print("-" * 50)

    return article_records


if __name__ == "__main__":
    # Load data
    article_record_files = collect_last_x_files(SERP_CLEAN_DIR, NUM_DAYS - 1)

    # Extract records that we may need to process
    article_records = []
    for file in article_record_files:
        article_records.extend(load_article_records(file))

    # Process records, skipping those we already have
    process_articles(article_records)
    print("--- Script Complete ---")
