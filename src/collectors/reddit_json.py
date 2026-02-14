"""
Reddit data collector using public JSON endpoints (no API keys required).

Since November 2025, Reddit ended self-service API key creation.
This module uses Reddit's public .json endpoints as a fallback,
which work without any authentication for reading public subreddit data.

Rate limit: ~10 requests/minute without auth. We add 6-second delays
between subreddit fetches to stay well within limits.
"""

from __future__ import annotations

import time
from typing import Any

import requests

_HEADERS = {
    "User-Agent": "FormCoachBot/2.0 (trend-analysis; educational)",
}

_REQUEST_DELAY = 6  # seconds between requests to respect rate limits


def _fetch_subreddit_top(
    sub_name: str,
    time_filter: str = "week",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Fetch top posts from a subreddit via the public JSON endpoint.

    URL pattern: https://www.reddit.com/r/{sub}/top.json?t={time}&limit={n}
    """
    url = f"https://www.reddit.com/r/{sub_name}/top.json"
    params = {"t": time_filter, "limit": limit, "raw_json": 1}

    try:
        resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)
        if resp.status_code == 429:
            print(f"[Reddit-JSON] Rate limited on r/{sub_name}, waiting 30s...")
            time.sleep(30)
            resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)

        if resp.status_code != 200:
            print(f"[Reddit-JSON] r/{sub_name} returned HTTP {resp.status_code}")
            return []

        data = resp.json()
        children = data.get("data", {}).get("children", [])

        posts: list[dict[str, Any]] = []
        for child in children:
            post = child.get("data", {})
            posts.append({
                "title": post.get("title", ""),
                "score": int(post.get("score", 0)),
                "comments": int(post.get("num_comments", 0)),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "subreddit": sub_name,
                "body": (post.get("selftext", "") or "")[:300],
            })

        return posts

    except requests.RequestException as exc:
        print(f"[Reddit-JSON] Error fetching r/{sub_name}: {exc}")
        return []


def _search_subreddit(
    sub_name: str,
    query: str,
    time_filter: str = "month",
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Search a subreddit via the public JSON endpoint."""
    url = f"https://www.reddit.com/r/{sub_name}/search.json"
    params = {
        "q": query,
        "restrict_sr": "on",
        "t": time_filter,
        "limit": limit,
        "sort": "relevance",
        "raw_json": 1,
    }

    try:
        resp = requests.get(url, headers=_HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            return []

        data = resp.json()
        children = data.get("data", {}).get("children", [])

        posts: list[dict[str, Any]] = []
        for child in children:
            post = child.get("data", {})
            posts.append({
                "title": post.get("title", ""),
                "score": int(post.get("score", 0)),
                "comments": int(post.get("num_comments", 0)),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "subreddit": sub_name,
                "body": (post.get("selftext", "") or "")[:300],
            })

        return posts

    except requests.RequestException:
        return []


def collect_reddit_json(
    subreddits: dict[str, list[str]],
) -> dict[str, list[dict[str, Any]]] | None:
    """Collect top weekly posts using public JSON endpoints (no API keys).

    Args:
        subreddits: A dict mapping category names to lists of subreddit names.

    Returns:
        A dict mapping each subreddit name to its top posts, or None on failure.
    """
    # Deduplicate subreddits
    seen: set[str] = set()
    unique: list[str] = []
    for sub_list in subreddits.values():
        for sub in sub_list:
            if sub not in seen:
                seen.add(sub)
                unique.append(sub)

    results: dict[str, list[dict[str, Any]]] = {}

    for i, sub_name in enumerate(unique):
        print(f"[Reddit-JSON] Fetching top posts from r/{sub_name}... ({i+1}/{len(unique)})")
        posts = _fetch_subreddit_top(sub_name)
        if posts:
            results[sub_name] = posts

        # Rate limiting delay (skip after last request)
        if i < len(unique) - 1:
            time.sleep(_REQUEST_DELAY)

    if not results:
        print("[Reddit-JSON] No results collected.")
        return None

    print(f"[Reddit-JSON] Collected posts from {len(results)} subreddits.")
    return results


def collect_local_leads_json(
    exec_subreddits: list[str],
    bay_area_subs: list[str] | None = None,
    pain_keywords: list[str] | None = None,
    lifestyle_keywords: list[str] | None = None,
) -> list[dict[str, str]] | None:
    """Search for local leads using public JSON endpoints (no API keys).

    Args:
        exec_subreddits: List of executive/lifestyle subreddit names.
        bay_area_subs: List of Bay Area subreddit names.
        pain_keywords: Pain-related search terms.
        lifestyle_keywords: Lifestyle search terms for exec subs.

    Returns:
        A list of lead dicts, or None if nothing found.
    """
    if bay_area_subs is None:
        bay_area_subs = [
            "bayarea", "sanfrancisco", "SanJose", "oakland",
        ]

    if pain_keywords is None:
        pain_keywords = [
            "back pain", "neck pain", "chronic pain",
            "physical therapy", "chiropractor",
        ]

    if lifestyle_keywords is None:
        lifestyle_keywords = [
            "standing desk", "posture", "ergonomic setup",
        ]

    leads: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Bay Area local leads
    for sub_name in bay_area_subs[:3]:  # limit to avoid rate limiting
        for keyword in pain_keywords[:3]:
            posts = _search_subreddit(sub_name, keyword, limit=2)
            for post in posts:
                if post["url"] in seen_urls:
                    continue
                seen_urls.add(post["url"])
                leads.append({
                    "source": f"r/{sub_name}",
                    "title": post["title"],
                    "url": post["url"],
                    "snippet": post.get("body", "")[:200],
                    "type": "BAY AREA LOCAL LEAD",
                })
            time.sleep(_REQUEST_DELAY)

    # Exec subreddit leads
    for sub_name in exec_subreddits[:4]:
        for keyword in (lifestyle_keywords + pain_keywords)[:3]:
            posts = _search_subreddit(sub_name, keyword, limit=2)
            for post in posts:
                if post["url"] in seen_urls:
                    continue
                seen_urls.add(post["url"])
                leads.append({
                    "source": f"r/{sub_name}",
                    "title": post["title"],
                    "url": post["url"],
                    "snippet": post.get("body", "")[:200],
                    "type": "EXEC LIFESTYLE LEAD",
                })
            time.sleep(_REQUEST_DELAY)

    if not leads:
        print("[Reddit-JSON] No leads found.")
        return None

    print(f"[Reddit-JSON] Found {len(leads)} leads.")
    return leads
