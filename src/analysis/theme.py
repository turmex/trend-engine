"""
FormCoach Trend Engine V2.0 — Theme Selection & Analysis Builder
=================================================================
Determines the week's primary theme from collected data and assembles
the full analysis dict consumed by rendering and strategy layers.

V2.0 upgrades theme selection to use composite-scored body-part groups
(volume + momentum + stability) instead of pure wow_pct sorting, which
prevented low-volume spikes from outranking high-volume steady topics.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from analysis.body_part_groups import (
    compute_composite_score,
    group_keywords_by_body_part,
    select_theme_from_groups,
)


def _google_movers(google: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort Google Trends keywords by wow_pct descending.

    Skips entries where wow_pct is None.

    Returns:
        A list of dicts with ``keyword``, ``current``, ``wow_pct``, and
        ``composite`` keys, sorted from largest positive WoW change to
        smallest. The ``composite`` field uses volume-weighted scoring
        from :func:`analysis.body_part_groups.compute_composite_score`.
    """
    movers: list[dict[str, Any]] = []
    for keyword, data in google.items():
        wow = data.get("wow_pct")
        if wow is not None:
            current = data.get("current", 0)
            four_w_avg = data.get("4w_avg", 0)
            movers.append({
                "keyword": keyword,
                "current": current,
                "wow_pct": float(wow),
                "prev_week": data.get("prev_week", 0),
                "4w_trend": data.get("4w_trend", "stable"),
                "4w_avg": four_w_avg,
                "composite": compute_composite_score(current, wow, four_w_avg),
            })
    movers.sort(key=lambda m: m["wow_pct"], reverse=True)
    return movers


