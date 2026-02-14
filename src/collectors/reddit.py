"""
Reddit data collector for Trend Engine V2.0.

Collects top posts from configured subreddits and searches for
local leads from Bay Area and executive subreddits.
"""

from __future__ import annotations

from typing import Any

import praw


def collect_reddit(
    subreddits: dict[str, list[str]],
    client_id: str,
    client_secret: str,
    user_agent: str,
) -> dict[str, dict[str, list[dict[str, Any]]]] | None:
    """Collect top weekly posts from configured subreddits.

    Args:
        subreddits: A dict mapping category names to lists of subreddit names.
            Example: {"pain": ["ChronicPain", "BackPain"], "fitness": ["Fitness"]}
        client_id: Reddit API client ID.
        client_secret: Reddit API client secret.
        user_agent: Reddit API user agent string.

    Returns:
        A dict mapping each subreddit name to its top posts::

            {
                "ChronicPain": {
                    "posts": [
                        {
                            "title": str,
                            "score": int,
                            "comments": int,
                            "url": str,
                            "subreddit": str
                        },
                        ...
                    ]
                }
            }

        Returns None if the collection fails entirely.
    """
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
    except Exception as exc:
        print(f"[Reddit] Failed to initialize Reddit client: {exc}")
        return None

    results: dict[str, dict[str, list[dict[str, Any]]]] = {}

    # Flatten all subreddit names from the category dict
    all_subreddits: list[str] = []
    for sub_list in subreddits.values():
        all_subreddits.extend(sub_list)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_subreddits: list[str] = []
    for sub in all_subreddits:
        if sub not in seen:
            seen.add(sub)
            unique_subreddits.append(sub)

    for sub_name in unique_subreddits:
        print(f"[Reddit] Fetching top posts from r/{sub_name}...")
        try:
            subreddit = reddit.subreddit(sub_name)
            posts: list[dict[str, Any]] = []

            for submission in subreddit.top(time_filter="week", limit=10):
                posts.append({
                    "title": submission.title,
                    "score": submission.score,
                    "comments": submission.num_comments,
                    "url": f"https://reddit.com{submission.permalink}",
                    "subreddit": sub_name,
                })

            results[sub_name] = posts

        except Exception as exc:
            print(f"[Reddit] Error fetching r/{sub_name}: {exc}")
            continue

    if not results:
        print("[Reddit] No results collected.")
        return None

    print(f"[Reddit] Collected posts from {len(results)} subreddits.")
    return results


def collect_local_leads(
    exec_subreddits: list[str],
    client_id: str,
    client_secret: str,
    user_agent: str,
    bay_area_subs: list[str] | None = None,
    pain_keywords: list[str] | None = None,
    lifestyle_keywords: list[str] | None = None,
) -> list[dict[str, str]] | None:
    """Search Bay Area and executive subreddits for local lead opportunities.

    Searches Bay Area location subreddits for pain-related keywords and
    executive subreddits for combined lifestyle + pain keywords.

    Args:
        exec_subreddits: List of executive/lifestyle subreddit names.
        client_id: Reddit API client ID.
        client_secret: Reddit API client secret.
        user_agent: Reddit API user agent string.
        bay_area_subs: List of Bay Area subreddit names. Defaults to common ones.
        pain_keywords: List of pain-related search terms.
        lifestyle_keywords: List of lifestyle search terms for exec subs.

    Returns:
        A list of lead dicts::

            [
                {
                    "source": str,
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "type": str
                },
                ...
            ]

        Returns None if the collection fails entirely.
    """
    if bay_area_subs is None:
        bay_area_subs = [
            "bayarea", "sanfrancisco", "SanJose", "oakland",
            "berkeley", "PaloAlto", "MountainView",
        ]

    if pain_keywords is None:
        pain_keywords = [
            "back pain", "neck pain", "sciatica", "chronic pain",
            "physical therapy", "chiropractor", "ergonomic",
        ]

    if lifestyle_keywords is None:
        lifestyle_keywords = [
            "standing desk", "office chair", "work from home pain",
            "sitting all day", "posture", "ergonomic setup",
        ]

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
    except Exception as exc:
        print(f"[Local Leads] Failed to initialize Reddit client: {exc}")
        return None

    leads: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Search Bay Area subreddits for pain keywords
    for sub_name in bay_area_subs:
        for keyword in pain_keywords:
            try:
                subreddit = reddit.subreddit(sub_name)
                for submission in subreddit.search(keyword, limit=3, time_filter="month"):
                    url = f"https://reddit.com{submission.permalink}"
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    snippet = (submission.selftext[:200] + "...") if submission.selftext else ""
                    leads.append({
                        "source": f"r/{sub_name}",
                        "title": submission.title,
                        "url": url,
                        "snippet": snippet,
                        "type": "BAY AREA LOCAL LEAD",
                    })
            except Exception as exc:
                print(f"[Local Leads] Error searching r/{sub_name} for '{keyword}': {exc}")
                continue

    # Search executive subreddits for lifestyle + pain keywords
    combined_keywords = lifestyle_keywords + pain_keywords
    for sub_name in exec_subreddits:
        for keyword in combined_keywords:
            try:
                subreddit = reddit.subreddit(sub_name)
                for submission in subreddit.search(keyword, limit=3, time_filter="month"):
                    url = f"https://reddit.com{submission.permalink}"
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    snippet = (submission.selftext[:200] + "...") if submission.selftext else ""
                    leads.append({
                        "source": f"r/{sub_name}",
                        "title": submission.title,
                        "url": url,
                        "snippet": snippet,
                        "type": "EXEC LIFESTYLE LEAD",
                    })
            except Exception as exc:
                print(f"[Local Leads] Error searching r/{sub_name} for '{keyword}': {exc}")
                continue

    if not leads:
        print("[Local Leads] No leads found.")
        return None

    print(f"[Local Leads] Found {len(leads)} leads.")
    return leads
