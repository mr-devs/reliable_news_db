"""
Purpose: 
    Fetch news articles from various domains using SERP API.
    Saves all SERP results but only saves new article URLs.

Inputs:
    No script inputs.
    A dataframe with domains and associated Google News publication tokens is
    loaded with constants specified below.

Description:
    The script completes the following steps:
    1. Loads a dataframe with domains and associated Google News publication tokens
    2. Loads URLs already gathered in recent queries as a set
    3. Fetches news data from Google news for each domain using the SERP API
        3a. All SERP results are stored in a new-line delimited JSON file
        3b. URLS are stored in a new-line delimited text file, only new URLs are saved

Usage:
    python collect_gnews_links.py

Output:
    The script creates two files.
        1. SERP_FILE: Each line contains results from the Serp API. Will contain multiple URLs for
            a specific domain.
        2. LINKS_FILE: Each line contains one URL.
    All files are:
        - Saved in the data/article_data/{SERP/LINKS_DIR}
        - Filenames are prefixed with today's date YYYY_MM_DD

Author: Matthew DeVerna
"""

import datetime
import json
import os

import pandas as pd
from serpapi import GoogleSearch

from reliable_db.utils import collect_last_x_files, random_wait, get_class_property_dict
from reliable_db.serp_models import SerpGnewsArticle

# Make sure we are in the proper directory for the relative output dirs/files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != CURR_DIR:
    os.chdir(CURR_DIR)


# Input dataframe
DATA_DIR = "../../data/domains/"
DOMAINS_FILE = "easy_domains.csv"
DOMAINS_PATH = os.path.join(DATA_DIR, DOMAINS_FILE)

# Output files
SERP_RAW_DIR = "../../../raw_data/article_data/serp_raw"
SERP_CLEAN_DIR = "../../../raw_data/article_data/serp_clean"
os.makedirs(SERP_RAW_DIR, exist_ok=True)
os.makedirs(SERP_CLEAN_DIR, exist_ok=True)
SERP_RAW_FILE = "serp_raw_results.jsonl"
SERP_CLEAN_FILE = "serp_clean_records.jsonl"

# Number of days to consider for url cache
NUM_DAYS = 14

# Set API key
SERP_API_KEY = os.environ.get("SERP_API_KEY")
if not SERP_API_KEY:
    raise ValueError("Missing SERP_API_KEY environment variable.")


def build_existing_links_set(files):
    """
    Builds a set of URLs already gathered in recent queries.

    Parameters
    ----------
    - files (list): list of full paths to link files

    Returns
    -------
    set: A set of URLs already gathered in recent queries.
    """
    urls = set()
    try:
        for file in files:
            with open(file, "r") as f:
                for line in f:
                    record = json.loads(line)
                    urls.add(record["link"])
        return urls
    except Exception as e:
        print("PROBLEM LOADING EXISTING LINKS!!")
        print(e)


def fetch_serp_data(api_key, gnews_pub_token):
    """
    Fetches data from the SERP API for a given domain using that domain's
    associated "publisher token" for the Google News engine.

    Parameters
    ----------
    - api_key (str): The API key for SerpAPI.
    - gnews_pub_token (str): Google News publication token for the domain.
        - Ref: https://serpapi.com/playground?engine=google_news

    Returns
    -------
    dict: A dictionary containing the fetched data from SERP API.

    Examples
    --------
    serp_data = fetch_serp_data("your_api_key", "publication_token")
    """
    if not isinstance(api_key, str):
        raise ValueError("api_key must be a string.")
    if not isinstance(gnews_pub_token, str):
        raise ValueError("gnews_pub_token must be a string.")

    params = {
        "api_key": api_key,
        "engine": "google_news",
        "gl": "us",
        "publication_token": gnews_pub_token,
    }
    search = GoogleSearch(params)
    return search.get_dict()


def extract_links(news_results):
    """
    Extract URLs from Serp results.

    Parameters
    ----------
    - news_results (list): A list of dictionaries containing the fetched data from SERP API.
        This should be the item in the "news_results" key in the raw SERP API payload.

    Returns
    ---------
    (list): A list of article urls.
    """
    try:
        return [article["link"] for article in news_results]
    except Exception as e:
        print(f"ERROR! NO LINKS IN 'serp_results['news_results']'!")
        print(e)
        return []


def main(quality_domains_df, api_key):
    """
    Main function to orchestrate the fetching and processing of articles from multiple domains.
    This function will download data from the SERP API and save that raw data to a new-line
    delimited JSON file where each line represents one SERP response.
    Afterward, the raw data from that response is processed and saved to a separate new-line delimited
    file. Each line of this file will represent a record for a single article.

    Parameters
    ----------
    - quality_domains_df (DataFrame): A pandas DataFrame containing the domains and their
        respective Google News publisher tokens. Must contain the following columns:
        - 'domain': The domain name
        - 'gnews_pub_token': The Google News publication token associated with the domain for Serp
            - Serp Ref: https://serpapi.com/playground?engine=google_news
    - api_key (str): The API key for SerpAPI.

    Returns
    -------
    None
    Saves two files:
    - SERP_RAW_FILE: Each line contains results from the Serp API.
    - SERP_CLEAN_FILE: Each line contains a record for a single article.

    Examples
    --------
    serp_results, all_article_records = main(dataframe, "your_api_key")
    """
    # Update output files to include current date/time
    today_str = datetime.date.today().strftime("%Y_%m_%d")
    serp_fp = os.path.join(SERP_RAW_DIR, f"{today_str}__{SERP_RAW_FILE}")
    serp_clean_fp = os.path.join(SERP_CLEAN_DIR, f"{today_str}__{SERP_CLEAN_FILE}")

    # Ignore links from past days
    files = collect_last_x_files(path=SERP_CLEAN_DIR, max_paths=NUM_DAYS)
    existing_links = build_existing_links_set(files)

    print(f"Existing links (from last {NUM_DAYS} days): {len(existing_links)}")

    num_domains = len(quality_domains_df)
    for idx, row in quality_domains_df.iterrows():
        print(f"Source {idx + 1}/{num_domains}: {row.domain}...")

        # Be nice by waiting, except for first call.
        if idx != 0:
            random_wait()

        with open(serp_fp, "a") as f_serp:
            try:
                results = fetch_serp_data(api_key, row.gnews_pub_token)
                json_line = f"{json.dumps(results)}\n"
                f_serp.write(json_line)

                if not results.get("news_results", None):
                    print("\t - *** No news results found. ***")
                    continue

                else:
                    new_article_cnt = 0
                    with open(serp_clean_fp, "a") as f_serp_clean:
                        for result in results["news_results"]:
                            # Ingest the article data with the class and convert it to a dict
                            serp_obj = SerpGnewsArticle(result)
                            record = get_class_property_dict(serp_obj)

                            # Ignore if it has already been saved
                            if record["link"] in existing_links:
                                continue

                            # Otherwise, add domain/publisher token and save
                            record.update(
                                {"domain": row.domain, "pub_token": row.gnews_pub_token}
                            )
                            json_line = f"{json.dumps(record)}\n"
                            f_serp_clean.write(json_line)
                            new_article_cnt += 1

                    print(f"\t- New links added: {new_article_cnt}")

            except Exception as e:
                print(f"Error processing domain {row.domain}: {e}")
                print("-" * 50)


if __name__ == "__main__":
    quality_domains_df = pd.read_csv(DOMAINS_PATH)
    main(quality_domains_df, SERP_API_KEY)
    print("--- Script Complete ---")
