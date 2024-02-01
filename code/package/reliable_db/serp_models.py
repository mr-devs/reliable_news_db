"""
Data models for processing responses from models.
"""
from datetime import datetime
from reliable_db.utils import get_dict_val


class SerpGnewsArticle:
    """
    Class for article objects from the Serp API, specific to Google News Search.
    - Ref: https://serpapi.com/google-news-api
    """

    def __init__(self, article_obj):
        """
        Initialize the class.
        """
        if not isinstance(article_obj, dict):
            raise ValueError(
                "Invalid input object. Expected a dictionary representing a Google News "
                "Serp API article response."
            )
        self.article_obj = article_obj

    @property
    def serp_date(self):
        """
        Return the of the article.
        """
        return get_dict_val(self.article_obj, ["date"])

    @property
    def title(self):
        """
        Return the title of the article.
        """
        return get_dict_val(self.article_obj, ["title"])

    @property
    def authors(self, delimiter=","):
        """
        Return the author(s) of the article.
        If more than one author is present, they are delimited by `delimiter`.
        Default delimiter: ,
        """
        authors_list = get_dict_val(self.article_obj, ["source", "authors"])
        if not authors_list:
            return None
        if len(authors_list) > 1:
            return delimiter.join(authors_list)
        return authors_list[0]

    @property
    def publisher(self):
        """
        Return the publisher of the article (e.g., 'The New York Times').
        """
        return get_dict_val(self.article_obj, ["source", "name"])

    @property
    def link(self):
        """
        Return the article link.
        """
        return get_dict_val(self.article_obj, ["link"])

    def __repr__(self) -> str:
        return f"Pub: {self.publisher}\nURL: {self.link}"

    def __str__(self) -> str:
        return f"Pub: {self.publisher}\nURL: {self.link}"
