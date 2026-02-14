"""
Quora question collector for Trend Engine V2.0.

Discovers relevant Quora questions by scraping Google search results.
Falls back gracefully if Google blocks the requests.
"""

from __future__ import annotations

import random
import re
import time
from typing import Any
from urllib.parse import unquote

import requests


_GOOGLE_SEARCH_URL = "https://www.google.com/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _make_fingerprint(question: str) -> str:
    """Create a lowercase URL-style slug from a question string.

    Args:
        question: The raw question text.

    Returns:
        A lowercase hyphenated slug suitable for deduplication.
        Example: "Best exercises for chronic back pain" becomes
        "best-exercises-for-chronic-back-pain".
    """
    # Remove non-alphanumeric characters except spaces and hyphens
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", question)
    # Replace whitespace with hyphens and lowercase
    slug = re.sub(r"\s+", "-", cleaned.strip()).lower()
    # Collapse multiple hyphens
    slug = re.sub(r"-+", "-", slug)
    return slug


def _extract_quora_urls(html: str) -> list[dict[str, str]]:
    """Extract Quora question URLs and titles from Google search HTML.

    Args:
        html: Raw HTML from a Google search results page.

    Returns:
        A list of dicts with "url" and "question" keys.
    """
    results: list[dict[str, str]] = []

    # Pattern to find Quora URLs in Google results
    # Google wraps URLs in /url?q= redirects or directly in href attributes
    url_pattern = re.compile(
        r'href="(?:/url\?q=)?(https?://(?:www\.)?quora\.com/[^"&]+)',
        re.IGNORECASE,
    )

    for match in url_pattern.finditer(html):
        raw_url = unquote(match.group(1))

        # Skip non-question pages (profiles, topics, spaces, etc.)
        if any(skip in raw_url for skip in ["/profile/", "/topic/", "/space/", "/answer/"]):
            continue

        # Extract question from URL path
        path = raw_url.rstrip("/").split("/")[-1]
        question = path.replace("-", " ")

        # Clean up query parameters
        if "?" in raw_url:
            raw_url = raw_url.split("?")[0]

        results.append({
            "url": raw_url,
            "question": question,
        })

    return results


def collect_quora(
    queries: list[str],
    max_per_query: int = 3,
) -> list[dict[str, Any]] | None:
    """Collect Quora questions relevant to the given search queries.

    Uses Google search with ``site:quora.com`` to find relevant questions.
    Deduplicates results by URL.

    Args:
        queries: A list of search query strings.
        max_per_query: Maximum number of results to keep per query.

    Returns:
        A list of question dicts::

            [
                {
                    "question": str,
                    "url": str,
                    "source_query": str,
                    "fingerprint": str
                },
                ...
            ]

        Returns None if collection fails entirely (e.g., Google blocks requests).
    """
    if not queries:
        print("[Quora] No queries provided.")
        return None

    all_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    blocked = False

    session = requests.Session()
    session.headers.update(_HEADERS)

    for query_idx, query in enumerate(queries):
        search_query = f'site:quora.com "{query}"'
        print(f"[Quora] Searching ({query_idx + 1}/{len(queries)}): {search_query}")

        try:
            response = session.get(
                _GOOGLE_SEARCH_URL,
                params={"q": search_query, "num": max_per_query + 2},
                timeout=15,
            )

            # Check for Google blocking
            if response.status_code == 429 or response.status_code == 503:
                print("[Quora] WARNING: Google is rate-limiting requests. Stopping.")
                blocked = True
                break

            if response.status_code != 200:
                print(f"[Quora] Got status {response.status_code} for query: {query}")
                continue

            # Check for CAPTCHA page
            if "unusual traffic" in response.text.lower() or "captcha" in response.text.lower():
                print("[Quora] WARNING: Google CAPTCHA detected. Stopping.")
                blocked = True
                break

            extracted = _extract_quora_urls(response.text)
            count = 0

            for item in extracted:
                if count >= max_per_query:
                    break
                if item["url"] in seen_urls:
                    continue

                seen_urls.add(item["url"])
                all_results.append({
                    "question": item["question"],
                    "url": item["url"],
                    "source_query": query,
                    "fingerprint": _make_fingerprint(item["question"]),
                })
                count += 1

        except requests.exceptions.RequestException as exc:
            print(f"[Quora] Request error for query '{query}': {exc}")
            continue
        except Exception as exc:
            print(f"[Quora] Unexpected error for query '{query}': {exc}")
            continue

        # Sleep 3-5 seconds between searches to be polite
        if query_idx < len(queries) - 1:
            sleep_time = random.uniform(3.0, 5.0)
            time.sleep(sleep_time)

    if blocked and not all_results:
        print("[Quora] WARNING: Google blocked all requests. Returning None.")
        return None

    if not all_results:
        print("[Quora] No results collected.")
        return None

    print(f"[Quora] Collected {len(all_results)} unique questions.")
    return all_results