def _wiki_movers(wikipedia: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort Wikipedia articles by wow_pct descending.

    Returns:
        A list of dicts with ``article`` and ``wow_pct`` keys,
        sorted from largest positive WoW change to smallest.
    """
    movers: list[dict[str, Any]] = []
    for article, data in wikipedia.items():
        wow = data.get("wow_pct")
        if wow is not None:
            movers.append({
                "article": article,
                "wow_pct": float(wow),
                "current_avg": data.get("current_week_avg", data.get("current_avg", 0)),
                "prior_avg": data.get("prior_week_avg", data.get("prior_avg", 0)),
            })
    movers.sort(key=lambda m: m["wow_pct"], reverse=True)
    return movers


_PAIN_KEYWORDS: set[str] = {
    "pain", "back", "neck", "hip", "knee", "shoulder",
    "posture", "sciatica", "headache", "ankle", "wrist",
    "spine", "disc", "herniated", "plantar", "fasciitis",
    "tendonitis", "fibromyalgia", "arthritis", "scoliosis",
}


def _best_reddit_keyword(reddit: dict[str, list[dict[str, Any]]]) -> str | None:
    """Find a real pain/fitness keyword from the most-upvoted Reddit post.

    First attempts to extract an actual keyword from the highest-scored
    post's title by checking for overlap with common pain/fitness terms.
    Falls back to the subreddit name if no recognizable keyword is found.

    Returns:
        A pain/fitness keyword extracted from the top post title, the
        subreddit name as fallback, or ``None`` if no posts are available.
    """
    best_score = -1
    best_subreddit: str | None = None
    best_title: str = ""

    for subreddit, posts in reddit.items():
        if not isinstance(posts, list):
            continue
        for post in posts:
            if not isinstance(post, dict):
                continue
            score = int(post.get("score", 0))
            if score > best_score:
                best_score = score
                best_subreddit = subreddit
                best_title = str(post.get("title", ""))

    if best_subreddit is None:
        return None

    # Try to extract a real keyword from the top post's title
    if best_title:
        title_lower = best_title.lower()
        title_words = set(title_lower.split())
        matched = title_words & _PAIN_KEYWORDS
        if matched:
            # Return the longest matching word for specificity
            # (e.g. "sciatica" over "back")
            return max(matched, key=len)

    return best_subreddit


def select_theme(
    google: dict[str, dict[str, Any]] | None,
    wikipedia: dict[str, dict[str, Any]] | None,
    reddit: dict[str, list[dict[str, Any]]] | None,
    prior_theme: str | None,
) -> str:
    """Determine this week's primary theme for the trend brief.

    Selection cascade:
        1. **Body-part group composite score** (PRIMARY) — groups keywords
           by anatomical region and selects by volume-weighted composite
           score, preventing low-volume spikes from dominating.
        2. Highest WoW mover from Wikipedia (wow_pct > 15%).
        3. Most-upvoted Reddit topic keyword (extracted from post title).
        4. ``"General Pain Management"`` as the final fallback.

    If the selected theme matches ``prior_theme``, the second-highest
    option is tried for variety (but only if it also meets the threshold).

    Args:
        google: Google Trends data dict, or ``None``.
        wikipedia: Wikipedia pageview data dict, or ``None``.
        reddit: Reddit data dict mapping subreddits to post lists, or ``None``.
        prior_theme: The theme string from the prior week, or ``None``.

    Returns:
        A theme string suitable for use as the brief's headline topic.
    """
    # ── PRIMARY: Body-part group composite scoring ──────────────────
    if google:
        groups = group_keywords_by_body_part(google)
        if groups:
            theme = select_theme_from_groups(groups, prior_theme)
            if theme != "General Pain Management":
                return theme

    # ── Fallback: Wikipedia WoW movers ─────────────────────────────
    if wikipedia:
        movers = _wiki_movers(wikipedia)
        significant = [m for m in movers if m["wow_pct"] > 15]

        if significant:
            # Convert article slug to readable form
            candidate = significant[0]["article"].replace("_", " ")
            if candidate == prior_theme and len(significant) > 1:
                return significant[1]["article"].replace("_", " ")
            return candidate

    # ── Fallback: Reddit keyword extraction ────────────────────────
    if reddit:
        keyword = _best_reddit_keyword(reddit)
        if keyword:
            return keyword

    # ── Final fallback ──────────────────────────────────────────────
    return "General Pain Management"


def _extract_top_mover(
    google: dict[str, dict[str, Any]] | None,
    wikipedia: dict[str, dict[str, Any]] | None,
) -> dict[str, Any] | None:
    """Extract the single top-mover record for the analysis dict.

    Prefers Google Trends data. Falls back to Wikipedia.

    Returns:
        A dict with mover details, or ``None`` if no data is available.
    """
    if google:
        movers = _google_movers(google)
        if movers:
            return movers[0]

    if wikipedia:
        movers = _wiki_movers(wikipedia)
        if movers:
            top = movers[0]
            return {
                "keyword": top["article"].replace("_", " "),
                "current": top.get("current_avg", 0),
                "wow_pct": top["wow_pct"],
            }

    return None


def build_analysis(
    google: dict[str, dict[str, Any]] | None,
    rising_queries: dict[str, dict[str, list[dict[str, Any]]]] | None,
    reddit: dict[str, list[dict[str, Any]]] | None,
    quora: list[dict[str, Any]] | None,
    wikipedia: dict[str, dict[str, Any]] | None,
    pubmed: list[dict[str, Any]] | None,
    news: list[dict[str, Any]] | None,
    leads: list[dict[str, Any]] | None,
    hn_leads: list[dict[str, Any]] | None,
    *,
    prior_theme: str | None = None,
) -> dict[str, Any]:
    """Assemble all collected data into a single analysis dict.

    This is the canonical structure consumed by rendering and strategy
    layers.  The ``theme`` is auto-selected via :func:`select_theme` and
    the ``top_mover`` is the keyword with the highest wow_pct.

    Args:
        google: Google Trends data.
        rising_queries: Rising/top related queries per keyword.
        reddit: Reddit posts grouped by subreddit.
        quora: List of Quora question dicts.
        wikipedia: Wikipedia pageview data per article.
        pubmed: List of PubMed article dicts.
        news: List of news article dicts.
        leads: List of lead/opportunity dicts.
        hn_leads: List of Hacker News lead dicts.
        prior_theme: The prior week's theme (used for variety logic).

    Returns:
        A dict with all data unified under a single structure, including
        auto-selected ``theme`` and ``top_mover`` fields.
    """
    groups = group_keywords_by_body_part(google)
    theme = select_theme(google, wikipedia, reddit, prior_theme)
    top_mover = _extract_top_mover(google, wikipedia)

    return {
        "date": date.today().isoformat(),
        "theme": theme,
        "top_mover": top_mover,
        "body_part_groups": groups,
        "google": google,
        "rising_queries": rising_queries,
        "reddit": reddit,
        "quora": quora,
        "wikipedia": wikipedia,
        "pubmed": pubmed,
        "news": news,
        "leads": leads,
        "hn_leads": hn_leads,
    }
