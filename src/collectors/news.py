"""
RSS news collector for Trend Engine V2.0.

Collects recent health and pain-related news articles from
Google News via RSS feed.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import feedparser


# Google News RSS base URL
_GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Default boolean queries targeting pain/exercise/longevity news from the last 7 days
_DEFAULT_QUERY = (
    '("back pain" OR "neck pain" OR "sciatica" OR "cancer pain" OR "chronic pain") '
    'AND ("treatment" OR "exercise" OR "study" OR "ergonomics" OR "posture" '
    'OR "prevention") when:7d'
)

_SUPPLEMENTAL_QUERIES = [
    '("yoga therapy" OR "yoga for pain" OR "therapeutic yoga") AND ("study" OR "benefit" OR "research") when:7d',
    '("longevity" OR "functional fitness" OR "mobility") AND ("exercise" OR "aging" OR "research") when:7d',
    '("cancer exercise" OR "exercise oncology" OR "exercise during chemotherapy") when:7d',
    '("running injury" OR "marathon recovery" OR "runner knee") AND ("treatment" OR "prevention") when:7d',
]


def collect_rss_news(
    query: str = _DEFAULT_QUERY,
    max_results: int = 10,
    include_supplemental: bool = True,
) -> list[dict[str, Any]] | None:
    """Collect recent news articles from Google News RSS.

    Parses the Google News RSS feed for articles matching a boolean
    query about pain conditions and treatments.

    Args:
        query: The Google News search query. Defaults to the pain/exercise
            query with a 7-day recency filter.
        max_results: Maximum number of articles to return.

    Returns:
        A list of article dicts::

            [
                {
                    "title": str,
                    "source": str,
                    "url": str,
                    "date": str
                },
                ...
            ]

        Returns None if the collection fails or no articles are found.
    """
    encoded_query = quote(query)
    feed_url = f"{_GOOGLE_NEWS_RSS}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    print(f"[News] Fetching Google News RSS feed...")

    try:
        feed = feedparser.parse(feed_url)
    except Exception as exc:
        print(f"[News] Failed to parse RSS feed: {exc}")
        return None

    # Check for feed errors
    if feed.bozo and not feed.entries:
        print(f"[News] Feed error: {feed.bozo_exception}")
        return None

    if not feed.entries:
        print("[News] No entries found in RSS feed.")
        return None

    articles: list[dict[str, Any]] = []

    for entry in feed.entries[:max_results]:
        try:
            title = entry.get("title", "No title")

            # Google News titles often include " - Source Name" at the end
            source = "Unknown"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    source = parts[1].strip()

            # Also check the source field directly
            if source == "Unknown":
                source_info = entry.get("source", {})
                if hasattr(source_info, "get"):
                    source = source_info.get("title", source)
                elif isinstance(source_info, str):
                    source = source_info

            url = entry.get("link", "")
            date = entry.get("published", entry.get("updated", "Unknown"))

            articles.append({
                "title": title,
                "source": source,
                "url": url,
                "date": date,
            })

        except Exception as exc:
            print(f"[News] Error parsing entry: {exc}")
            continue

    # Supplemental queries for broader Bart-relevant coverage
    if include_supplemental and len(articles) < max_results:
        seen_titles = {a["title"].lower() for a in articles}
        for sup_query in _SUPPLEMENTAL_QUERIES:
            if len(articles) >= max_results:
                break
            sup_encoded = quote(sup_query)
            sup_url = f"{_GOOGLE_NEWS_RSS}?q={sup_encoded}&hl=en-US&gl=US&ceid=US:en"
            try:
                sup_feed = feedparser.parse(sup_url)
                for entry in (sup_feed.entries or [])[:3]:
                    if len(articles) >= max_results:
                        break
                    title = entry.get("title", "No title")
                    source = "Unknown"
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        if len(parts) == 2:
                            title = parts[0].strip()
                            source = parts[1].strip()
                    if title.lower() in seen_titles:
                        continue
                    seen_titles.add(title.lower())
                    articles.append({
                        "title": title,
                        "source": source,
                        "url": entry.get("link", ""),
                        "date": entry.get("published", "Unknown"),
                    })
            except Exception:
                continue

    if not articles:
        print("[News] Failed to parse any articles from feed.")
        return None

    print(f"[News] Collected {len(articles)} news articles.")
    return articles
