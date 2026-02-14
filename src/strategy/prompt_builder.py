"""Trend Engine V2.0 — Claude Prompt Construction.

Builds a comprehensive prompt for Claude that includes all available data
sources (Google Trends, Reddit, Quora, Wikipedia, PubMed, News, emerging
signals) and requests structured JSON output for a weekly content playbook.
"""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# System context block (always included)
# ---------------------------------------------------------------------------
_SYSTEM_CONTEXT = (
    "You are a content strategist for Bart Firch, an expert Pain Management "
    "and Longevity Coach based in the Bay Area (Sacramento/San Francisco). "
    "His credentials and differentiators:\n"
    "- 15,000+ hours of clinical experience in corrective exercise and pain management\n"
    "- 10,000+ hours of yoga teaching (therapeutic, restorative, and power yoga)\n"
    "- ACSM-Certified Cancer Exercise Trainer (CET) — a rare and high-value certification\n"
    "- Ultra marathoner with deep knowledge of running biomechanics and recovery\n"
    "- Longevity and functional aging specialist\n\n"
    "His target audience segments (in priority order):\n"
    "1. Silicon Valley executives/founders with desk-related pain\n"
    "2. Chronic pain patients seeking non-surgical solutions\n"
    "3. Cancer survivors/patients needing safe exercise guidance\n"
    "4. Runners and athletes dealing with overuse injuries\n"
    "5. Desk workers and remote employees with posture issues\n"
    "6. Adults 40+ focused on longevity and functional movement\n\n"
    "IMPORTANT: Leverage ALL of Bart's expertise in the playbook — not just "
    "pain management. When the data supports it, incorporate yoga-based "
    "solutions, running recovery angles, cancer exercise safety, or longevity "
    "framing. These differentiators set Bart apart from generic fitness creators.\n\n"
    "You produce a weekly content playbook that Bart executes across 8 "
    "platforms (YouTube, LinkedIn, IG, TikTok, Facebook, blog, Medium, "
    "Pinterest).\n\n"
    "Your output MUST be valid JSON matching the schema below. No markdown "
    "fencing, no explanation outside the JSON."
)

# ---------------------------------------------------------------------------
# Required JSON output schema (always included)
# ---------------------------------------------------------------------------
_OUTPUT_SCHEMA = """\
REQUIRED JSON OUTPUT SCHEMA:
{
  "theme_narrative": "2-3 sentences on why this topic matters NOW. Reference specific data.",
  "monday_video": {
    "title": "YouTube title: [Problem] — N Exercises That Actually Work (2026)",
    "hook": "First 10 seconds script. Reference a specific data point.",
    "talking_points": ["point 1", "point 2", "point 3", "point 4"],
    "exercises": [
      {"name": "Exercise Name", "form_cue": "[Bart: add specific form cue]"}
    ],
    "end_cta": "CTA referencing Wednesday's follow-up.",
    "thumbnail": {
      "text_overlay": "Bold 3-5 word text for thumbnail overlay",
      "pose_suggestion": "What Bart should be doing in the thumbnail image",
      "color_scheme": "Suggested contrast colors (e.g. 'red text on dark background')"
    },
    "viewer_assessment": "A simple self-test viewers can do before the exercises to gauge their issue (e.g. 'Try this: stand on one leg with eyes closed for 30 seconds. If you wobble, your hip stabilizers need work.')",
    "platforms": {
      "youtube": {"description": "SEO description with timestamps and blog link.", "tags": ["tag1", "tag2", "...8 tags"]},
      "linkedin": "Native video caption with provocative stat hook.",
      "instagram_reels": "60-90 sec caption with hashtags.",
      "tiktok": "Casual caption."
    }
  },
  "wednesday_post": {
    "linkedin_draft": "300-600 word post referencing Monday video and comment themes. Include [Bart: add...] placeholders for clinical detail. If PubMed studies were provided, reference at least one.",
    "blog_title": "SEO-optimized article title.",
    "blog_meta_description": "155 char meta description.",
    "medium_subtitle": "Subtitle for Medium cross-post.",
    "cross_post_note": "Blog (bartonfirch.com) -> Medium (canonical to blog) -> Substack",
    "study_citation": "If PubMed data was provided, write a 1-sentence citation Bart can drop into the blog post."
  },
  "friday_card": {
    "stat_headline": "Bold data stat for social card.",
    "tip": "One actionable tip.",
    "engagement_ask": "Question referencing Monday's exercises. 'How do you feel after 4 days?'",
    "platforms": {
      "linkedin": "Caption.",
      "pinterest": "Keyword-rich pin description.",
      "twitter": "Thread format: stat -> tip -> link."
    }
  },
  "seo_notes": {
    "target_keyword": "Primary long-tail keyword.",
    "secondary_keywords": ["kw1", "kw2", "kw3"],
    "schema_types": ["HowTo", "FAQPage"],
    "ai_findability_tips": ["tip1", "tip2", "tip3"]
  },
  "engagement_replies": [
    {
      "post_title": "Title of the engagement opportunity post",
      "suggested_reply": "3-4 sentence helpful reply. Clinical expertise, no pitch, no link. Draw from Bart's 15K hours."
    }
  ]
}"""


