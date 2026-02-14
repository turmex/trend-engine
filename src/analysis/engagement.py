"""
Trend Engine V2.0 — Engagement Opportunity Ranking
=============================================================
Scores and ranks Reddit posts and Quora questions by how promising
they are for a helpful reply from Bart (the FormCoach persona).
"""

from __future__ import annotations

import math
from typing import Any

# ─── Help-seeking keywords (multi-word phrases checked as substrings) ─
_HELP_SIGNALS: list[str] = [
    "advice", "help", "struggling", "years", "months",
    "nothing works", "getting worse", "desperate", "recommend",
    "any tips", "what should i do", "tried everything",
    "pain", "chronic", "can't sleep", "surgery",
    "scared", "terrified", "frustrated",
]

# ─── Pain/posture relevance keywords ────────────────────────────────
_RELEVANCE_KEYWORDS: frozenset[str] = frozenset({
    "pain", "back", "neck", "posture", "sciatica", "hip", "shoulder",
    "stretch", "exercise", "spine", "disc", "herniated", "chronic",
    "stiff", "sore", "mobility", "flexibility", "therapy", "rehab",
    "ergonomic", "desk", "sitting", "standing", "piriformis",
    "fibromyalgia", "kyphosis", "lordosis", "scoliosis", "plantar",
    "carpal", "headache", "tension", "foam", "roller", "corrective",
    # Yoga therapy terms
    "yoga", "restorative", "therapeutic", "yin",
    # Running recovery terms
    "runner", "running", "marathon", "achilles", "itband",
    # Longevity terms
    "longevity", "aging", "functional",
    # Cancer exercise terms
    "cancer", "chemotherapy", "oncology", "fatigue",
    # Additional clinical terms
    "pelvic", "thoracic", "cervical", "lumbar",
})


def _find_help_signals(text: str) -> list[str]:
    """Find which help-seeking keywords appear in the given text.

    Both single-word and multi-word phrases are matched as substrings
    against the lowercased text.

    Args:
        text: The text to scan (typically title + snippet).

    Returns:
        A list of matched help-signal strings.
    """
    lower = text.lower()
    return [signal for signal in _HELP_SIGNALS if signal in lower]


def _help_signal_density(text: str, help_signals: list[str]) -> float:
    """Calculate the density of help signals relative to total word count.

    Args:
        text: Original text.
        help_signals: Already-matched help signal strings.

    Returns:
        A float in [0.0, 1.0] representing signal count / total words.
        Capped at 1.0.
    """
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    return min(len(help_signals) / total_words, 1.0)


def _comment_engagement(comments: int) -> float:
    """Normalize comment count into a 0-1 score using a log scale.

    Formula: ``log(comments + 1) / 6``, capped at 1.0.

    Args:
        comments: Number of comments on the post.

    Returns:
        A float in [0.0, 1.0].
    """
    return min(math.log(comments + 1) / 6.0, 1.0)


def _relevance_score(title: str) -> float:
    """Calculate relevance as the fraction of title words that are pain/posture keywords.

    Args:
        title: The post or question title.

    Returns:
        A float in [0.0, 1.0].
    """
    words = title.lower().split()
    if not words:
        return 0.0
    matches = sum(1 for w in words if w in _RELEVANCE_KEYWORDS)
    return min(matches / len(words), 1.0)


def _compute_engagement_score(
    text: str,
    comments: int,
    is_new: bool,
    help_signals: list[str],
) -> float:
    """Compute the composite engagement score for a single post.

    Weights:
        - 0.30 help_signal_density
        - 0.25 comment_engagement (log-normalized)
        - 0.20 is_new bonus (1.0 if new, 0.3 if returning)
        - 0.15 relevance_score (title word overlap)
        - 0.10 recency_score (constant 1.0 for V1)

    Args:
        text: Combined title + snippet text for signal detection.
        comments: Number of comments.
        is_new: Whether this post is newly detected.
        help_signals: Pre-computed list of matched help signals.

    Returns:
        A float score, typically in [0.0, 1.0].
    """
    density = _help_signal_density(text, help_signals)
    comment_eng = _comment_engagement(comments)
    new_bonus = 1.0 if is_new else 0.3
    relevance = _relevance_score(text)
    recency = 1.0  # constant for V1 (all posts from last week)

    return round(
        0.30 * density
        + 0.25 * comment_eng
        + 0.20 * new_bonus
        + 0.15 * relevance
        + 0.10 * recency,
        4,
    )


