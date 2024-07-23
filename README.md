# reliable_news_db

This repository includes the meat of a pipeline that generates a reliable news database.
An AI browser extension, powered by retrievel-augmented LLMs, that finds low-credibility posts on Facebook and allows users to generate bridging responses rooted in reliable news.
This database is meant to be employed by an [AI browser extension](https://chromewebstore.google.com/detail/facebook-browser-extensio/edpggeojlpegninogebnekncniolbahm), powered by retrieval-augmented LLMs, that finds low-credibility posts on Facebook and allows users to generate [bridging](https://bridging.systems/) [responses](https://www.pnas.org/doi/abs/10.1073/pnas.2311627120) rooted in reliable news.

> Note:
> - Some of this code may need tweaking and/or cleaning up. The production version of the linked extension was moved to another repository.
> - This code requires paid API keys for [serp](https://serpapi.com/) (to collect Google News links) as well as [OpenAI](https://openai.com/) (to summarize article text).

### Overview of the pipeline
1. [serp](https://serpapi.com/) is used to search for recent Google News articles in the US from a specific list of domains
2. The text of these articles is programmatically scraped.
  - We use [`newspaper3k`](https://newspaper.readthedocs.io/en/latest/) to do this automatically. Note that scraping works as of July 2024 for the current list of domains. If you change this or a great deal of time has passed, the scrapping process may not work anymore. You should check your data!
3. Each article is summarized using [OpenAI](https://openai.com/)'s ChatGPT-3.5 Turbo.
4. Summary text is inserted into a vector database for fast semantic search by the browser extension. 

**The entire pipeline is run by a single [`bash`](https://www.gnu.org/software/bash/) script [`code/collect_summarize_update_vdb.sh`](https://github.com/mr-devs/reliable_news_db/blob/main/code/collect_summarize_update_vdb.sh)**

### Repository structure
- `code/`: contains all code/scripts
- `data/`: contains all data