# ---------------------------------------------------------------------------
# Internal helpers — work with raw analysis dict from build_analysis()
# ---------------------------------------------------------------------------

def _format_google_trends(analysis: dict) -> str | None:
    """Format Google Trends keywords as a text table.

    Handles raw format: analysis["google"] = {keyword: {current, prev_week, wow_pct, ...}}
    """
    google = analysis.get("google")
    if not google or not isinstance(google, dict):
        return None

    lines: list[str] = ["TREND DATA (Google Trends — scores are relative search interest 0-100 where 100 = peak popularity this quarter, NOT percentage of searches):"]
    lines.append(f"{'Keyword':<30} {'Interest':>8} {'WoW%':>7} {'4w Trend':>10}")
    lines.append("-" * 58)

    for kw, data in google.items():
        if not isinstance(data, dict):
            continue
        score = data.get("current", "")
        wow = data.get("wow_pct", "")
        trend = data.get("4w_trend", "")
        lines.append(f"{kw:<30} {score!s:>8} {wow!s:>7} {trend!s:>10}")

    # Rising queries
    rising = analysis.get("rising_queries")
    if rising and isinstance(rising, dict):
        lines.append("")
        lines.append("Rising queries per keyword:")
        for keyword, kw_data in rising.items():
            if isinstance(kw_data, dict):
                rising_list = kw_data.get("rising", [])
                if rising_list:
                    queries = [q.get("query", str(q)) for q in rising_list[:5]]
                    lines.append(f"  {keyword}: {', '.join(queries)}")

    return "\n".join(lines)


def _format_reddit(analysis: dict) -> str | None:
    """Format Reddit posts as a bullet list.

    Handles raw format: analysis["reddit"] = {subreddit: [post_dicts]}
    """
    reddit = analysis.get("reddit")
    if not reddit or not isinstance(reddit, dict):
        return None

    lines: list[str] = ["REDDIT:"]
    for subreddit, posts in reddit.items():
        if not isinstance(posts, list):
            continue
        for post in posts:
            if not isinstance(post, dict):
                continue
            title = post.get("title", "")
            score = post.get("score", 0)
            comments = post.get("comments", post.get("num_comments", 0))
            new_tag = " [NEW]" if post.get("is_new") else ""
            lines.append(f"  - r/{subreddit}: {title} (score {score}, {comments} comments){new_tag}")

    return "\n".join(lines) if len(lines) > 1 else None


def _format_quora(analysis: dict) -> str | None:
    """Format Quora questions as a simple list.

    Handles raw format: analysis["quora"] = [{question, url, ...}]
    """
    quora = analysis.get("quora")
    if not quora or not isinstance(quora, list):
        return None

    lines: list[str] = ["QUORA:"]
    for item in quora:
        if isinstance(item, dict):
            question = item.get("question", str(item))
        else:
            question = str(item)
        lines.append(f"  - {question}")

    return "\n".join(lines) if len(lines) > 1 else None


def _format_wikipedia(analysis: dict) -> str | None:
    """Format Wikipedia article pageviews with WoW changes.

    Handles raw format: analysis["wikipedia"] = {article: {current_week_avg, wow_pct, ...}}
    """
    wiki = analysis.get("wikipedia")
    if not wiki or not isinstance(wiki, dict):
        return None

    lines: list[str] = ["WIKIPEDIA:"]
    for article, data in wiki.items():
        if not isinstance(data, dict):
            continue
        title = article.replace("_", " ")
        views = round(data.get("current_week_avg", 0))
        wow = data.get("wow_pct", "N/A")
        lines.append(f"  - {title}: {views} views/day (WoW: {wow}%)")

    return "\n".join(lines) if len(lines) > 1 else None


