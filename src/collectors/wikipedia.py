"""
Wikipedia pageview data collector for Trend Engine V2.0.

Collects daily pageview statistics from the Wikimedia REST API
for specified Wikipedia articles.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

import requests


_BASE_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
    "/en.wikipedia/all-access/all-agents"
)

_HEADERS = {
    "User-Agent": "FormCoachTrendEngine/1.5 (contact@formcoach.com)",
    "Accept": "application/json",
}


def collect_wikipedia_pageviews(
    articles: list[str],
    days: int = 14,
) -> dict[str, dict[str, Any]] | None:
    """Collect daily Wikipedia pageview data for a list of articles.

    Fetches the last ``days`` days of pageview data, splits into current
    week (last 7 days) and prior week (days 8-14), and computes averages
    and week-over-week change.

    Args:
        articles: List of Wikipedia article titles (use underscores for spaces,
            e.g. "Low_back_pain").
        days: Number of days of history to fetch. Defaults to 14.

    Returns:
        A dict mapping each article to its pageview metrics::

            {
                "Low_back_pain": {
                    "current_week_avg": float,
                    "prior_week_avg": float,
                    "wow_pct": float | None,
                    "daily": [{"date": str, "views": int}, ...]
                }
            }

        Returns None if the collection fails entirely.
    """
    if not articles:
        print("[Wikipedia] No articles provided.")
        return None

    end_date = datetime.utcnow() - timedelta(days=1)  # Yesterday (data lag)
    start_date = end_date - timedelta(days=days - 1)

    # Wikimedia date format: YYYYMMDD00 (trailing 00 required)
    start_str = start_date.strftime("%Y%m%d") + "00"
    end_str = end_date.strftime("%Y%m%d") + "00"

    results: dict[str, dict[str, Any]] = {}

    for article in articles:
        # Replace spaces with underscores for the API
        article_slug = article.replace(" ", "_")
        url = f"{_BASE_URL}/{article_slug}/daily/{start_str}/{end_str}"

        print(f"[Wikipedia] Fetching pageviews for '{article_slug}'...")
        try:
            response = requests.get(url, headers=_HEADERS, timeout=15)

            if response.status_code == 404:
                print(f"[Wikipedia] Article not found: '{article_slug}', skipping.")
                time.sleep(0.1)
                continue

            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                print(f"[Wikipedia] No pageview data for '{article_slug}'.")
                time.sleep(0.1)
                continue

            # Build daily list sorted by date
            daily: list[dict[str, Any]] = []
            for item in items:
                timestamp = item.get("timestamp", "")
                # Timestamp format is YYYYMMDD00; extract YYYY-MM-DD
                if len(timestamp) >= 8:
                    date_str = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
                else:
                    date_str = timestamp
                daily.append({
                    "date": date_str,
                    "views": item.get("views", 0),
                })

            # Sort by date ascending
            daily.sort(key=lambda d: d["date"])

            # Split into current week (last 7 entries) and prior week
            if len(daily) >= 14:
                prior_week = daily[:7]
                current_week = daily[7:]
            elif len(daily) >= 7:
                current_week = daily[-7:]
                prior_week = daily[: len(daily) - 7] if len(daily) > 7 else daily[:len(daily) // 2]
            else:
                current_week = daily
                prior_week = []

            current_views = [d["views"] for d in current_week]
            prior_views = [d["views"] for d in prior_week]

            current_week_avg = (
                round(sum(current_views) / len(current_views), 2)
                if current_views
                else 0.0
            )
            prior_week_avg = (
                round(sum(prior_views) / len(prior_views), 2)
                if prior_views
                else 0.0
            )

            # Week-over-week percentage change
            if prior_week_avg > 0:
                wow_pct = round(
                    ((current_week_avg - prior_week_avg) / prior_week_avg) * 100, 2
                )
            else:
                wow_pct = None

            results[article] = {
                "current_week_avg": current_week_avg,
                "prior_week_avg": prior_week_avg,
                "wow_pct": wow_pct,
                "daily": daily,
            }

        except requests.exceptions.HTTPError as exc:
            print(f"[Wikipedia] HTTP error for '{article_slug}': {exc}")
        except requests.exceptions.RequestException as exc:
            print(f"[Wikipedia] Request error for '{article_slug}': {exc}")
        except Exception as exc:
            print(f"[Wikipedia] Unexpected error for '{article_slug}': {exc}")

        time.sleep(0.1)

    if not results:
        print("[Wikipedia] No results collected.")
        return None

    print(f"[Wikipedia] Collected pageviews for {len(results)} articles.")
    return results
