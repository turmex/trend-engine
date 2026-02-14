"""
YouTube competitor intelligence collector for Trend Engine V2.0.

Monitors top creators in pain management, yoga, running, longevity,
and fitness spaces. Scrapes YouTube channel pages for recent video
data — no API key required, zero cost.

Optionally extracts transcripts via youtube-transcript-api (also free).
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

# Try to import transcript API (optional — graceful fallback)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _HAS_TRANSCRIPT_API = True
except ImportError:
    _HAS_TRANSCRIPT_API = False

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_relative_date(text: str) -> int | None:
    """Parse YouTube's relative date (e.g. '3 days ago') into days.

    Returns None if unparseable.
    """
    text = text.lower().strip()
    match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", text)
    if not match:
        # Handle "Streamed X days ago"
        match = re.match(r"streamed\s+(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", text)
    if not match:
        return None

    num = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "second": 0, "minute": 0, "hour": 0,
        "day": 1, "week": 7, "month": 30, "year": 365,
    }
    return num * multipliers.get(unit, 1)


def _fetch_channel_videos(
    handle: str,
    max_videos: int = 10,
) -> list[dict[str, Any]]:
    """Fetch recent videos from a YouTube channel by scraping the page.

    Args:
        handle: YouTube channel handle (e.g. '@bobandbrad').
        max_videos: Maximum number of videos to return.

    Returns:
        List of video dicts with title, video_id, published_text, days_ago.
    """
    url = f"https://www.youtube.com/{handle}/videos"

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
    except requests.RequestException:
        return []

    # YouTube embeds video data in ytInitialData JSON
    match = re.search(r"var ytInitialData = ({.*?});", resp.text)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    videos: list[dict[str, Any]] = []

    # Navigate to the video grid
    tabs = (data.get("contents", {})
            .get("twoColumnBrowseResultsRenderer", {})
            .get("tabs", []))

    for tab in tabs:
        tab_content = tab.get("tabRenderer", {}).get("content", {})
        rich_grid = tab_content.get("richGridRenderer", {})
        if not rich_grid:
            continue

        items = rich_grid.get("contents", [])[:max_videos]
        for item in items:
            video = (item.get("richItemRenderer", {})
                     .get("content", {})
                     .get("videoRenderer", {}))
            if not video:
                continue

            title_runs = video.get("title", {}).get("runs", [])
            title = title_runs[0].get("text", "") if title_runs else ""
            vid_id = video.get("videoId", "")
            published_text = (video.get("publishedTimeText", {})
                              .get("simpleText", ""))
            days_ago = _parse_relative_date(published_text)
            view_text = (video.get("viewCountText", {})
                         .get("simpleText", ""))

            videos.append({
                "title": title,
                "video_id": vid_id,
                "published_text": published_text,
                "days_ago": days_ago,
                "views_text": view_text,
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

        break  # Only process the videos tab

    return videos


def _get_transcript_keywords(video_id: str, max_chars: int = 3000) -> str | None:
    """Fetch transcript text for a video (first ~3000 chars).

    Returns None if transcripts are unavailable or the library isn't installed.
    """
    if not _HAS_TRANSCRIPT_API:
        return None

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en"]
        )
        full_text = " ".join(entry["text"] for entry in transcript_list)
        return full_text[:max_chars]
    except Exception:
        return None


def _match_keywords(text: str, keywords: set[str]) -> list[str]:
    """Find which keywords appear in text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


# Keywords to match against video titles and transcripts
_RELEVANCE_KEYWORDS = {
    # Pain conditions
    "back pain", "neck pain", "sciatica", "shoulder pain", "knee pain",
    "hip pain", "chronic pain", "herniated disc", "plantar fasciitis",
    "carpal tunnel", "arthritis", "fibromyalgia", "tendonitis",
    "piriformis", "stenosis", "radiculopathy", "bursitis",
    "impingement", "numbness", "tingling",

    # Treatment & exercise
    "stretch", "mobility", "posture", "ergonomic", "physical therapy",
    "foam roll", "corrective exercise", "rehab", "recovery",
    "pain relief", "flexibility", "warm up",

    # Yoga
    "yoga for pain", "yoga for back", "yoga therapy", "yin yoga",
    "restorative yoga",

    # Running
    "running injury", "runner's knee", "it band", "shin splint",
    "marathon recovery", "running form", "achilles",

    # Longevity
    "longevity", "aging", "functional fitness", "mobility drill",

    # Cancer exercise
    "cancer exercise", "chemotherapy", "oncology exercise",
    "cancer fatigue", "cancer rehab",
}