def _format_pubmed(analysis: dict) -> str | None:
    """Format PubMed study titles and journals.

    Handles raw format: analysis["pubmed"] = [{title, journal, date, pmid}]
    """
    pubmed = analysis.get("pubmed")
    if not pubmed or not isinstance(pubmed, list):
        return None

    lines: list[str] = ["PUBMED:"]
    for study in pubmed:
        if not isinstance(study, dict):
            continue
        title = study.get("title", "")
        journal = study.get("journal", "")
        suffix = f" ({journal})" if journal else ""
        lines.append(f"  - {title}{suffix}")

    return "\n".join(lines) if len(lines) > 1 else None


def _format_news(analysis: dict) -> str | None:
    """Format news headlines and sources.

    Handles raw format: analysis["news"] = [{title, source, url, date}]
    """
    news = analysis.get("news")
    if not news or not isinstance(news, list):
        return None

    lines: list[str] = ["NEWS:"]
    for item in news:
        if not isinstance(item, dict):
            continue
        headline = item.get("title", "")
        source = item.get("source", "")
        suffix = f" — {source}" if source else ""
        lines.append(f"  - {headline}{suffix}")

    return "\n".join(lines) if len(lines) > 1 else None


def _format_emerging(emerging: dict) -> str | None:
    """Format emerging signals section (highest priority)."""
    if not emerging:
        return None

    parts: list[str] = [
        "EMERGING SIGNALS (HIGHEST PRIORITY — prioritize these in the playbook):"
    ]

    rising = emerging.get("new_rising_queries")
    if rising:
        queries_str = ", ".join(
            q.get("query", str(q)) if isinstance(q, dict) else str(q)
            for q in rising
        )
        parts.append(f"  New rising queries: {queries_str}")

    reddit_new = emerging.get("new_reddit_topics")
    if reddit_new:
        parts.append("  New Reddit conversations:")
        for post in reddit_new:
            if isinstance(post, dict):
                title = post.get("title", str(post))
                novel = post.get("novel_terms", [])
                novel_str = f" (novel terms: {', '.join(novel)})" if novel else ""
                parts.append(f"    - {title}{novel_str}")
            else:
                parts.append(f"    - {post}")

    wiki_breakout = emerging.get("wikipedia_breakouts")
    if wiki_breakout:
        breakout_strs = []
        for b in wiki_breakout:
            if isinstance(b, dict):
                article = b.get("article", "").replace("_", " ")
                wow = b.get("wow_pct", "")
                breakout_strs.append(f"{article} (+{wow}%)")
            else:
                breakout_strs.append(str(b))
        parts.append(f"  Wikipedia breakouts: {', '.join(breakout_strs)}")

    quora_new = emerging.get("new_quora_questions")
    if quora_new:
        parts.append("  New Quora questions:")
        for q in quora_new:
            if isinstance(q, dict):
                question = q.get("question", str(q))
            else:
                question = str(q)
            parts.append(f"    - {question}")

    # Only return if we have more than the header
    return "\n".join(parts) if len(parts) > 1 else None


def _format_continuity(prior_theme: str | None) -> str | None:
    """Format continuity section for theme transitions."""
    if not prior_theme:
        return None
    return (
        f"CONTINUITY:\n"
        f"Last week's theme was '{prior_theme}'. Write a brief transition "
        f"sentence in theme_narrative that bridges from last week to this week."
    )


