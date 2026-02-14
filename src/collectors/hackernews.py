"""
Hacker News lead collector for Trend Engine V2.0.

Discovers relevant stories from Hacker News using the Algolia
search API, targeting ergonomics and pain-related tech discussions.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests


_HN_ALGOLIA_URL = "http://hn.algolia.com/api/v1/search_by_date"

_DEFAULT_QUERIES = [
    "standing desk",
    "office chair",
    "back pain",
    "RSI",
    "posture",
    "carpal tunnel",
    "ergonomics",
]

_HEADERS = {
    "User-Agent": "FormCoachTrendEngine/2.0",
    "Accept": "application/json",
}


def collect_hacker_news_leads(
    queries: list[str] | None = None,
    max_results: int = 10,
    days_back: int = 7,
) -> list[dict[str, str]] | None:
    """Collect relevant Hacker News stories about ergonomics and pain topics.

    Uses the HN Algolia API to search for stories from the last week
    matching ergonomics, pain, and workspace-related queries.

    Args:
        queries: List of search query strings. Defaults to the standard
            ergonomics/pain keyword list.
        max_results: Maximum total results to return after deduplication.
        days_back: Number of days to look back for stories.

    Returns:
        A list of lead dicts::

            [
                {
                    "source": "Hacker News",
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "type": "TECH LEADER MATCH"
                },
                ...
            ]

        Returns None if the collection fails entirely.
    """
    if queries is None:
        queries = _DEFAULT_QUERIES

    # Calculate the Unix timestamp for the cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    cutoff_ts = int(cutoff.timestamp())

    all_results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for query_idx, query in enumerate(queries):
        print(f"[Hacker News] Searching ({query_idx + 1}/{len(queries)}): '{query}'")

        try:
            response = requests.get(
                _HN_ALGOLIA_URL,
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{cutoff_ts}",
                    "hitsPerPage": 5,
                },
                headers=_HEADERS,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as exc:
            print(f"[Hacker News] Request error for '{query}': {exc}")
            continue
        except Exception as exc:
            print(f"[Hacker News] Unexpected error for '{query}': {exc}")
            continue

        hits = data.get("hits", [])
        for hit in hits:
            # Prefer the story URL; fall back to the HN discussion page
            url = hit.get("url", "")
            if not url:
                object_id = hit.get("objectID", "")
                url = f"https://news.ycombinator.com/item?id={object_id}"

            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = hit.get("title", "No title")

            # Build a snippet from available metadata
            points = hit.get("points", 0)
            num_comments = hit.get("num_comments", 0)
            author = hit.get("author", "unknown")
            snippet = f"{points} points, {num_comments} comments by {author}"

            all_results.append({
                "source": "Hacker News",
                "title": title,
                "url": url,
                "snippet": snippet,
                "type": "TECH LEADER MATCH",
            })

        # Small delay between API calls
        if query_idx < len(queries) - 1:
            time.sleep(0.5)

    if not all_results:
        print("[Hacker News] No results collected.")
        return None

    # Limit to max_results
    all_results = all_results[:max_results]

    print(f"[Hacker News] Collected {len(all_results)} leads.")
    return all_results