def _reddit_posts_to_candidates(reddit: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Flatten Reddit data into a list of candidate dicts for scoring.

    Each candidate includes platform metadata and a text snippet.
    """
    candidates: list[dict[str, Any]] = []
    for subreddit, posts in reddit.items():
        if not isinstance(posts, list):
            continue
        for post in posts:
            if not isinstance(post, dict):
                continue
            title = post.get("title", "")
            # Use body if available, otherwise fall back to title
            body = post.get("body", post.get("selftext", ""))
            snippet = body[:200] if body else title
            candidates.append({
                "platform": "reddit",
                "title": title,
                "url": post.get("url", post.get("permalink", "")),
                "subreddit": post.get("subreddit", subreddit),
                "score": int(post.get("score", 0)),
                "comments": int(post.get("num_comments", post.get("comments", 0))),
                "is_new": bool(post.get("is_new", True)),
                "snippet": snippet,
            })
    return candidates


def _quora_to_candidates(quora: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Quora data into candidate dicts for scoring."""
    candidates: list[dict[str, Any]] = []
    for item in quora:
        question = item.get("question", "")
        candidates.append({
            "platform": "quora",
            "title": question,
            "url": item.get("url", ""),
            "subreddit": None,
            "score": 0,
            "comments": 0,
            "is_new": bool(item.get("is_new", True)),
            "snippet": question,
        })
    return candidates


def rank_engagement_opportunities(
    reddit: dict[str, list[dict[str, Any]]] | None,
    quora: list[dict[str, Any]] | None,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Select the top N posts where Bart should reply.

    Combines Reddit posts and Quora questions, scores each using a
    weighted composite of help-signal density, comment engagement,
    novelty, relevance, and recency, then returns the highest-scoring
    opportunities.

    Args:
        reddit: Reddit data dict mapping subreddits to post lists,
            or ``None``.
        quora: List of Quora question dicts, or ``None``.
        top_n: Maximum number of opportunities to return. Defaults to 5.

    Returns:
        A ranked list of dicts, each containing ``rank``, ``platform``,
        ``title``, ``url``, ``subreddit``, ``score``, ``comments``,
        ``is_new``, ``help_signals``, ``snippet``, and
        ``engagement_score``.
    """
    candidates: list[dict[str, Any]] = []

    if reddit:
        candidates.extend(_reddit_posts_to_candidates(reddit))

    if quora:
        candidates.extend(_quora_to_candidates(quora))

    if not candidates:
        return []

    # Score each candidate
    scored: list[dict[str, Any]] = []
    for cand in candidates:
        text = f"{cand['title']} {cand['snippet']}"
        help_signals = _find_help_signals(text)
        eng_score = _compute_engagement_score(
            text=text,
            comments=cand["comments"],
            is_new=cand["is_new"],
            help_signals=help_signals,
        )
        scored.append({
            "platform": cand["platform"],
            "title": cand["title"],
            "url": cand["url"],
            "subreddit": cand["subreddit"],
            "score": cand["score"],
            "comments": cand["comments"],
            "is_new": cand["is_new"],
            "help_signals": help_signals,
            "snippet": cand["snippet"],
            "engagement_score": eng_score,
        })

    # Sort by engagement score descending, then by post score as tiebreaker
    scored.sort(key=lambda x: (x["engagement_score"], x["score"]), reverse=True)

    # Take top N and assign ranks
    results: list[dict[str, Any]] = []
    for i, item in enumerate(scored[:top_n]):
        item["rank"] = i + 1
        results.append(item)

    return results
