"""
Trend Engine V2.0 — Emerging Signal Detection
=========================================================
Compares current week's collected data against a prior snapshot to
surface genuinely NEW signals: rising queries, Reddit conversations,
Wikipedia breakouts, and Quora questions.
"""

from __future__ import annotations

from typing import Any

# ─── Stopwords used for Reddit topic fingerprinting ──────────────────
_STOPWORDS: frozenset[str] = frozenset({
    "the", "is", "a", "an", "my", "i", "me", "we", "our", "you", "your",
    "it", "its", "this", "that", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "from", "by", "as", "be", "was", "were",
    "been", "am", "are", "do", "does", "did", "have", "has", "had",
    "will", "would", "could", "should", "can", "may", "might", "not",
    "no", "so", "if", "then", "just", "also", "very", "really", "about",
    "all", "any", "some", "what", "when", "how", "who", "which", "there",
    "here", "more", "other", "than", "too", "only", "after", "before",
    "now", "into", "over", "up", "out", "like", "im", "ive", "dont",
    "cant", "get", "got", "going", "been", "still", "even",
})


def _fingerprint(text: str) -> frozenset[str]:
    """Create a topic fingerprint from text.

    Lowercases, splits on whitespace, and removes common stopwords.
    Returns the remaining significant words as a frozenset.
    """
    words = text.lower().split()
    return frozenset(w for w in words if w not in _STOPWORDS)


def _best_overlap(fingerprint: frozenset[str], prior_fingerprints: set[frozenset[str]]) -> float:
    """Compute the highest Jaccard-like overlap between a fingerprint and a set of prior fingerprints.

    Returns a float in [0.0, 1.0] representing the fraction of the current
    fingerprint's words found in the closest prior fingerprint.
    """
    if not fingerprint or not prior_fingerprints:
        return 0.0

    best = 0.0
    for prior_fp in prior_fingerprints:
        overlap_count = len(fingerprint & prior_fp)
        total = len(fingerprint)
        if total > 0:
            ratio = overlap_count / total
            if ratio > best:
                best = ratio
    return best


def _all_prior_words(prior_fingerprints: set[frozenset[str]]) -> frozenset[str]:
    """Flatten all prior fingerprints into a single set of known words."""
    combined: set[str] = set()
    for fp in prior_fingerprints:
        combined |= fp
    return frozenset(combined)


def _extract_rising_query_set(
    rising_queries: dict[str, dict[str, list[dict[str, Any]]]] | None,
) -> set[str]:
    """Extract the set of all rising query strings from a rising_queries dict."""
    queries: set[str] = set()
    if not rising_queries:
        return queries
    for keyword_data in rising_queries.values():
        for entry in keyword_data.get("rising", []):
            query = entry.get("query", "")
            if query:
                queries.add(query)
    return queries


def _google_score_for_keyword(
    google: dict[str, dict[str, Any]] | None, keyword: str,
) -> int:
    """Look up the current Google Trends score for a parent keyword."""
    if not google or keyword not in google:
        return 0
    return int(google[keyword].get("current", 0))


def _find_parent_keyword(
    query: str,
    rising_queries: dict[str, dict[str, list[dict[str, Any]]]] | None,
) -> str | None:
    """Find which parent keyword a rising query belongs to."""
    if not rising_queries:
        return None
    for keyword, keyword_data in rising_queries.items():
        for entry in keyword_data.get("rising", []):
            if entry.get("query", "") == query:
                return keyword
    return None


def _extract_reddit_posts(reddit: dict | None) -> list[dict[str, Any]]:
    """Flatten the Reddit data structure into a single list of post dicts."""
    posts: list[dict[str, Any]] = []
    if not reddit:
        return posts
    for subreddit_name, subreddit_posts in reddit.items():
        if not isinstance(subreddit_posts, list):
            continue
        for post in subreddit_posts:
            if isinstance(post, dict):
                enriched = dict(post)
                if "subreddit" not in enriched:
                    enriched["subreddit"] = subreddit_name
                posts.append(enriched)
    return posts


