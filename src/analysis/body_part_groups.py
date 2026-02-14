"""
FormCoach Trend Engine V2.0 — Body-Part Grouping & Composite Scoring
=====================================================================
Groups keywords by anatomical region (or modality) so related signals
are aggregated.  Uses a composite score that balances *volume* (how
many people are searching) with *momentum* (week-over-week change)
and *stability* (4-week average).

This prevents low-volume spikes (3 -> 10 = +233%) from outranking
high-volume steady topics (1000 -> 1020 = +2%).
"""

from __future__ import annotations

import math
from typing import Any


# ═══════════════════════════════════════════════════════════════════
# BODY-PART / MODALITY REGISTRY
# ═══════════════════════════════════════════════════════════════════
# Each group maps to: keywords it absorbs, related wiki articles,
# subreddit hints, and exercise keys for TOPIC_SOLUTIONS lookup.

BODY_PART_REGISTRY: dict[str, dict[str, Any]] = {
    "neck": {
        "label": "Neck & Cervical Spine",
        "keywords": [
            "neck pain", "stiff neck", "text neck",
            "forward head posture",
        ],
        "wiki_articles": ["Tension_headache"],
        "exercise_keys": ["neck pain", "text neck", "forward head posture"],
    },
    "upper_back": {
        "label": "Upper Back & Thoracic",
        "keywords": [
            "upper back pain", "thoracic outlet syndrome",
        ],
        "wiki_articles": [
            "Kyphosis", "Thoracic_outlet_syndrome",
        ],
        "exercise_keys": ["upper back pain", "thoracic outlet", "thoracic outlet syndrome"],
    },
    "lower_back": {
        "label": "Lower Back & Lumbar Spine",
        "keywords": [
            "lower back pain", "sciatica", "herniated disc",
            "yoga for back pain", "yoga for sciatica",
            "driving back pain",
        ],
        "wiki_articles": [
            "Low_back_pain", "Sciatica", "Spinal_disc_herniation",
            "Spinal_stenosis", "Scoliosis",
        ],
        "exercise_keys": [
            "lower back pain", "sciatica", "back pain",
            "yoga for back pain", "yoga for sciatica",
        ],
    },
    "hip_pelvis": {
        "label": "Hip & Pelvis",
        "keywords": [
            "hip pain", "anterior pelvic tilt", "hip flexor pain",
            "hip flexor running", "piriformis syndrome",
        ],
        "wiki_articles": [
            "Piriformis_syndrome", "Sacroiliac_joint_dysfunction",
            "Anterior_pelvic_tilt",
        ],
        "exercise_keys": [
            "hip pain", "anterior pelvic tilt", "piriformis",
            "piriformis syndrome", "hip flexor running",
        ],
    },
    "shoulder": {
        "label": "Shoulder",
        "keywords": ["shoulder pain"],
        "wiki_articles": ["Rotator_cuff_tear"],
        "exercise_keys": ["shoulder pain"],
    },
    "knee": {
        "label": "Knee",
        "keywords": [
            "knee pain", "runner's knee",
        ],
        "wiki_articles": ["Patellofemoral_pain_syndrome"],
        "exercise_keys": ["knee pain", "runner's knee"],
    },
    "foot_ankle": {
        "label": "Foot & Ankle",
        "keywords": [
            "plantar fasciitis", "plantar fasciitis running",
            "achilles tendonitis",
        ],
        "wiki_articles": [
            "Plantar_fasciitis", "Achilles_tendinitis",
        ],
        "exercise_keys": [
            "plantar fasciitis", "plantar fasciitis running",
            "achilles tendonitis",
        ],
    },
    "hand_wrist": {
        "label": "Hand & Wrist",
        "keywords": ["carpal tunnel"],
        "wiki_articles": ["Carpal_tunnel_syndrome"],
        "exercise_keys": ["carpal tunnel"],
    },
    "head_jaw": {
        "label": "Head & Jaw",
        "keywords": ["tension headache"],
        "wiki_articles": ["Tension_headache", "Myofascial_pain_syndrome"],
        "exercise_keys": ["tension headache"],
    },
    # ── Non-anatomical modality groups ──────────────────────────
    "posture_ergonomics": {
        "label": "Posture & Ergonomics",
        "keywords": [
            "posture", "posture correction", "office ergonomics",
            "standing desk", "working from home", "squat form",
            "deadlift form", "aging posture",
        ],
        "wiki_articles": ["Posture", "Ergonomics", "Lordosis"],
        "exercise_keys": [
            "posture", "office ergonomics", "standing desk",
        ],
    },
    "yoga_therapy": {
        "label": "Yoga Therapy",
        "keywords": [
            "therapeutic yoga", "yoga for chronic pain",
            "restorative yoga", "yin yoga for pain",
        ],
        "wiki_articles": ["Yoga_therapy", "Yoga_as_exercise"],
        "exercise_keys": [
            "therapeutic yoga", "yoga for chronic pain",
            "restorative yoga",
        ],
    },
    "running_recovery": {
        "label": "Running Recovery",
        "keywords": [
            "IT band syndrome", "marathon recovery",
        ],
        "wiki_articles": ["Iliotibial_band_syndrome"],
        "exercise_keys": [
            "IT band syndrome", "marathon recovery",
        ],
    },
    "longevity": {
        "label": "Longevity & Functional Aging",
        "keywords": [
            "longevity exercises", "mobility for aging",
            "functional fitness over 40", "joint health",
            "movement longevity",
        ],
        "wiki_articles": ["Blue_zone", "Longevity"],
        "exercise_keys": [
            "longevity exercises", "mobility for aging",
            "functional fitness over 40", "joint health",
            "movement longevity",
        ],
    },
    "cancer_exercise": {
        "label": "Cancer Exercise",
        "keywords": [
            "exercise during chemotherapy", "cancer rehabilitation",
            "exercise after cancer treatment", "cancer fatigue exercise",
            "oncology exercise", "cancer pain",
        ],
        "wiki_articles": ["Cancer-related_fatigue", "Exercise_and_cancer"],
        "exercise_keys": [
            "exercise during chemotherapy", "cancer rehabilitation",
            "exercise after cancer treatment", "cancer fatigue exercise",
            "oncology exercise", "cancer pain",
        ],
    },
    "chronic_conditions": {
        "label": "Chronic Conditions",
        "keywords": [
            "fibromyalgia", "chronic pain syndrome",
            "degenerative disc disease",
        ],
        "wiki_articles": [
            "Chronic_pain", "Fibromyalgia",
        ],
        "exercise_keys": ["fibromyalgia"],
    },
    "general_modalities": {
        "label": "General Exercise Modalities",
        "keywords": [
            "corrective exercise", "foam rolling",
            "mobility exercises", "work injury",
        ],
        "wiki_articles": ["Physical_therapy"],
        "exercise_keys": [
            "corrective exercise", "foam rolling", "mobility exercises",
        ],
    },
}

