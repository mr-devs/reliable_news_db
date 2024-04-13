"""
Purpose: 
    Update a vector database with new records.

Inputs:
    No script inputs.
    Article data and summaries loaded with constants.

Description:
    The script completes the following steps:
    1. Create (or load) a collection based on the parameters (distance,
        splitting, etc.) defined by CL flags. These parameters can be accesed by
        calling `collections.metadata`.
    2. Load article summary data.
    3. Remove duplicates with the loaded data (based on article URL).
    4. Retrieve articles based on these URLs from the collection. Anything that is returned
        is necessary already in there, so they are excluded so as to not create duplicates.
    5. If new summaries remain:
        5a. Handle text splitting, as defined by the CL flags.
            - If a summary is split, the metadata fields are duplicated to all documents
        5a. Add documents to the collection.

Usage:
    python update_vdb.py

Output:
    Creates (or updates) the Chroma collection as defined by the CL flags.

Author: Matthew DeVerna
"""

import sys
import argparse
import chromadb
import json

import pandas as pd

from langchain.text_splitter import RecursiveCharacterTextSplitter
from nltk.tokenize import sent_tokenize
from reliable_db.utils import collect_last_x_files

CHROMA_DIR = "/home/data/apps/llm_facebook_browser_extension/vector_dbs"
SUMMARIES_DIR = (
    "/home/mdeverna/reliable_news_db/data/article_data/article_results_summarized"
)
METADATA_COLUMNS = [
    "link",
    "domain",
    "publisher",
    "serp_date",
    "title",
]


def parse_command_line_flags():
    """
    Parses command line flags for configuring a vector database.

    Returns:
    ---------
    - args (Namespace): Parsed command-line arguments.
    """
    # Create the parser
    parser = argparse.ArgumentParser(description="Configure vector database settings.")

    # Add arguments
    parser.add_argument(
        "--distance",
        type=str,
        choices=["cosine", "l2"],
        required=True,
        help="Distance function to use for the vector database.",
    )
    parser.add_argument(
        "--summaries_split",
        action="store_true",
        help="Whether or not article summaries should be split.",
    )
    help_msg = (
        "What to use to split summaries on, if applicable. "
        "Pass 'sentences' to split by sentences. "
        "Pass multiple strings that are input to langchain.RecursiveCharacterTextSplitter."
    )
    parser.add_argument(
        "--separators",
        nargs="*",
        type=str,
        help=help_msg,
    )
    help_msg = (
        "Number of characters to split text on, if applicable. "
        "Input to langchain.RecursiveCharacterTextSplitter. "
        "Ignored if --separators == 'sentences'."
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        help=help_msg,
    )
    help_msg = (
        "Size of the character chunk overlap, if applicable. "
        "Input to langchain.RecursiveCharacterTextSplitter. "
        "Ignored if --separators == 'sentences'."
    )
    parser.add_argument(
        "--chunk_overlap",
        type=int,
        help=help_msg,
    )

    # Parse arguments
    args = parser.parse_args()

    # Implementing conditional logic based on summaries_split
    if args.summaries_split:
        if not args.separators or args.chunk_size is None or args.chunk_overlap is None:
            parser.error(
                "When --summaries_split is True, --separators, --chunk_size, and --chunk_overlap must also be specified."
            )
    else:
        if (
            args.separators
            or args.chunk_size is not None
            or args.chunk_overlap is not None
        ):
            print(
                "Warning: --separators, --chunk_size, and --chunk_overlap are ignored when --summaries_split is False."
            )

    return args


def create_database_name(args, is_sentences):
    """
    Creates a database name based on the command line flags provided.

    Parameters:
    -----------
    - args (Namespace): Parsed command-line arguments.
    - is_sentences (bool): if True, include 'sentences' in split info, otherwise
        specify the character splitting information.

    Returns:
    -----------
    - str: A string representing the database name, incorporating key configuration details.
    """
    db_name = f"db_{args.distance}"

    if args.summaries_split:
        split_info = (
            "sentences"
            if is_sentences
            else f"chunk-{args.chunk_size}_overlap-{args.chunk_overlap}"
        )
        db_name += f"_split_{split_info}"
    else:
        db_name += "_nosplit"

    return db_name


def load_records_as_df(files):
    """
    Load article records data into a dataframe.

    Parameters:
    -----------
    - files (List[str]) : full paths to article summaries jsonl files.

    Returns:
    -----------
    - records_df (pandas.DataFrame) : dataframe with record keys as columns
    """
    records = []
    for file_path in files:
        with open(file_path, "r") as f:
            for line in f:
                records.append(json.loads(line))
    records_df = pd.DataFrame.from_records(records)
    return records_df