def _extract_quora_fingerprints(quora: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    """Build a mapping of fingerprint-string -> quora item for deduplication."""
    result: dict[str, dict[str, Any]] = {}
    if not quora:
        return result
    for item in quora:
        question = item.get("question", "")
        fp = str(sorted(_fingerprint(question)))
        result[fp] = item
    return result


# ═════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════


def detect_emerging_signals(
    current: dict[str, Any],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare current week's data against a prior snapshot to find new signals.

    Args:
        current: Dict with keys ``google``, ``rising_queries``, ``reddit``,
            ``quora``, ``wikipedia``.
        prior: Same structure from the prior snapshot, or ``None`` on first run.

    Returns:
        A dict containing ``new_rising_queries``, ``new_reddit_topics``,
        ``wikipedia_breakouts``, ``new_quora_questions``, ``is_first_run``,
        and a human-readable ``summary`` string.
    """
    is_first_run = prior is None

    cur_google = current.get("google") or {}
    cur_rising = current.get("rising_queries")
    cur_reddit = current.get("reddit")
    cur_quora = current.get("quora")
    cur_wiki = current.get("wikipedia")

    pri_rising = prior.get("rising_queries") if prior else None
    pri_reddit = prior.get("reddit") if prior else None
    pri_quora = prior.get("quora") if prior else None
    pri_wiki = prior.get("wikipedia") if prior else None

    # ── Rising Query Diff ───────────────────────────────────────────
    new_rising_queries: list[dict[str, Any]] = []
    if not is_first_run:
        cur_query_set = _extract_rising_query_set(cur_rising)
        pri_query_set = _extract_rising_query_set(pri_rising)
        new_queries = cur_query_set - pri_query_set

        for query in new_queries:
            parent = _find_parent_keyword(query, cur_rising)
            parent_score = _google_score_for_keyword(cur_google, parent) if parent else 0
            new_rising_queries.append({
                "query": query,
                "parent_keyword": parent or "unknown",
                "parent_score": parent_score,
            })

        new_rising_queries.sort(key=lambda x: x["parent_score"], reverse=True)

    # ── Reddit Topic Diff ───────────────────────────────────────────
    new_reddit_topics: list[dict[str, Any]] = []
    cur_posts = _extract_reddit_posts(cur_reddit)

    if is_first_run:
        # First run: return top 5 by score, don't flag everything
        sorted_posts = sorted(
            cur_posts,
            key=lambda p: int(p.get("score", 0)),
            reverse=True,
        )
        for post in sorted_posts[:5]:
            fp = _fingerprint(post.get("title", ""))
            new_reddit_topics.append({
                "title": post.get("title", ""),
                "subreddit": post.get("subreddit", ""),
                "score": int(post.get("score", 0)),
                "url": post.get("url", post.get("permalink", "")),
                "novel_terms": sorted(fp),
            })
    else:
        pri_posts = _extract_reddit_posts(pri_reddit)
        prior_fingerprints: set[frozenset[str]] = set()
        for post in pri_posts:
            fp = _fingerprint(post.get("title", ""))
            if fp:
                prior_fingerprints.add(fp)

        all_prior = _all_prior_words(prior_fingerprints)

        for post in cur_posts:
            fp = _fingerprint(post.get("title", ""))
            if not fp:
                continue
            overlap = _best_overlap(fp, prior_fingerprints)
            if overlap < 0.50:
                novel = sorted(fp - all_prior)
                new_reddit_topics.append({
                    "title": post.get("title", ""),
                    "subreddit": post.get("subreddit", ""),
                    "score": int(post.get("score", 0)),
                    "url": post.get("url", post.get("permalink", "")),
                    "novel_terms": novel,
                })

        new_reddit_topics.sort(key=lambda x: x["score"], reverse=True)

    # ── Wikipedia Breakouts ─────────────────────────────────────────
    wikipedia_breakouts: list[dict[str, Any]] = []
    if cur_wiki and isinstance(cur_wiki, dict):
        for article, data in cur_wiki.items():
            if not isinstance(data, dict):
                continue

            wow_pct = data.get("wow_pct")
            current_avg = data.get("current_week_avg", data.get("current_avg", 0))
            prior_avg = data.get("prior_week_avg", data.get("prior_avg", 0))

            # On first run, use internal WoW data (current_week_avg vs prior_week_avg)
            # On subsequent runs, also use internal WoW data since it is always computed
            if wow_pct is not None and wow_pct > 15:
                wikipedia_breakouts.append({
                    "article": article,
                    "current_avg": current_avg,
                    "prior_avg": prior_avg,
                    "wow_pct": round(float(wow_pct), 1),
                })

    wikipedia_breakouts.sort(key=lambda x: x["wow_pct"], reverse=True)

    # ── Quora Diff ──────────────────────────────────────────────────
    new_quora_questions: list[dict[str, Any]] = []
    if not is_first_run:
        cur_quora_fps = _extract_quora_fingerprints(cur_quora)
        pri_quora_fps = _extract_quora_fingerprints(pri_quora)

        new_fp_keys = set(cur_quora_fps.keys()) - set(pri_quora_fps.keys())
        for fp_key in new_fp_keys:
            item = cur_quora_fps[fp_key]
            new_quora_questions.append({
                "question": item.get("question", ""),
                "url": item.get("url", ""),
                "fingerprint": fp_key,
            })

    # ── Summary ─────────────────────────────────────────────────────
    parts: list[str] = []
    if new_rising_queries:
        parts.append(f"{len(new_rising_queries)} new rising queries")
    if new_reddit_topics:
        parts.append(f"{len(new_reddit_topics)} new Reddit topics")
    if wikipedia_breakouts:
        parts.append(f"{len(wikipedia_breakouts)} Wikipedia breakout{'s' if len(wikipedia_breakouts) != 1 else ''}")
    if new_quora_questions:
        parts.append(f"{len(new_quora_questions)} new Quora questions")

    summary = "; ".join(parts) if parts else "No new emerging signals detected"

    return {
        "new_rising_queries": new_rising_queries,
        "new_reddit_topics": new_reddit_topics,
        "wikipedia_breakouts": wikipedia_breakouts,
        "new_quora_questions": new_quora_questions,
        "is_first_run": is_first_run,
        "summary": summary,
    }


def deduplicate_reddit_posts(
    current_posts: dict[str, list[dict[str, Any]]] | None,
    prior_posts: dict[str, list[dict[str, Any]]] | None,
) -> dict[str, list[dict[str, Any]]]:
    """Tag each Reddit post as NEW or RETURNING by matching on URL.

    Args:
        current_posts: Reddit data dict mapping subreddit names to lists of
            post dicts. May be ``None``.
        prior_posts: Same structure from the prior snapshot, or ``None``
            on first run.

    Returns:
        Same structure as ``current_posts``, but each post dict gains:
        ``is_new`` (bool), ``prior_score`` (int | None),
        ``score_delta`` (int | None).
    """
    if not current_posts:
        return {}

    # Build a lookup from URL -> post dict for prior data
    prior_by_url: dict[str, dict[str, Any]] = {}
    if prior_posts:
        for subreddit_posts in prior_posts.values():
            if not isinstance(subreddit_posts, list):
                continue
            for post in subreddit_posts:
                if isinstance(post, dict):
                    url = post.get("url", post.get("permalink", ""))
                    if url:
                        prior_by_url[url] = post

    result: dict[str, list[dict[str, Any]]] = {}

    for subreddit, posts in current_posts.items():
        if not isinstance(posts, list):
            result[subreddit] = posts
            continue

        tagged_posts: list[dict[str, Any]] = []
        for post in posts:
            if not isinstance(post, dict):
                tagged_posts.append(post)
                continue

            enriched = dict(post)
            url = post.get("url", post.get("permalink", ""))
            prior_match = prior_by_url.get(url) if url else None

            if prior_match is None:
                enriched["is_new"] = True
                enriched["prior_score"] = None
                enriched["score_delta"] = None
            else:
                prior_score = int(prior_match.get("score", 0))
                current_score = int(post.get("score", 0))
                enriched["is_new"] = False
                enriched["prior_score"] = prior_score
                enriched["score_delta"] = current_score - prior_score

            tagged_posts.append(enriched)

        result[subreddit] = tagged_posts

    return result


def detect_declining_signals(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Detect keywords and topics that are trending downward.

    Flags keywords with a negative week-over-week percentage across
    Google Trends data. These are topics Bart should consider avoiding
    or deprioritizing in the current week's content.

    Args:
        analysis: Dict with keys ``google`` and ``wikipedia`` containing
            raw collector data.

    Returns:
        A list of dicts with keys ``keyword``, ``wow_pct``, and
        ``trend_direction``, sorted by wow_pct ascending (most negative
        first). Only includes keywords with wow_pct < -10.
    """
    declining: list[dict[str, Any]] = []

    # Check Google Trends keywords
    google = analysis.get("google")
    if google and isinstance(google, dict):
        for keyword, data in google.items():
            if not isinstance(data, dict):
                continue
            wow_pct = data.get("wow_pct")
            trend = data.get("4w_trend", "stable")
            current_val = data.get("current", 0)
            if wow_pct is not None and wow_pct < -10 and current_val >= 15:
                declining.append({
                    "keyword": keyword,
                    "wow_pct": round(float(wow_pct), 1),
                    "trend_direction": trend,
                    "source": "google_trends",
                })

    # Check Wikipedia articles for declining interest
    wiki = analysis.get("wikipedia")
    if wiki and isinstance(wiki, dict):
        for article, data in wiki.items():
            if not isinstance(data, dict):
                continue
            wow_pct = data.get("wow_pct")
            current_avg = data.get("current_week_avg", data.get("current_avg", 0))
            if wow_pct is not None and wow_pct < -15 and current_avg >= 50:
                title = article.replace("_", " ")
                # Avoid duplicating if already in declining from Google
                if not any(d["keyword"].lower() == title.lower() for d in declining):
                    declining.append({
                        "keyword": title,
                        "wow_pct": round(float(wow_pct), 1),
                        "trend_direction": "declining",
                        "source": "wikipedia",
                    })

    # Sort by wow_pct ascending (most negative first)
    declining.sort(key=lambda x: x["wow_pct"])

    return declining
