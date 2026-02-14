"""
FormCoach Trend Engine — Seasonal / Calendar Awareness
=======================================================
Maps calendar periods to seasonal context for pain/fitness content,
enabling the trend engine to weight topics and suggest angles that
align with what audiences are actually experiencing right now.
"""

from __future__ import annotations

import datetime
from typing import Any


# ─── Seasonal calendar: month-range -> context ───────────────────────
# Each entry covers one or more months and carries the contextual data
# the strategy layer can fold into prompts and angle selection.

SEASONAL_CALENDAR: dict[str, dict[str, Any]] = {
    "january": {
        "months": [1],
        "season_name": "New Year Resolution Rush",
        "context_note": (
            "Gym memberships spike and desk workers flood fitness classes. "
            "New Year 'new body' energy is high but injury risk rises as "
            "beginners push too hard too fast."
        ),
        "suggested_angles": [
            "Desk-to-gym transition: how to avoid the January injury spike",
            "New Year resolution-proof mobility routine",
            "Why your 'new year new body' plan needs a movement screen first",
        ],
        "trending_keywords_boost": [
            "new year fitness",
            "gym beginner pain",
            "new year new body",
            "desk to gym",
            "resolution workout",
            "beginner back pain",
        ],
    },
    "february": {
        "months": [2],
        "season_name": "Winter Stiffness & Stress",
        "context_note": (
            "Cold weather stiffness lingers, tax-season stress elevates "
            "tension patterns, and Valentine's Day creates interest in "
            "couple workouts and partner stretching."
        ),
        "suggested_angles": [
            "Valentine's partner stretching routine for couples",
            "Tax-season tension: where stress hides in your body",
            "Winter stiffness SOS — the 5-minute morning warm-up",
        ],
        "trending_keywords_boost": [
            "couple workout",
            "partner stretching",
            "winter stiffness",
            "stress tension neck",
            "tax season stress",
            "cold weather joint pain",
        ],
    },
    "march_april": {
        "months": [3, 4],
        "season_name": "Spring Activity Surge",
        "context_note": (
            "Warmer weather pulls people outdoors — running, gardening, "
            "and yard work spike. 'Summer body prep' motivation peaks and "
            "gardening injuries become surprisingly common."
        ),
        "suggested_angles": [
            "Summer body prep starts with mobility, not cardio",
            "Gardening injuries are real — protect your back this spring",
            "Spring running comeback: avoiding shin splints and knee pain",
        ],
        "trending_keywords_boost": [
            "summer body prep",
            "gardening back pain",
            "spring running",
            "outdoor exercise",
            "yard work injury",
            "shin splints",
        ],
    },
    "may": {
        "months": [5],
        "season_name": "Weekend Warrior Season",
        "context_note": (
            "Memorial Day weekend warriors emerge — people who've been "
            "sedentary jump into hiking, running, and outdoor sports. "
            "Overuse injuries and trail-related tweaks surge."
        ),
        "suggested_angles": [
            "Weekend warrior survival guide: don't let Memorial Day wreck your back",
            "Trail running season: ankles, knees, and what to strengthen first",
            "Hiking injury prevention — the pre-hike mobility check",
        ],
        "trending_keywords_boost": [
            "weekend warrior injury",
            "hiking knee pain",
            "outdoor running",
            "memorial day fitness",
            "trail running pain",
            "hiking injury",
        ],
    },
    "june_august": {
        "months": [6, 7, 8],
        "season_name": "Summer Activity Peak",
        "context_note": (
            "Peak outdoor activity season. Vacation travel introduces "
            "prolonged sitting in cars and planes, dehydration causes "
            "cramping, and overall activity volume is at its yearly high."
        ),
        "suggested_angles": [
            "Vacation travel pain: the airplane seat survival stretches",
            "Dehydration and cramping — the summer pain connection no one talks about",
            "Summer activity overload: when more exercise makes pain worse",
        ],
        "trending_keywords_boost": [
            "travel back pain",
            "airplane stretches",
            "dehydration cramps",
            "summer exercise",
            "vacation fitness",
            "road trip pain",
            "swimming shoulder pain",
        ],
    },
    "september": {
        "months": [9],
        "season_name": "RTO Wave",
        "context_note": (
            "Return-to-office mandates and back-to-school transitions put "
            "people back at desks full-time. Desk pain resurges after a "
            "summer of relative movement freedom."
        ),
        "suggested_angles": [
            "RTO survival: your desk is wrecking your summer gains",
            "Back-to-school back pain — it's not just the backpacks",
            "Desk pain resurgence: the September slump is real",
        ],
        "trending_keywords_boost": [
            "return to office pain",
            "desk pain",
            "back to school posture",
            "ergonomic setup",
            "office chair back pain",
            "RTO desk ergonomics",
        ],
    },
    "october": {
        "months": [10],
        "season_name": "Marathon Season Peak",
        "context_note": (
            "Major marathons (Chicago, NYC) drive peak running culture. "
            "Fall sports injuries from football, soccer, and weekend "
            "leagues add to the mix."
        ),
        "suggested_angles": [
            "Marathon recovery: what to do the week after race day",
            "Fall sports injury prevention for weekend league warriors",
            "Runner's knee season: why October is peak IT band flare-up time",
        ],
        "trending_keywords_boost": [
            "marathon recovery",
            "runner's knee",
            "IT band pain",
            "fall sports injury",
            "running pain",
            "post-marathon soreness",
        ],
    },
    "november_december": {
        "months": [11, 12],
        "season_name": "Holiday Stress & Travel",
        "context_note": (
            "Holiday travel means long drives and flights. Cold weather "
            "stiffness returns, holiday stress creates tension headaches "
            "and neck pain, and gift-guide angles open up for fitness "
            "and recovery products."
        ),
        "suggested_angles": [
            "Holiday travel pain survival kit — stretches for the car and plane",
            "Cold weather stiffness: why your joints hate December",
            "Gift guide angle: recovery tools that actually work",
        ],
        "trending_keywords_boost": [
            "holiday travel pain",
            "cold weather stiffness",
            "holiday stress tension",
            "gift guide fitness",
            "winter joint pain",
            "tension headache holiday",
            "foam roller gift",
        ],
    },
}


