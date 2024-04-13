#!/bin/bash

# Purpose:
#   Run the pipeline to collect and summarize article data, then update the vector database.
#   See individual scripts for details.
#
# Inputs:
#   None
#
# Output:
#   See individual scripts for information about their respective outputs.
#
# How to call:
#   ```
#   bash collect_summarize_update_vdb.sh
#   ```
#
# Author: Matthew DeVerna

### Ensure we are in the correct directory
code_dir="/home/data/apps/llm_facebook_browser_extension/reliable_news_db/code"
cd $code_dir

### Use conda python to ensure we have all packages, etc.
my_py=/home/data/apps/llm_facebook_browser_extension/myvenv/bin/python


echo ""
echo "########################################"
echo "--------- Collecting Serp Data ---------"
echo "########################################"
echo ""

$my_py ./collect/000_collect_serp_results.py

echo ""
echo "######################################"
echo "--------- Collection complete ---------"
echo "######################################"
echo ""

echo ""
echo "#############################################"
echo "--------- Downloading Article Text ---------"
echo "#############################################"
echo ""

$my_py ./collect/001_collect_article_data.py

echo ""
echo "######################################"
echo "--------- Downloading complete ---------"
echo "######################################"
echo ""


echo ""
echo "###################################################################"
echo "--------- Summarizing Article Text with Chat GPT3.5-Turbo ---------"
echo "###################################################################"
echo ""

$my_py ./collect/002_summarize_article_data.py

echo ""
echo "######################################"
echo "--------- Summarization complete ---------"
echo "######################################"
echo ""


echo ""
echo "################################################"
echo "--------- Updating the vector database ---------"
echo "################################################"
echo ""

$my_py ./create_dbs/update_vdb.py --distance cosine

echo ""
echo "#############################################"
echo "--------- Vector DB update complete ---------"
echo "#############################################"
echo ""