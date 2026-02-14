#!/usr/bin/env python3
"""
FormCoach Trend Engine V2.0 — Main Orchestrator
=================================================
Sunday night cron -> Monday morning email.

Collects trend data from 7 sources, compares against last week's
snapshot, detects emerging signals, applies seasonal context and
movement assessments, calls Claude API for a complete content playbook,
and sends Bart one email with everything he needs.

Usage:
    python src/trend_engine.py                  # Full run + email
    python src/trend_engine.py --preview        # Print HTML, no email
    python src/trend_engine.py --skip-google    # Skip Google Trends
    python src/trend_engine.py --skip-reddit    # Skip Reddit
    python src/trend_engine.py --skip-quora     # Skip Quora scraping
    python src/trend_engine.py --skip-wiki      # Skip Wikipedia
    python src/trend_engine.py --skip-pubmed    # Skip PubMed
    python src/trend_engine.py --with-rising    # Enable rising queries (off by default)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# ── Logging ──
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _setup_logging():
    """Configure dual logging: console + file."""
    log_file = _DATA_DIR / f"run_{datetime.now().strftime('%Y-%m-%d_%H%M')}.log"

    # File handler — captures everything
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
    ))

    # Console handler — info and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return log_file


# ── Configuration ──
from config import (
    KEYWORDS, SUBREDDITS, EXEC_SUBREDDITS,
    QUORA_SEARCH_QUERIES, WIKI_ARTICLES, TOPIC_SOLUTIONS,
    EXERCISE_PROTOCOLS,
    EMAIL_CONFIG, ANTHROPIC_API_KEY,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
    get_all_keywords,
)

# ── Collectors ──
from collectors.google_trends import collect_google_trends, collect_rising_queries
from collectors.reddit import collect_reddit, collect_local_leads
from collectors.reddit_json import collect_reddit_json, collect_local_leads_json
from collectors.quora import collect_quora
from collectors.wikipedia import collect_wikipedia_pageviews
from collectors.pubmed import collect_pubmed
from collectors.news import collect_rss_news
from collectors.hackernews import collect_hacker_news_leads

# ── Analysis ──
from analysis.emerging import detect_emerging_signals, deduplicate_reddit_posts, detect_declining_signals
from analysis.theme import build_analysis, select_theme
from analysis.engagement import rank_engagement_opportunities
from analysis.seasonal import get_seasonal_context
from analysis.assessment import suggest_assessment
from analysis.reddit_filter import filter_reddit_posts
from analysis.hackernews_filter import filter_hackernews_leads

# ── Strategy ──
from strategy.prompt_builder import build_claude_prompt
from strategy.claude_client import call_claude
from strategy.fallback import generate_fallback_strategy

# ── Rendering ──
from rendering.email_builder import render_email
from rendering.sender import send_email

# ── Persistence ──
from persistence.snapshot import (
    load_latest_snapshot, save_snapshot, get_brief_number, save_html,
)


def parse_args() -> set:
    """Parse CLI flags."""
    return set(sys.argv[1:])


def main():
    log_file = _setup_logging()
    logger = logging.getLogger("trend_engine")

    args = parse_args()
    preview = "--preview" in args
    use_cache = "--use-cache" in args
    skip_google = "--skip-google" in args
    skip_reddit = "--skip-reddit" in args
    skip_quora = "--skip-quora" in args
    skip_wiki = "--skip-wiki" in args
    skip_pubmed = "--skip-pubmed" in args
    with_rising = "--with-rising" in args

    logger.info("=" * 60)
    logger.info("  Trend Engine V2.0")
    logger.info("=" * 60)

    # ────────────────────────────────────────────────────────
    # 1. LOAD PRIOR SNAPSHOT
    # ────────────────────────────────────────────────────────
    logger.info("\n[1/9] Loading prior snapshot...")
    prior = load_latest_snapshot()
    is_first_run = prior is None
    prior_theme = prior.get("theme") if prior else None

    if is_first_run:
        logger.info("  First run detected — baseline report (no deltas)")
    else:
        logger.info(f"  Prior theme: '{prior_theme}' from {prior.get('date', 'unknown')}")

    # ────────────────────────────────────────────────────────
    # 2. COLLECT DATA
    # ────────────────────────────────────────────────────────
    logger.info("\n[2/9] Collecting data...")
    all_kw = get_all_keywords()

    # Google Trends
    google = None
    rising = None
    if not skip_google:
        logger.info("\n  --- Google Trends ---")
        if use_cache:
            logger.info("  Using cached data (--use-cache)")
        google = collect_google_trends(all_kw, use_cache=use_cache)
        if with_rising:
            rising = collect_rising_queries(all_kw, use_cache=use_cache)
        else:
            logger.info("  Rising queries skipped (use --with-rising to enable)")
    else:
        logger.info("  Skipping Google Trends (--skip-google)")

    # Reddit — uses PRAW if API keys are set, otherwise public JSON endpoints
    reddit_raw = None
    leads = None
    if not skip_reddit:
        logger.info("\n  --- Reddit ---")
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            logger.info("  Using PRAW (API keys detected)")
            reddit_raw = collect_reddit(
                SUBREDDITS,
                REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
            )
            leads = collect_local_leads(
                EXEC_SUBREDDITS,
                REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
            )
        else:
            logger.info("  No Reddit API keys — using public JSON endpoints")
            reddit_raw = collect_reddit_json(SUBREDDITS)
            leads = collect_local_leads_json(EXEC_SUBREDDITS)
    else:
        logger.info("  Skipping Reddit (--skip-reddit)")

    # Quora
    quora = None
    if not skip_quora:
        logger.info("\n  --- Quora ---")
        quora = collect_quora(QUORA_SEARCH_QUERIES)
    else:
        logger.info("  Skipping Quora (--skip-quora)")

    # Wikipedia
    wikipedia = None
    if not skip_wiki:
        logger.info("\n  --- Wikipedia ---")
        wikipedia = collect_wikipedia_pageviews(WIKI_ARTICLES)
    else:
        logger.info("  Skipping Wikipedia (--skip-wiki)")

    # PubMed
    pubmed = None
    if not skip_pubmed:
        logger.info("\n  --- PubMed ---")
        pubmed = collect_pubmed(EMAIL_CONFIG.get("sender", ""))
    else:
        logger.info("  Skipping PubMed (--skip-pubmed)")

    # News (RSS) — always runs, very fast
    logger.info("\n  --- News (Google RSS) ---")
    news = collect_rss_news()

    # Hacker News — always runs, fast
    logger.info("\n  --- Hacker News ---")
    hn_leads = collect_hacker_news_leads()

    # ────────────────────────────────────────────────────────
    # 3. DEDUPLICATE REDDIT POSTS
    # ────────────────────────────────────────────────────────
    logger.info("\n[3/9] Deduplicating Reddit posts...")
    reddit = deduplicate_reddit_posts(
        reddit_raw,
        prior.get("reddit") if prior else None,
    )

    # ────────────────────────────────────────────────────────
    # 3.5. FILTER REDDIT FOR RELEVANCE
    # ────────────────────────────────────────────────────────
    logger.info("\n[3.5/9] Filtering Reddit for relevance...")
    reddit = filter_reddit_posts(reddit)

    # ────────────────────────────────────────────────────────
    # 3.6. FILTER HACKER NEWS FOR RELEVANCE
    # ────────────────────────────────────────────────────────
    logger.info("\n[3.6/9] Filtering Hacker News for relevance...")
    hn_leads = filter_hackernews_leads(hn_leads)

    # ────────────────────────────────────────────────────────
    # 4. DETECT EMERGING SIGNALS
    # ────────────────────────────────────────────────────────
    logger.info("\n[4/9] Detecting emerging signals...")
    current_data = {
        "google": google,
        "rising_queries": rising,
        "reddit": reddit,
        "quora": quora,
        "wikipedia": wikipedia,
    }
    emerging = detect_emerging_signals(current_data, prior)
    logger.info(f"  {emerging.get('summary', 'No emerging signals')}")

    # ────────────────────────────────────────────────────────
    # 5. BUILD ANALYSIS & SELECT THEME
    # ────────────────────────────────────────────────────────
    logger.info("\n[5/9] Building analysis...")
    theme = select_theme(google, wikipedia, reddit, prior_theme)
    analysis = build_analysis(
        google, rising, reddit, quora, wikipedia,
        pubmed, news, leads, hn_leads,
    )
    analysis["theme"] = theme
    logger.info(f"  Theme: '{theme}'")
    body_groups = analysis.get("body_part_groups", [])
    if body_groups:
        logger.info(f"  Body-part groups: {len(body_groups)} ({body_groups[0]['label']} leads)")

    # Rank engagement opportunities
    engagement_opps = rank_engagement_opportunities(reddit, quora)
    logger.info(f"  Engagement opportunities: {len(engagement_opps)}")

    # Seasonal context
    seasonal = get_seasonal_context()
    logger.info(f"  Seasonal context: {seasonal['season_name']}")

    # Declining signals
    declining = detect_declining_signals(analysis)
    if declining:
        logger.info(f"  Declining signals: {len(declining)} topics losing steam")
    else:
        logger.info("  No declining signals detected")

    # Movement assessment suggestion
    assessment = suggest_assessment(theme)
    logger.info(f"  Assessment: {assessment['assessment_name']} (matched: {assessment['matched_theme']})")

    # ────────────────────────────────────────────────────────
    # 6. GENERATE CONTENT STRATEGY
    # ────────────────────────────────────────────────────────
    logger.info("\n[6/9] Generating content strategy...")
    strategy = None
    strategy_source = "none"
    if ANTHROPIC_API_KEY:
        logger.info("  Using Claude API...")
        prompt = build_claude_prompt(
            analysis, emerging, prior_theme,
            TOPIC_SOLUTIONS, is_first_run,
            seasonal=seasonal,
            exercise_protocols=EXERCISE_PROTOCOLS,
        )
        prompt_tokens = len(prompt.split()) * 1.3  # rough estimate
        strategy = call_claude(prompt, ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS)
        if strategy:
            strategy_source = "claude_api"
            # Estimate cost: Sonnet input ~$3/MTok, output ~$15/MTok
            est_input_tokens = int(prompt_tokens)
            est_output_tokens = 2000  # typical playbook response
            est_cost = (est_input_tokens * 3 + est_output_tokens * 15) / 1_000_000
            logger.info(f"  Claude strategy generated (est. cost: ${est_cost:.3f})")
        else:
            logger.info("  Claude failed — falling back to template strategy")
            strategy = generate_fallback_strategy(analysis, TOPIC_SOLUTIONS)
            strategy_source = "fallback_template"
    else:
        logger.info("  No ANTHROPIC_API_KEY — using template strategy")
        strategy = generate_fallback_strategy(analysis, TOPIC_SOLUTIONS)
        strategy_source = "fallback_template"

    # ────────────────────────────────────────────────────────
    # 7. RENDER EMAIL
    # ────────────────────────────────────────────────────────
    logger.info("\n[7/9] Rendering email...")
    meta = {
        "brief_number": get_brief_number(),
        "date": datetime.now().strftime("%B %d, %Y"),
        "generated_at": datetime.now().strftime("%A, %B %d, %Y at %I:%M %p"),
        "is_first_run": is_first_run,
        "sources": [
            "Google Trends (US)" if not skip_google else None,
            "Reddit" if not skip_reddit else None,
            "Quora" if not skip_quora else None,
            "Wikipedia Pageviews" if not skip_wiki else None,
            "PubMed" if not skip_pubmed else None,
            "Google News RSS",
            "Hacker News",
        ],
    }
    meta["sources"] = [s for s in meta["sources"] if s]

    html = render_email(
        analysis, strategy, emerging, engagement_opps, meta,
        declining=declining, seasonal=seasonal, assessment=assessment,
    )

    # Save HTML for debugging / CI artifact
    save_html(html)
    logger.info(f"  Brief #{meta['brief_number']} rendered ({len(html):,} chars)")

    # ────────────────────────────────────────────────────────
    # 8. DELIVER
    # ────────────────────────────────────────────────────────
    logger.info("\n[8/9] Delivering...")

    # Save snapshot (includes all raw data for next week's diffing)
    snapshot_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "theme": theme,
        "google": google,
        "rising_queries": rising,
        "reddit": reddit,
        "quora": quora,
        "wikipedia": wikipedia,
        "pubmed": pubmed,
        "news": news,
        "leads": leads,
        "hn_leads": hn_leads,
        "emerging_signals": emerging,
        "declining_signals": declining,
        "seasonal_context": seasonal,
        "assessment": assessment,
        "strategy_json": strategy,
        "strategy_source": strategy_source,
    }
    save_snapshot(snapshot_data)

    if preview:
        logger.info("\n--- PREVIEW MODE --- (email not sent)")
        print(html)
    elif EMAIL_CONFIG.get("recipient"):
        send_email(html, EMAIL_CONFIG["recipient"], theme, EMAIL_CONFIG)
    else:
        logger.info("  No recipient configured. HTML saved to data/latest_brief.html")

    # ────────────────────────────────────────────────────────
    # 9. SUMMARY
    # ────────────────────────────────────────────────────────
    logger.info("\n[9/9] Summary")
    logger.info(f"  Theme: '{theme}'")
    logger.info(f"  Season: {seasonal['season_name']}")
    logger.info(f"  Assessment: {assessment['assessment_name']}")
    logger.info(f"  Strategy source: {strategy_source}")
    logger.info(f"  Emerging: {emerging.get('summary', 'none')}")
    if declining:
        logger.info(f"  Declining: {', '.join(d['keyword'] for d in declining[:3])}")
    logger.info(f"  Engagement opps: {len(engagement_opps)}")

    logger.info("\n" + "=" * 60)
    logger.info(f"  Done. Brief #{meta['brief_number']}: '{theme}'")
    logger.info("=" * 60)
    logger.info(f"  Run log saved: {log_file}")


if __name__ == "__main__":
    main()