# ── Build reverse lookup: keyword -> group key ─────────────────
_KEYWORD_TO_GROUP: dict[str, str] = {}
for _group_key, _group_data in BODY_PART_REGISTRY.items():
    for _kw in _group_data["keywords"]:
        _KEYWORD_TO_GROUP[_kw.lower()] = _group_key


# ═══════════════════════════════════════════════════════════════════
# COMPOSITE SCORING
# ═══════════════════════════════════════════════════════════════════


def compute_composite_score(
    current: float | int,
    wow_pct: float | None,
    four_w_avg: float | int = 0,
) -> float:
    """Compute a volume-weighted composite trend score for a keyword.

    Formula weights:
        volume   (0.45): log(current + 1) / log(101)
        momentum (0.35): tanh(wow_pct / 100) — clamps wild swings
        stability(0.20): log(4w_avg + 1) / log(101)

    All components are normalized to roughly [0, 1].

    Parameters
    ----------
    current : float | int
        Current Google Trends score (0-100, batch-normalized).
    wow_pct : float | None
        Week-over-week percentage change. ``None`` treated as 0.
    four_w_avg : float | int
        Four-week rolling average score.

    Returns
    -------
    float
        Composite score, typically in [0, 1].
    """
    log101 = math.log(101)  # ~4.615

    vol = math.log(max(float(current), 0) + 1) / log101
    mom = math.tanh((float(wow_pct) if wow_pct is not None else 0.0) / 100.0)
    # Shift momentum from [-1, 1] to [0, 1] so declining = 0, neutral = 0.5
    mom_norm = (mom + 1.0) / 2.0
    stab = math.log(max(float(four_w_avg), 0) + 1) / log101

    return round(0.45 * vol + 0.35 * mom_norm + 0.20 * stab, 4)


# ═══════════════════════════════════════════════════════════════════
# GROUPING & AGGREGATION
# ═══════════════════════════════════════════════════════════════════


def get_body_part_for_keyword(keyword: str) -> str | None:
    """Return the body-part/modality group key for a keyword.

    Case-insensitive lookup.

    Returns ``None`` if the keyword is not in any registered group.
    """
    return _KEYWORD_TO_GROUP.get(keyword.lower())


