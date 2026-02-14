"""Jinja2-based email renderer for FormCoach Trend Engine briefs.

Loads templates from src/templates/ and renders the complete weekly
trend brief as a single HTML string suitable for email delivery.
All styling is inline (email clients strip <style> blocks).

Includes data normalization to bridge the gap between raw collector
output and the template-expected structures.
"""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def _build_env() -> Environment:
    """Create a Jinja2 environment configured for email HTML rendering."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


# ─── Data normalization helpers ─────────────────────────────────────


def _normalize_google_trends(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw Google Trends data into template-expected structure.

    Raw: analysis["google"] = {keyword: {current, prev_week, wow_pct, 4w_trend, 4w_avg}}
    Raw: analysis["rising_queries"] = {keyword: {rising: [...], top: [...]}}
    Template expects: analysis["google_trends"]["keywords"] = [{keyword, score, wow_pct, four_week_avg, rising_queries}]
    """
    google = analysis.get("google")
    rising = analysis.get("rising_queries")
    if not google:
        return {}

    keywords = []
    for kw, data in google.items():
        entry = {
            "keyword": kw,
            "score": data.get("current", 0),
            "wow_pct": data.get("wow_pct"),
            "four_week_avg": data.get("4w_avg", 0),
            "trend_direction": data.get("4w_trend", "stable"),
            "prev_week": data.get("prev_week", 0),
        }
        # Attach rising queries for this keyword
        if rising and kw in rising:
            kw_rising = rising[kw].get("rising", [])
            entry["rising_queries"] = [q.get("query", "") for q in kw_rising[:3]]
        else:
            entry["rising_queries"] = []
        keywords.append(entry)

    # Sort by wow_pct descending (None values go to end)
    keywords.sort(key=lambda x: x["wow_pct"] if x["wow_pct"] is not None else -999, reverse=True)

    return {"keywords": keywords}


