"""
Purpose:

Usage:

Input:

Output:

Author: Matthew DeVerna
"""
import os
import pandas as pd

from reliable_db.constants import MBFC_LEAN_MAP, SELECTED_DOMAINS, GNEWS_PUB_TOKEN_MAP

# Make sure we are in the proper directory for the relative output dirs/files
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != CURR_DIR:
    os.chdir(CURR_DIR)

# Full paths to data files
NG_FILE_PATH = "../data/domains/newsguard_metadata.csv"
TRANCO_FILE_PATH = "../data/domains/top-1m.csv"

OUTPUT_DIR = "../data/domains"

# Loading data
ng_df = pd.read_csv(NG_FILE_PATH)
top1m = pd.read_csv(TRANCO_FILE_PATH, names=["rank", "domain"])

# Select only US domains
ng_df_us = ng_df[ng_df.Country == "US"]

# Select top 50 quality sites
quality_and_pop = (
    top1m[top1m.domain.isin(list(ng_df_us[ng_df_us.Score >= 95]["Domain"]))]
    .head(50)
    .reset_index(drop=True)
)

# Add Tranco data
quality_sites = pd.merge(
    ng_df_us[["Domain", "Score", "Orientation"]],
    quality_and_pop,
    left_on="Domain",
    right_on="domain",
)
quality_sites = quality_sites.drop(columns=["Domain"])
quality_sites.rename(
    columns={
        "Score": "newsguard_score",
        "Orientation": "newsguard_orientation",
        "rank": "tranco_rank",
    },
    inplace=True,
)
quality_sites.sort_values(by=["tranco_rank", "newsguard_score"], inplace=True)
print(quality_sites)

# Add MBFC biases and Gnews publisher tokens
quality_sites["mbfc_bias"] = quality_sites["domain"].map(MBFC_LEAN_MAP)
quality_sites["gnews_pub_token"] = quality_sites["domain"].map(GNEWS_PUB_TOKEN_MAP)

# Save this file
output_file = os.path.join(
    OUTPUT_DIR,
    f"top_50_quality_sites.csv",
)
quality_sites.to_csv(output_file, index=False)

# Create the selected 12 domains file
quality_sites = quality_sites.drop(columns=["newsguard_orientation"])
selected_domains_df = quality_sites[
    quality_sites.domain.isin(SELECTED_DOMAINS)
].reset_index(drop=True)
output_file = os.path.join(
    OUTPUT_DIR,
    f"selected_reliable_domains.csv",
)
selected_domains_df.to_csv(output_file, index=False)