def split_summaries_into_sentences(df):
    """
    Splits article summaries into individual sentences and duplicates the associated columns.

    Parameters:
    -----------
    - df (DataFrame): The original dataframe. Must have an 'article_summary' column.

    Returns:
    -----------
    - DataFrame: A new dataframe where each row represents a single sentence from the article summaries.
        All other data is duplicated.
    """
    # Tokenize the 'article_summary' into sentences and create a list
    df = df.copy()
    df["article_summary"] = df["article_summary"].apply(sent_tokenize)

    # Explode the 'article_summary' list into separate rows
    df_exploded = df.explode("article_summary").reset_index(drop=True)

    return df_exploded


def split_summaries_with_splitter(df, splitter):
    """
    Splits article summaries using the provided text splitter.

    Parameters:
    -----------
    - df (DataFrame): The original dataframe. Must have an 'article_summary' column.
    - splitter (langchain.text_splitter.RecursiveCharacterTextSplitter): A class for
        splitting text based on character counts, etc.

    Returns:
    -----------
    - DataFrame: A new dataframe where each row represents a single text chunk split from
        the article summaries. All other data is duplicated.
    """
    # Tokenize the 'article_summary' into sentences and create a list
    df = df.copy()
    df["article_summary"] = df["article_summary"].apply(splitter.split_text)

    # Explode the 'article_summary' list into separate rows
    df_exploded = df.explode("article_summary").reset_index(drop=True)

    return df_exploded


def add_records_to_collection(df, collection):
    """
    Add records from dataframe to the specified collection.

    Parameters:
    -----------
    - df (pandas.DataFrame): the dataframe of records to add. Must contain the
        following columns:
        - article_summary: summaries or split summaries. Will become the "documents"
        - link : the URLs for the articles
    """

    num_items = collection.count()
    ids = [str(i).zfill(12) for i in range(num_items + 1, len(df) + 1)]
    metadatas = df[METADATA_COLUMNS].to_dict(orient="records")
    documents = df.article_summary.tolist()
    collection.add(
        ids=ids,
        metadatas=metadatas,
        documents=documents,
    )


if __name__ == "__main__":

    print("Setting up the splitting parameters...")
    args = parse_command_line_flags()
    if args.summaries_split:
        is_sentences = any(i in ["sentence", "sentences"] for i in args.separators)
        args.separators = "sentences" if is_sentences else args.separators
    else:
        is_sentences = None
    args.separators = "none" if args.separators is None else args.separators
    args.chunk_size = "none" if args.chunk_size is None else args.chunk_size
    args.chunk_overlap = "none" if args.chunk_overlap is None else args.chunk_overlap

    if args.separators == "sentences":
        args.chunk_size = "none"
        args.chunk_overlap = "none"

    print("Setting up the databse...")
    db_name = create_database_name(args, is_sentences)
    print(f"Database Name: {db_name}")
    client = chromadb.PersistentClient(CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=db_name,
        metadata={  # Dictionary describing the parameters used to create the collection!
            "hnsw:space": args.distance,
            "summaries_split": args.summaries_split,
            "separators": "|".join(args.separators),
            "chunk_size": args.chunk_size,
            "chunk_overlap": args.chunk_overlap,
        },
    )

    print("Loading summaries...")
    files = collect_last_x_files(SUMMARIES_DIR)  # Includes all summary files
    records_df = load_records_as_df(files)
    records_df.publisher = records_df.publisher

    print("Removing duplicate articles within the dataframe...")
    records_df = records_df.drop_duplicates(subset="link").reset_index(drop=True)

    print("Finding any links that are already present in the database...")
    # Creates an empty set if there are none
    links_already_present = set(
        item["link"] for item in collection.get(include=["metadatas"])["metadatas"]
    )

    if len(records_df) > 0:
        if args.summaries_split:
            if args.separators == "sentences":
                print("Splitting by sentences...")
                records_df = split_summaries_into_sentences(records_df)

            else:
                print("Splitting by characters...")
                splitter = RecursiveCharacterTextSplitter(
                    separators=args.separators,
                    chunk_size=args.chunk_size,
                    chunk_overlap=args.chunk_overlap,
                )
                records_df = split_summaries_with_splitter(records_df, splitter)

        print("Adding new records...")
        add_records_to_collection(records_df, collection)
        print("Done.")

    else:
        print("No new documents to add!")

    print("--- Script complete ---")
