"""
Cumbersome constant objects for scripts are saved here to clean up other scripts.
"""

# Based on mediabiasfactcheck "bias" measurement as of 12/12/2023 of top 50 selected below
MBFC_LEAN_MAP = {
    "yahoo.com": "least-biased",
    "msn.com": "left-center",
    "nytimes.com": "left-center",
    "theguardian.com": "left-center",
    "forbes.com": "right-center",
    "bbc.com": "left-center",
    "washingtonpost.com": "left-center",
    "cdc.gov": "pro-science",
    "reuters.com": "least-biased",
    "bloomberg.com": "left-center",
    "wsj.com": "right-center",
    "businessinsider.com": "left-center",
    "nasa.gov": "pro-science",
    "npr.org": "left-center",
    "usatoday.com": "left-center",
    "time.com": "left-center",
    "cnet.com": "least-biased",
    "ft.com": "least-biased",
    "cbsnews.com": "left-center",
    "latimes.com": "left-center",
    "theverge.com": "left-center",
    "nbcnews.com": "left-center",
    "theatlantic.com": "left-center",
    "hbr.org": "least-biased",
    "nationalgeographic.com": "pro-science",
    "investopedia.com": "least-biased",
    "yahoo.net": "n/a",  # reroutes to yahoo.com
    # Note: I would not include pbs.org (below)
    # Note also that this is the rating for PBS NewsHour (the nightly TV show)
    # pbs.org does not have its own MBFC site and if you do a news.google search, you get mostly
    # PBS NewsHour results. However, they are links to videos, not articles. You also get
    # Antiques roadshow results, which aren't what we want.
    "pbs.org": "left-center",
    "economist.com": "least-biased",
    "usnews.com": "left-center",
    "theconversation.com": "least-biased",
    "cbc.ca": "left-center",
    "marketwatch.com": "right-center",
    "newyorker.com": "left",
    "fortune.com": "right-center",
    "apnews.com": "left-center",
    "newsweek.com": "right-center",
    "fastcompany.com": "left-center",
    "zdnet.com": "least-biased",
    "pewresearch.org": "least-biased",
    "scientificamerican.com": "pro-science",
    "inc.com": "least-biased",
    "engadget.com": "left-center",
    "politico.com": "left-center",
    "arstechnica.com": "least-biased",
    "sfgate.com": "left-center",
    "pcmag.com": "n/a",  # couldn't find
    "variety.com": "left-center",
    "fool.com": "left-center",  # motley fool
    "livescience.com": "pro-science",
    "qz.com": "left-center",  # quarz
    "chicagotribune.com": "right-center",
    "insider.com": "left-center",
    "nejm.org": "pro-science",
    "smithsonianmag.com": "pro-science",
    "theglobeandmail.com": "right-center",
    "technologyreview.com": "pro-science",
    "chron.com": "left-center",  # houston chronicle
}

# Manually selected domains
SELECTED_DOMAINS = [
    # center (MBFC "least-biased")
    "reuters.com",
    "ft.com",
    "hbr.org",
    "economist.com",
    "theconversation.com",
    # left (MBFC "center-left")
    "nytimes.com",
    "theguardian.com",
    "washingtonpost.com",
    # right (MBFC "right-left")
    "forbes.com",
    "wsj.com",
    "newsweek.com",
]

GNEWS_PUB_TOKEN_MAP = {
    # center (least-biased)
    "reuters.com": "CAAqBggKMLegDDCwJg",
    "ft.com": "CAAqBwgKMPuH1gcw-M9I",
    "hbr.org": "CAAqIAgKIhpDQklTRFFnTWFna0tCMmhpY2k1dmNtY29BQVAB",
    "economist.com": "CAAqKAgKIiJDQklTRXdnTWFnOEtEV1ZqYjI1dmJXbHpkQzVqYjIwb0FBUAE",
    "theconversation.com": "CAAqMAgKIipDQklTR1FnTWFoVUtFM1JvWldOdmJuWmxjbk5oZEdsdmJpNWpiMjBvQUFQAQ",
    # left-center
    "nytimes.com": "CAAqBwgKMI7rigMwlq88",
    "theguardian.com": "CAAqBggKMJeqezDfswk",
    "washingtonpost.com": "CAAqBwgKMI7UlAowt9F0",
    # right-center
    "forbes.com": "CAAqBggKMK6pATCgRQ",
    "wsj.com": "CAAqBwgKMNbcyQEw58sV",
    "newsweek.com": "CAAqBwgKMO-82wow4qvMAQ",
}
