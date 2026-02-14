"""HackerNews lead relevance filtering for Trend Engine V2.0.

Scores each HN story title against health/pain/ergonomics keywords
and drops stories that are pure tech noise. The HN Algolia API returns
any story mentioning broad terms like "RSI" or "standing desk" — most
are product launches, coding tools, or unrelated tech discussions.
"""

from __future__ import annotations
from typing import Any


# Keywords that indicate a story IS relevant to Bart's audience
_POSITIVE_KEYWORDS = {
    # Pain & conditions
    "pain", "ache", "injury", "chronic", "inflammation",
    "sciatica", "tendonitis", "tendinitis", "carpal tunnel",
    "repetitive strain", "rsi injury", "rsi symptoms", "rsi prevention",
    "back problem", "neck problem", "shoulder problem",
    "herniated", "pinched nerve",

    # Ergonomics & workspace (health angle)
    "ergonomic", "ergonomics", "posture", "standing desk",
    "sit-stand", "office chair", "lumbar support", "wrist rest",
    "monitor height", "desk setup", "workspace health",
    "typing injury", "mouse injury",

    # Treatment & wellness
    "physical therapy", "physiotherapy", "stretch", "exercise",
    "yoga", "mobility", "recovery", "rehab", "wellness",
    "health", "fitness", "meditation", "sleep",

    # Specific angles relevant to tech workers
    "burnout", "sedentary", "sitting disease", "desk worker",
    "remote work health", "wfh health", "programmer health",
    "developer health", "tech worker health",
    "eye strain", "screen time",
}

# Keywords that indicate a story is NOT relevant (tech noise)
_NEGATIVE_KEYWORDS = {
    # Dev tools / products
    "show hn", "launch hn", "hiring", "who is hiring",
    "ycombinator", "y combinator", "demo day",
    "llm", "gpt", "claude code", "copilot", "chatgpt",
    "machine learning", "deep learning", "neural network",
    "kubernetes", "docker", "terraform", "aws", "azure", "gcp",
    "blockchain", "crypto", "bitcoin", "ethereum", "nft",
    "saas", "startup", "funding", "series a", "series b",
    "ipo", "valuation", "acquisition",

    # Programming (when not health-related)
    "compiler", "parser", "database", "sql", "nosql",
    "javascript", "typescript", "python framework", "rust lang",
    "algorithm", "sorting", "turing machine",
    "open source", "github", "gitlab", "repository",
    "api", "sdk", "framework", "library",

    # Entertainment / off-topic
    "game", "gaming", "movie", "book review", "podcast",
    "political", "election", "lawsuit", "antitrust",
}

# Short terms that need word-boundary matching to avoid false positives
_BOUNDARY_TERMS = {"rsi", "wfh", "pt"}


def score_hn_relevance(title: str) -> float:
    """Score a HackerNews story title for health/ergonomics relevance.

    Returns a score from 0.0 to 1.0.
    HN has no subreddit-tier boost — all scoring is keyword-based.
    """
    title_lower = title.lower()
    words = set(title_lower.split())

    # Check negative keywords first — strong disqualifier
    for neg in _NEGATIVE_KEYWORDS:
        if neg in title_lower:
            return 0.0

    # Keyword match scoring
    strong_matches = 0
    weak_matches = 0

    for kw in _POSITIVE_KEYWORDS:
        if len(kw) <= 4:
            # Short keywords: require word boundary
            if kw in words or kw in _BOUNDARY_TERMS:
                if kw in words:
                    weak_matches += 1
        else:
            if kw in title_lower:
                strong_matches += 1

    # HN stories start from 0.0 base (no sub-tier boost)
    # Need at least one strong match to be considered relevant
    score = strong_matches * 0.25 + weak_matches * 0.1

    return min(score, 1.0)


def filter_hackernews_leads(
    hn_leads: list[dict[str, Any]] | None,
    min_relevance: float = 0.20,
) -> list[dict[str, Any]] | None:
    """Filter HackerNews leads by relevance score.

    Args:
        hn_leads: Raw HN leads list [{title, url, snippet, ...}]
        min_relevance: Minimum relevance score to keep (0.0-1.0)

    Returns:
        Filtered list with only relevant leads, or None if empty.
    """
    if not hn_leads:
        return None

    total_before = len(hn_leads)
    filtered = []

    for lead in hn_leads:
        title = lead.get("title", "")
        score = score_hn_relevance(title)
        if score >= min_relevance:
            lead["relevance_score"] = round(score, 2)
            filtered.append(lead)

    # Sort by relevance descending
    filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    if filtered:
        print(f"[HN Filter] Kept {len(filtered)}/{total_before} leads "
              f"({len(filtered)/max(total_before,1)*100:.0f}% relevant)")
    else:
        print(f"[HN Filter] No relevant leads found (dropped all {total_before})")

    return filtered if filtered else None
