# FormCoach Trend Engine — Data Collectors

from .google_trends import collect_google_trends, collect_rising_queries
from .reddit import collect_reddit, collect_local_leads
from .wikipedia import collect_wikipedia_pageviews
from .quora import collect_quora
from .pubmed import collect_pubmed
from .news import collect_rss_news
from .hackernews import collect_hacker_news_leads

__all__ = [
    "collect_google_trends",
    "collect_rising_queries",
    "collect_reddit",
    "collect_local_leads",
    "collect_wikipedia_pageviews",
    "collect_quora",
    "collect_pubmed",
    "collect_rss_news",
    "collect_hacker_news_leads",
]