# ─── Internal: month -> seasonal key lookup ──────────────────────────

def _month_to_season_key(month: int) -> str:
    """Map a calendar month (1-12) to its SEASONAL_CALENDAR key.

    Args:
        month: Integer month (1 = January, 12 = December).

    Returns:
        The string key into ``SEASONAL_CALENDAR``.
    """
    for key, data in SEASONAL_CALENDAR.items():
        if month in data["months"]:
            return key
    # Defensive fallback — should never happen with complete calendar
    return "january"


# ═════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════


def get_seasonal_context(date: datetime.date | None = None) -> dict[str, Any]:
    """Return seasonal context for the given date (or today).

    Looks up the current month in ``SEASONAL_CALENDAR`` and returns a
    dict with the season name, a contextual insight note, suggested
    content angles, and keywords that historically spike during this
    period.

    Args:
        date: A ``datetime.date`` to evaluate. If ``None``, defaults to
            ``datetime.date.today()``.

    Returns:
        A dict with keys:

        - ``season_name`` (str): Human-readable season label,
          e.g. ``"RTO Wave"``.
        - ``context_note`` (str): 1-2 sentence seasonal insight for
          strategy prompts.
        - ``suggested_angles`` (list[str]): 2-3 content angles tied
          to the season.
        - ``trending_keywords_boost`` (list[str]): Keywords that
          historically spike this time of year.
        - ``month`` (int): The evaluated month.
        - ``date`` (str): ISO-formatted date string.

    Example::

        >>> ctx = get_seasonal_context(datetime.date(2025, 9, 15))
        >>> ctx["season_name"]
        'RTO Wave'
        >>> "desk pain" in ctx["trending_keywords_boost"]
        True
    """
    if date is None:
        date = datetime.date.today()

    key = _month_to_season_key(date.month)
    entry = SEASONAL_CALENDAR[key]

    return {
        "season_name": entry["season_name"],
        "context_note": entry["context_note"],
        "suggested_angles": list(entry["suggested_angles"]),
        "trending_keywords_boost": list(entry["trending_keywords_boost"]),
        "month": date.month,
        "date": date.isoformat(),
    }