def collect_competitor_videos(
    channels: dict[str, dict[str, str]],
    days_back: int = 7,
    fetch_transcripts: bool = True,
    max_transcript_videos: int = 5,
) -> dict[str, Any] | None:
    """Collect recent videos from tracked competitor YouTube channels.

    Scrapes YouTube channel pages — no API key needed, zero cost.

    Args:
        channels: Dict mapping channel names to their config:
            {"Bob & Brad": {"handle": "@bobandbrad", "category": "physical_therapy"}}
        days_back: Only include videos from the last N days.
        fetch_transcripts: Whether to attempt transcript extraction.
        max_transcript_videos: Max videos to fetch transcripts for (slow).

    Returns:
        A dict with competitor intel, or None if collection fails.
    """
    if not channels:
        print("[Competitors] No channels configured.")
        return None

    all_videos: list[dict[str, Any]] = []
    channels_with_content = 0
    transcript_count = 0

    for channel_name, config in channels.items():
        handle = config.get("handle", "")
        category = config.get("category", "general")

        if not handle:
            continue

        print(f"[Competitors] Checking {channel_name}...")

        raw_videos = _fetch_channel_videos(handle)

        channel_videos = 0
        for rv in raw_videos:
            # Filter by recency
            days_ago = rv.get("days_ago")
            if days_ago is not None and days_ago > days_back:
                continue

            title = rv.get("title", "")
            url = rv.get("url", "")
            video_id = rv.get("video_id", "")

            # Check title for keyword matches
            title_matches = _match_keywords(title, _RELEVANCE_KEYWORDS)

            video: dict[str, Any] = {
                "channel": channel_name,
                "category": category,
                "title": title,
                "url": url,
                "published": rv.get("published_text", ""),
                "views": rv.get("views_text", ""),
                "matched_keywords": title_matches,
                "transcript_snippet": None,
                "transcript_keywords": None,
            }

            # Fetch transcript for relevant videos (limited to save time)
            if (fetch_transcripts and video_id and title_matches
                    and transcript_count < max_transcript_videos):
                transcript = _get_transcript_keywords(video_id)
                if transcript:
                    video["transcript_snippet"] = transcript[:500]
                    video["transcript_keywords"] = _match_keywords(
                        transcript, _RELEVANCE_KEYWORDS
                    )
                    transcript_count += 1

            all_videos.append(video)
            channel_videos += 1

        if channel_videos > 0:
            channels_with_content += 1

        # Small delay between channels to be polite
        time.sleep(0.5)

    if not all_videos:
        print("[Competitors] No recent videos found.")
        return None

    # Separate relevant videos (title keyword match)
    relevant = [v for v in all_videos if v["matched_keywords"]]

    # Count topic frequencies across all videos
    topic_counts: dict[str, int] = {}
    for v in all_videos:
        for kw in v["matched_keywords"]:
            topic_counts[kw] = topic_counts.get(kw, 0) + 1
    top_topics = sorted(topic_counts, key=topic_counts.get, reverse=True)[:10]

    # Group by category
    by_category: dict[str, list[dict[str, Any]]] = {}
    for v in all_videos:
        cat = v["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(v)

    result = {
        "videos": all_videos,
        "summary": {
            "total_channels_checked": len(channels),
            "channels_with_new_content": channels_with_content,
            "total_new_videos": len(all_videos),
            "relevant_videos": len(relevant),
            "top_topics": top_topics,
        },
        "by_category": by_category,
    }

    print(f"[Competitors] Found {len(all_videos)} new videos from "
          f"{channels_with_content} channels ({len(relevant)} relevant).")
    if top_topics:
        print(f"[Competitors] Hot topics: {', '.join(top_topics[:5])}")

    return result