def _normalize_reddit(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw Reddit data into template-expected structure.

    Raw: analysis["reddit"] = {subreddit: [post_dicts]}
    Template expects: analysis["reddit"]["posts"] = flat list of post dicts
    """
    reddit = analysis.get("reddit")
    if not reddit or not isinstance(reddit, dict):
        return {}

    posts = []
    subreddit_count = 0
    for subreddit, sub_posts in reddit.items():
        if not isinstance(sub_posts, list):
            continue
        subreddit_count += 1
        for post in sub_posts:
            if not isinstance(post, dict):
                continue
            posts.append({
                "title": post.get("title", ""),
                "url": post.get("url", post.get("permalink", "")),
                "score": post.get("score", 0),
                "num_comments": post.get("comments", post.get("num_comments", 0)),
                "subreddit": post.get("subreddit", subreddit),
                "is_new": post.get("is_new", True),
                "prior_score": post.get("prior_score"),
                "score_delta": post.get("score_delta"),
            })

    # Sort by score descending
    posts.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {"posts": posts[:20], "subreddit_count": subreddit_count}


def _normalize_quora(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw Quora data into template-expected structure.

    Raw: analysis["quora"] = [{question, url, source_query, fingerprint}]
    Template expects: analysis["quora"]["questions"] = [{title, url, query}]
    """
    quora = analysis.get("quora")
    if not quora or not isinstance(quora, list):
        return {}

    questions = []
    for item in quora:
        if not isinstance(item, dict):
            continue
        questions.append({
            "title": item.get("question", ""),
            "url": item.get("url", ""),
            "query": item.get("source_query", ""),
        })

    return {"questions": questions}


def _normalize_wikipedia(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw Wikipedia data into template-expected structure.

    Raw: analysis["wikipedia"] = {article: {current_week_avg, prior_week_avg, wow_pct, daily}}
    Template expects: analysis["wikipedia"]["pages"] = [{title, daily_views, wow_pct}]
    """
    wiki = analysis.get("wikipedia")
    if not wiki or not isinstance(wiki, dict):
        return {}

    pages = []
    for article, data in wiki.items():
        if not isinstance(data, dict):
            continue
        pages.append({
            "title": article.replace("_", " "),
            "daily_views": round(data.get("current_week_avg", 0)),
            "wow_pct": data.get("wow_pct"),
            "prior_avg": data.get("prior_week_avg", 0),
        })

    # Sort by wow_pct descending
    pages.sort(key=lambda x: x["wow_pct"] if x["wow_pct"] is not None else -999, reverse=True)

    return {"pages": pages}


def _normalize_pubmed(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw PubMed data into template-expected structure.

    Raw: analysis["pubmed"] = [{title, journal, date, pmid}]
    Template expects: analysis["pubmed"]["studies"] = [{title, journal, date, url}]
    """
    pubmed = analysis.get("pubmed")
    if not pubmed or not isinstance(pubmed, list):
        return {}

    studies = []
    for item in pubmed:
        if not isinstance(item, dict):
            continue
        pmid = item.get("pmid", "")
        studies.append({
            "title": item.get("title", ""),
            "journal": item.get("journal", ""),
            "date": item.get("date", ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        })

    return {"studies": studies}


def _normalize_news(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw news data into template-expected structure.

    Raw: analysis["news"] = [{title, source, url, date}]
    Template expects: analysis["news"]["headlines"] = [{title, source, url, date}]
    """
    news = analysis.get("news")
    if not news or not isinstance(news, list):
        return {}

    return {"headlines": news}


def _normalize_leads(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize leads for template."""
    leads = analysis.get("leads")
    if not leads or not isinstance(leads, list):
        return []
    return leads


def _normalize_strategy(strategy: Dict[str, Any], theme: str) -> Dict[str, Any]:
    """Remap strategy keys from Claude/fallback output to template-expected keys.

    Claude/fallback returns: monday_video, wednesday_post, friday_card
    Templates expect: monday, wednesday, friday with different sub-keys.
    """
    if not strategy:
        return {}

    result = {
        "theme_name": theme,
        "theme_narrative": strategy.get("theme_narrative", ""),
    }

    # Monday video
    monday_raw = strategy.get("monday_video", strategy.get("monday", {}))
    if monday_raw and isinstance(monday_raw, dict):
        exercises = monday_raw.get("exercises", [])
        # Exercises could be list of dicts or list of strings
        exercise_list = []
        exercise_details = []
        for ex in exercises:
            if isinstance(ex, dict):
                name = ex.get("name", "")
                cue = ex.get("form_cue", "")
                sets = ex.get("sets", "")
                contra = ex.get("contraindication", "")
                progression = ex.get("progression", "")
                regression = ex.get("regression", "")
                # Build display string
                parts = [name]
                if sets:
                    parts.append(f"({sets})")
                if cue and cue != sets:
                    parts.append(f"— {cue}")
                exercise_list.append(" ".join(parts))
                # Store rich detail for template
                if sets or contra:
                    exercise_details.append({
                        "name": name,
                        "sets": sets,
                        "contraindication": contra,
                        "progression": progression,
                        "regression": regression,
                    })
            else:
                exercise_list.append(str(ex))

        # Normalize platform keys: instagram_reels -> instagram
        platforms = dict(monday_raw.get("platforms", {}))
        if "instagram_reels" in platforms and "instagram" not in platforms:
            platforms["instagram"] = platforms.pop("instagram_reels")

        result["monday"] = {
            "video_title": monday_raw.get("title", monday_raw.get("video_title", "")),
            "hook": monday_raw.get("hook", ""),
            "talking_points": monday_raw.get("talking_points", []),
            "exercises": exercise_list,
            "exercise_details": exercise_details,
            "cta": monday_raw.get("end_cta", monday_raw.get("cta", "")),
            "platforms": platforms,
            "thumbnail": monday_raw.get("thumbnail", {}),
            "viewer_assessment": monday_raw.get("viewer_assessment", ""),
        }

    # Wednesday post
    wed_raw = strategy.get("wednesday_post", strategy.get("wednesday", {}))
    if wed_raw and isinstance(wed_raw, dict):
        result["wednesday"] = {
            "linkedin_post": wed_raw.get("linkedin_draft", wed_raw.get("linkedin_post", "")),
            "blog_title": wed_raw.get("blog_title", ""),
            "seo_target": wed_raw.get("blog_meta_description", wed_raw.get("seo_target", "")),
            "medium_subtitle": wed_raw.get("medium_subtitle", ""),
            "cross_post": wed_raw.get("cross_post_note", wed_raw.get("cross_post", "")),
            "study_citation": wed_raw.get("study_citation", ""),
        }

    # Friday card
    fri_raw = strategy.get("friday_card", strategy.get("friday", {}))
    if fri_raw and isinstance(fri_raw, dict):
        result["friday"] = {
            "stat_line": fri_raw.get("stat_headline", fri_raw.get("stat_line", "")),
            "tip": fri_raw.get("tip", ""),
            "engagement_ask": fri_raw.get("engagement_ask", ""),
            "platforms": fri_raw.get("platforms", {}),
        }

    # SEO notes
    seo_raw = strategy.get("seo_notes", {})
    if seo_raw and isinstance(seo_raw, dict):
        result["seo_notes"] = {
            "target_keyword": seo_raw.get("target_keyword", ""),
            "secondary_keywords": seo_raw.get("secondary_keywords", []),
            "schema_markup": ", ".join(seo_raw.get("schema_types", [])) if isinstance(seo_raw.get("schema_types"), list) else seo_raw.get("schema_markup", ""),
            "ai_tips": seo_raw.get("ai_findability_tips", seo_raw.get("ai_tips", [])),
        }

    # Engagement reply drafts
    replies = strategy.get("engagement_replies", [])
    if replies and isinstance(replies, list):
        result["engagement_replies"] = replies

    return result


def _build_executive_summary(
    strategy: Dict[str, Any],
    engagement_opps: List[Dict[str, Any]],
    emerging: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a Top 3 Actions executive summary for the email header."""
    actions = []

    # Action 1: Monday video
    monday = strategy.get("monday_video", strategy.get("monday", {}))
    if monday and isinstance(monday, dict):
        title = monday.get("title", monday.get("video_title", "this week's theme"))
        actions.append({
            "priority": 1,
            "action": f"Record video: {title}",
            "time_est": "45 min",
            "day": "Monday",
        })

    # Action 2: Best engagement opportunity
    if engagement_opps:
        top_opp = engagement_opps[0]
        opp_title = top_opp.get("title", "")[:60]
        opp_sub = top_opp.get("subreddit", "")
        source = f"r/{opp_sub}" if opp_sub else top_opp.get("platform", "")
        actions.append({
            "priority": 2,
            "action": f"Reply to: \"{opp_title}\" on {source}",
            "time_est": "5 min",
            "day": "Anytime",
        })

    # Action 3: Emerging signal to cover
    new_queries = emerging.get("new_rising_queries", [])
    new_reddit = emerging.get("new_reddit_topics", [])
    if new_queries:
        q = new_queries[0]
        query_text = q.get("query", str(q)) if isinstance(q, dict) else str(q)
        actions.append({
            "priority": 3,
            "action": f"New rising query: \"{query_text}\" — be first to cover this",
            "time_est": "Flag for next week",
            "day": "Note",
        })
    elif new_reddit:
        r = new_reddit[0]
        title = r.get("title", "")[:60] if isinstance(r, dict) else str(r)[:60]
        actions.append({
            "priority": 3,
            "action": f"New Reddit conversation: \"{title}\"",
            "time_est": "Flag for content",
            "day": "Note",
        })

    return {"actions": actions}


def _normalize_emerging(emerging: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize emerging signals keys for template consumption."""
    if not emerging:
        return {}

    result = dict(emerging)

    # Fix Wikipedia breakouts: template expects .title and .daily_views
    breakouts = result.get("wikipedia_breakouts", [])
    for b in breakouts:
        if "article" in b and "title" not in b:
            b["title"] = b["article"].replace("_", " ")
        if "current_avg" in b and "daily_views" not in b:
            b["daily_views"] = round(b["current_avg"])

    # Fix Reddit topics: template expects .new_terms but code has .novel_terms
    topics = result.get("new_reddit_topics", [])
    for t in topics:
        if "novel_terms" in t and "new_terms" not in t:
            t["new_terms"] = t["novel_terms"]

    # Fix Quora questions: template expects .title but code has .question
    questions = result.get("new_quora_questions", [])
    for q in questions:
        if "question" in q and "title" not in q:
            q["title"] = q["question"]

    return result


# ─── Public API ─────────────────────────────────────────────────────


def _text_sparkline(values: List) -> str:
    """Convert a list of numeric values into a Unicode text sparkline.

    Uses block characters to show visual trajectory over 4 data points.
    Returns an empty string if values are insufficient.
    """
    if not values or len(values) < 2:
        return ""
    blocks = " ▁▂▃▄▅▆▇█"
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return ""
    lo, hi = min(nums), max(nums)
    spread = hi - lo if hi != lo else 1
    return "".join(blocks[min(8, int((v - lo) / spread * 8))] for v in nums)


def render_email(
    analysis: Dict[str, Any],
    strategy: Dict[str, Any],
    emerging: Dict[str, Any],
    engagement_opps: List[Dict[str, Any]],
    meta: Dict[str, Any],
    declining: List[Dict[str, Any]] | None = None,
    seasonal: Dict[str, Any] | None = None,
    assessment: Dict[str, Any] | None = None,
) -> str:
    """Render the full weekly trend brief as HTML.

    Normalizes all data structures before passing to Jinja2 templates
    to bridge the gap between raw collector output and template expectations.

    Parameters
    ----------
    analysis : dict
        Combined analysis data from build_analysis().
    strategy : dict
        Content strategy generated by Claude or the fallback template.
    emerging : dict
        Emerging signals from detect_emerging_signals().
    engagement_opps : list[dict]
        Ranked list of engagement opportunity dicts.
    meta : dict
        Brief metadata: brief_number, date, generated_at, is_first_run, sources.
    declining : list[dict], optional
        Declining signal dicts from detect_declining_signals().
    seasonal : dict, optional
        Seasonal context from get_seasonal_context().
    assessment : dict, optional
        Movement assessment suggestion from suggest_assessment().

    Returns
    -------
    str
        Fully rendered HTML string ready for email delivery.
    """
    analysis = analysis or {}
    strategy = strategy or {}
    emerging = emerging or {}

    # Normalize data structures for templates
    theme = analysis.get("theme", strategy.get("theme_name", ""))
    normalized_analysis = {
        "google_trends": _normalize_google_trends(analysis),
        "reddit": _normalize_reddit(analysis),
        "quora": _normalize_quora(analysis),
        "wikipedia": _normalize_wikipedia(analysis),
        "pubmed": _normalize_pubmed(analysis),
        "news": _normalize_news(analysis),
        "local_leads": _normalize_leads(analysis),
        "hn_leads": analysis.get("hn_leads") or [],
        "body_part_groups": analysis.get("body_part_groups") or [],
    }
    normalized_strategy = _normalize_strategy(strategy, theme)
    normalized_emerging = _normalize_emerging(emerging)
    executive_summary = _build_executive_summary(
        strategy, engagement_opps or [], emerging,
    )

    env = _build_env()
    env.globals["sparkline"] = _text_sparkline
    template = env.get_template("base.html.j2")
    return template.render(
        analysis=normalized_analysis,
        strategy=normalized_strategy,
        emerging=normalized_emerging,
        engagement_opps=engagement_opps or [],
        executive_summary=executive_summary,
        declining=declining or [],
        seasonal=seasonal or {},
        assessment=assessment or {},
        meta=meta or {},
    )