def _format_exercise_map(
    topic_solutions: dict,
    theme: str = "",
    exercise_protocols: dict | None = None,
) -> str | None:
    """Format a filtered exercise prescription map as compact JSON.

    Only includes exercises relevant to the current theme and closely
    related topics, reducing prompt tokens by ~50% vs sending the full map.

    When ``exercise_protocols`` (structured clinical data with sets/reps,
    progressions, regressions, and contraindications) is provided, merges
    that detail into the output so Claude can generate richer prescriptions.
    """
    if not topic_solutions:
        return None

    # Filter to theme-relevant entries to save tokens
    theme_lower = theme.lower()
    relevant: dict[str, list] = {}

    for key, exercises in topic_solutions.items():
        key_lower = key.lower()
        # Include if: exact match, key appears in theme, theme appears in key,
        # or they share a significant word (>4 chars)
        if (
            key_lower == theme_lower
            or key_lower in theme_lower
            or theme_lower in key_lower
        ):
            relevant[key] = exercises
            continue

        # Check for shared significant words
        theme_words = {w for w in theme_lower.split() if len(w) > 3}
        key_words = {w for w in key_lower.split() if len(w) > 3}
        if theme_words & key_words:
            relevant[key] = exercises

    # Always include at least 5 entries for variety — add top entries by key overlap
    if len(relevant) < 5:
        for key, exercises in list(topic_solutions.items())[:8]:
            if key not in relevant:
                relevant[key] = exercises
            if len(relevant) >= 8:
                break

    # Merge clinical protocols (sets/reps/progressions/contraindications)
    if exercise_protocols:
        for key in list(relevant.keys()):
            if key in exercise_protocols:
                relevant[key] = exercise_protocols[key]

    parts = [f"EXERCISE PRESCRIPTION MAP (filtered for '{theme}'):"]
    parts.append(json.dumps(relevant, indent=2, ensure_ascii=False))

    if exercise_protocols:
        parts.append(
            "\nNOTE: Entries with 'sets', 'progression', 'regression', "
            "and 'contraindication' fields are clinical-grade protocols. "
            "Include sets/reps and a contraindication warning in the exercises "
            "output when this data is available."
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_claude_prompt(
    analysis: dict,
    emerging: dict,
    prior_theme: str | None,
    topic_solutions: dict,
    is_first_run: bool,
    seasonal: dict | None = None,
    exercise_protocols: dict | None = None,
) -> str:
    """Build a comprehensive prompt for Claude with all available data sources.

    Each section is only included when data is available. The prompt requests
    a structured JSON response matching the weekly content playbook schema.

    Parameters
    ----------
    analysis:
        Aggregated analysis dict from build_analysis() containing raw data
        under keys like ``google``, ``reddit``, ``quora``, ``wikipedia``,
        ``pubmed``, ``news``, ``theme``.
    emerging:
        Dict of emerging signals (new rising queries, new Reddit posts,
        Wikipedia breakouts, new Quora questions).
    prior_theme:
        The theme from the previous week, or ``None`` on first run.
    topic_solutions:
        Mapping of topic names to lists of recommended exercises.
    is_first_run:
        ``True`` if this is the first execution (no prior history).
    seasonal:
        Optional seasonal context dict from ``get_seasonal_context()``.

    Returns
    -------
    str
        The assembled prompt string.
    """
    sections: list[str] = []

    # Always include system context
    sections.append(f"SYSTEM CONTEXT:\n{_SYSTEM_CONTEXT}")

    # Theme
    theme = analysis.get("theme", "")
    if theme:
        sections.append(f"THIS WEEK'S THEME: {theme}")

    # Seasonal context
    if seasonal:
        season_name = seasonal.get("season_name", "")
        context_note = seasonal.get("context_note", "")
        angles = seasonal.get("suggested_angles", [])
        seasonal_text = f"SEASONAL CONTEXT ({season_name}):\n{context_note}"
        if angles:
            seasonal_text += "\nSuggested seasonal angles:\n" + "\n".join(
                f"  - {a}" for a in angles
            )
        sections.append(seasonal_text)

    # Data source sections — only included when data is present
    formatters = [
        _format_google_trends(analysis),
        _format_reddit(analysis),
        _format_quora(analysis),
        _format_wikipedia(analysis),
        _format_pubmed(analysis),
        _format_news(analysis),
    ]
    for formatted in formatters:
        if formatted:
            sections.append(formatted)

    # Emerging signals — highest priority
    emerging_section = _format_emerging(emerging)
    if emerging_section:
        sections.append(emerging_section)

    # Continuity with prior theme
    continuity = _format_continuity(prior_theme)
    if continuity:
        sections.append(continuity)

    # Exercise prescription map (filtered to theme for token efficiency)
    exercise_map = _format_exercise_map(
        topic_solutions, theme, exercise_protocols=exercise_protocols,
    )
    if exercise_map:
        sections.append(exercise_map)

    # First-run instruction
    if is_first_run:
        sections.append(
            "NOTE: This is the first weekly run. There is no prior playbook "
            "to reference — set the tone and establish the brand voice."
        )

    # Output schema (always last)
    sections.append(_OUTPUT_SCHEMA)

    return "\n\n".join(sections)
