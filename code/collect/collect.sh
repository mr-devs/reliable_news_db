#!/bin/bash

# Purpose:
#   Run the article collection pipeline. See individual scripts for details.
#
# Inputs:
#   None
#
# Output:
#   See individual scripts for information about their respective outputs.
#
# How to call:
#   ```
#   bash collect.sh
#   ```
#
# Author: Matthew DeVerna

### Ensure we are in the correct directory

# Set code directory based on virtual machine or local machine
if [[ -d "/home/exouser" ]]; then
  code_dir="/home/mdeverna/reliable_news_db/code/collect"
else
  code_dir="/Users/mdeverna/Documents/Projects/reliable_news_db/code/collect"
fi

cd $code_dir


echo ""
echo "########################################"
echo "--------- Collecting Serp Data ---------"
echo "########################################"
echo ""

python3 000_collect_serp_results.py

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

python3 001_collect_article_data.py

echo ""
echo "######################################"
echo "--------- Downloading complete ---------"
echo "######################################"
echo ""