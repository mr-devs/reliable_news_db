"""
Purpose: 
    Fetch and processes news articles from various domains using SERP API
    and newspaper3k.

NOTE: DO NOT USE THIS SCRIPT. THIS SCRIPT IS BEING STORED AS A BACKUP OF FUNCTIONALITY
    THAT USES COOKIES, MANUAL REQUESTS, AND OTHER APPROACHES TO GET AROUND TRICKY DOMAINS.
    WE MAY NEED IT DOWN THE LINE BUT DO NOT AT THIS POINT IN TIME.

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
import requests
import time
import tldextract

import pandas as pd

from fake_useragent import UserAgent
from serpapi import GoogleSearch
from newspaper import Config
from newspaper import Article

from reliable_db.cookies import COOKIES_MAP
from reliable_db.serp_models import SerpGnewsArticle
from reliable_db.utils import get_class_property_dict

# Make sure we are in the proper directory for the relative output dirs/files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != CURR_DIR:
    os.chdir(CURR_DIR)

# Request parameters for fake_useragent
OS = "macos"
fake_user_agent = UserAgent(os="macos")

# Input dataframe
DATA_DIR = "../../data/domains/"
DOMAINS_FILE = "selected_reliable_domains.csv"
DOMAINS_PATH = os.path.join(DATA_DIR, DOMAINS_FILE)

# Output files
OUT_DIR = "../../data/article_data/serp"
os.makedirs(OUT_DIR, exist_ok=True)
SERP_FILE = "serp_results.jsonl"
ARTICLE_FILE = "article_results.jsonl"

# Set API key
SERP_API_KEY = os.environ.get("SERP_API_KEY")
if not SERP_API_KEY:
    raise ValueError("Missing SERP_API_KEY environment variable.")


def fetch_serp_data(api_key, gnews_pub_token):
    """
    Fetches data from the SERP API for a given domain using that domains
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
    serp_data = fetch_serp_data("your_api_key", "example.com", "publication_token")
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


def random_wait(min=1, max=5):
    """
    Sleeps for a random amount of time between min+1 and max+1 seconds.
    """
    if not all(isinstance(item, int) for item in (min, max)):
        raise ValueError("min and max must be integers.")

    random_wait = 1 + random.uniform(min, max)
    print(f"\t- Sleeping for {random_wait:.2f} seconds.")
    time.sleep(random_wait)


def process_articles(articles):
    """
    Process a list of articles returned by the SERP API.

    Notes:
    - Downloads content from each article one by one with newspaper3k.
    - Parses content with the SerpGnewsArticle class.
    - Saves each article record in a new-line delimited JSON file.

    Parameters
    ----------
    - articles (list): A list of Google News articles returned by the SERP API to process.

    Returns
    -------
    list: A list of dictionaries, each containing details of an article.

    Examples
    --------
    processed_articles = process_articles(article_list)
    """
    today_str = datetime.date.today().strftime("%Y_%m_%d")
    article_fp = os.path.join(OUT_DIR, f"{today_str}__{ARTICLE_FILE}")

    article_records = []
    with open(article_fp, "a") as f_art:
        try:
            for idx, article in enumerate(articles[:2], start=1):
                print(f"\t- Processing article {idx}/{len(articles)}")
                print(f"\t\t- URL: {article['link']}")

                serp_article = SerpGnewsArticle(article)
                article_record = get_article_details(serp_article)

                json_line = f"{json.dumps(article_record)}\n"
                f_art.write(json_line)

                # Be nice, don't get banned. :P
                random_wait()
        except Exception as e:
            print(f"Error processing URL <{article['link']}>: {e}")
            print("-" * 50)

    return article_records


def make_request(url):
    """
    Make request, with manually collected cookies, if present.

    Parameters
    ----------
    - url (str): The URL to fetch.

    Returns
    -------
    requests.Response: The response object.
    """
    try:
        # Use requests to fetch the web page
        extracted = tldextract.extract(url)
        domain = ".".join([extracted.domain, extracted.suffix])
        if COOKIES_MAP.get(domain, None):
            response = requests.get(
                url,
                cookies=COOKIES_MAP[domain],
                headers={
                    "user-agent": fake_user_agent.random,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )
        else:
            response = requests.get(
                url,
                headers={
                    "user-agent": fake_user_agent.random,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )
    except Exception as e:
        raise Exception(f"Error fetching URL <{url}>: {e}")
    return response


def get_article_details(serp_article):
    """
    Given a SerpGnewsArticle, download and extract the article details.

    Parameters
    ----------
    - serp_article (SerpGnewsArticle): SerpGnewsArticle class based on SERP API response.
        Keys included: ['position', 'title', 'source', 'link', 'thumbnail', 'date']

    Returns
    -------
    article_record (dict): The article record.
        - Keys include:
            ['authors', 'gnews_position', 'link', 'publisher', 'serp_date',
            'title', 'text', 'article_text', 'article_html', 'n3k_publish_date']
        - See the SerpGnewsArticle class for more details.

    Examples
    --------
    article_details = get_article_details(article)
    """
    # Download the article using cookies, if present
    url = serp_article.link
    response = make_request(url)

    # Parse the article using newspaper3k
    n3k_article = Article(url="")
    n3k_article.set_html(response.text)
    n3k_article.parse()

    # Build the article record
    article_record = get_class_property_dict(serp_article)  # Creates dict

    article_record["article_text"] = None
    if n3k_article.text:
        article_record["article_text"] = n3k_article.text

    article_record["n3k_publish_date"] = None
    if n3k_article.publish_date:
        article_record["n3k_publish_date"] = n3k_article.publish_date.timestamp()

    article_record["article_html"] = None
    if n3k_article.html:
        article_record["article_html"] = n3k_article.html

    return article_record


def main(quality_domains_df, api_key):
    """
    Main function to orchestrate the fetching and processing of articles from multiple domains.

    Parameters
    ----------
    - quality_domains_df (DataFrame): A pandas DataFrame containing the domains and their
        respective Google News publisher tokens.
            - Ref: https://serpapi.com/playground?engine=google_news
    - api_key (str): The API key for SerpAPI.

    Returns
    -------
    tuple: A tuple containing the SERP results (dict) and all article records (list).

    Examples
    --------
    serp_results, all_article_records = main(dataframe, "your_api_key")
    """

    num_domains = len(quality_domains_df)
    for idx, row in quality_domains_df.iterrows():
        # Update SERP_FILE and ARTICLE_FILE to include current date
        today_str = datetime.date.today().strftime("%Y_%m_%d")
        serp_fp = os.path.join(OUT_DIR, f"{today_str}__{SERP_FILE}")

        with open(serp_fp, "a") as f_serp:
            try:
                print(f"Source {idx + 1}/{num_domains}: {row.domain}...")
                results = fetch_serp_data(api_key, row.gnews_pub_token)
                json_line = f"{json.dumps(results)}\n"
                f_serp.write(json_line)

                if not results.get("news_results", None):
                    print("*** No news results found. ***")
                    continue

                else:
                    print(f"\t- Num results found: {len(results['news_results'])}")
                    articles = results["news_results"]
                    print(f"\t- Num articles found: {len(articles)}")
                    process_articles(articles)

                print("Done collecting data for this domain.")
                print("-" * 50)

            except Exception as e:
                print(f"Error processing domain {row.domain}: {e}")
                print("-" * 50)


if __name__ == "__main__":
    quality_domains_df = pd.read_csv(DOMAINS_PATH)
    main(quality_domains_df, SERP_API_KEY)