def group_keywords_by_body_part(
    google: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Group Google Trends keywords by body part and compute group scores.

    Each keyword is scored with :func:`compute_composite_score`. Keywords
    are assigned to their body-part group via the registry. Ungrouped
    keywords fall into an ``"other"`` bucket.

    Group composite = max(members) * 0.6 + mean(members) * 0.4

    Parameters
    ----------
    google : dict | None
        Raw Google Trends data: ``{keyword: {current, wow_pct, 4w_avg, ...}}``.

    Returns
    -------
    list[dict]
        Sorted list (highest group_composite first) of dicts, each with:
        ``group_key``, ``label``, ``group_composite``, ``lead_keyword``,
        ``members`` (list of keyword detail dicts).
    """
    if not google:
        return []

    # Score each keyword and assign to a group
    group_members: dict[str, list[dict[str, Any]]] = {}

    for keyword, data in google.items():
        if not isinstance(data, dict):
            continue

        current = data.get("current", 0)
        wow_pct = data.get("wow_pct")
        four_w_avg = data.get("4w_avg", 0)

        composite = compute_composite_score(current, wow_pct, four_w_avg)
        group_key = get_body_part_for_keyword(keyword) or "other"

        member = {
            "keyword": keyword,
            "current": current,
            "wow_pct": wow_pct,
            "four_w_avg": four_w_avg,
            "composite": composite,
            "prev_week": data.get("prev_week", 0),
            "trend_direction": data.get("4w_trend", "stable"),
        }

        if group_key not in group_members:
            group_members[group_key] = []
        group_members[group_key].append(member)

    # Build group-level aggregates
    groups: list[dict[str, Any]] = []

    for group_key, members in group_members.items():
        scores = [m["composite"] for m in members]
        max_score = max(scores)
        mean_score = sum(scores) / len(scores)
        group_composite = round(max_score * 0.6 + mean_score * 0.4, 4)

        # Sort members within group by composite descending
        members.sort(key=lambda m: m["composite"], reverse=True)
        lead = members[0]

        registry_entry = BODY_PART_REGISTRY.get(group_key)
        label = registry_entry["label"] if registry_entry else "Other / Ungrouped"

        groups.append({
            "group_key": group_key,
            "label": label,
            "group_composite": group_composite,
            "lead_keyword": lead["keyword"],
            "lead_composite": lead["composite"],
            "lead_wow_pct": lead["wow_pct"],
            "lead_current": lead["current"],
            "member_count": len(members),
            "members": members,
        })

    # Sort groups by group_composite descending
    groups.sort(key=lambda g: g["group_composite"], reverse=True)
    return groups


def get_exercises_for_body_part(
    group_key: str,
    topic_solutions: dict[str, list],
) -> list[str]:
    """Collect all exercises relevant to a body-part group.

    Looks up each ``exercise_key`` from the registry in ``topic_solutions``
    and returns a deduplicated ordered list of exercise names.

    Parameters
    ----------
    group_key : str
        A key from :data:`BODY_PART_REGISTRY`.
    topic_solutions : dict
        The ``TOPIC_SOLUTIONS`` mapping from config.

    Returns
    -------
    list[str]
        Deduplicated exercise names, preserving insertion order.
    """
    registry_entry = BODY_PART_REGISTRY.get(group_key)
    if not registry_entry:
        return []

    seen: set[str] = set()
    exercises: list[str] = []

    for key in registry_entry.get("exercise_keys", []):
        for ex in topic_solutions.get(key, []):
            name = ex if isinstance(ex, str) else ex.get("name", str(ex))
            if name not in seen:
                seen.add(name)
                exercises.append(name)

    return exercises


def select_theme_from_groups(
    groups: list[dict[str, Any]],
    prior_theme: str | None,
) -> str:
    """Pick the best theme from ranked body-part groups.

    Returns the ``lead_keyword`` of the top-scoring group. If that
    matches ``prior_theme``, the second group's lead is returned
    (for variety). Falls back to ``"General Pain Management"``.

    Parameters
    ----------
    groups : list[dict]
        Output of :func:`group_keywords_by_body_part`, already sorted
        by ``group_composite`` descending.
    prior_theme : str | None
        Last week's theme string, or ``None``.

    Returns
    -------
    str
        The selected theme keyword.
    """
    if not groups:
        return "General Pain Management"

    candidate = groups[0]["lead_keyword"]
    if candidate == prior_theme and len(groups) > 1:
        return groups[1]["lead_keyword"]
    return candidate
