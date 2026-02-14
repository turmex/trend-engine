"""Reddit post relevance filtering for Trend Engine.

Scores each post against health/pain/fitness relevance keywords
and drops posts below threshold. This prevents irrelevant posts
(gaming, politics, memes, career rants) from cluttering the brief.
"""

from __future__ import annotations
from typing import Any


# Keywords that indicate a post IS relevant to pain management / fitness coaching
_POSITIVE_KEYWORDS = {
    # Pain & conditions
    "pain", "ache", "sore", "stiff", "tight", "numb", "tingling",
    "inflammation", "flare", "chronic", "acute", "injury", "injured",
    "herniat", "bulge", "pinch", "impinge", "tear", "strain", "sprain",
    "sciatica", "radiculopathy", "stenosis", "arthritis", "tendonitis",
    "tendinitis", "bursitis", "fasciitis", "fibromyalgia", "dysfunction",
    "discomfort", "weakness", "instability", "clicking", "popping",
    "grinding", "swelling", "burning",

    # Anatomy
    "back", "neck", "shoulder", "hip", "knee", "ankle", "wrist",
    "spine", "disc", "vertebra", "joint", "nerve", "muscle", "tendon",
    "ligament", "rotator", "pelvic", "lumbar", "cervical", "thoracic",
    "hamstring", "quad", "glute", "piriformis", "psoas", "flexor",
    "elbow", "calf", "achilles", "forearm", "trap",

    # Form & biomechanics — critical for fitness sub filtering
    "form check", "form breakdown", "bad form", "proper form",
    "technique", "biomechanic", "movement pattern", "compensation",
    "imbalance", "asymmetr", "dysfunction", "overuse",
    "deadlift form", "squat form", "bench form", "press form",
    "rounding", "butt wink", "knee cave", "valgus",
    "warm up", "cool down", "prehab", "accessory",

    # Treatment & exercise
    "stretch", "exercise", "mobility", "flexibility", "strengthen",
    "rehab", "recovery", "therapy", "physical therapy", "pt",
    "foam roll", "massage", "trigger point", "release", "corrective",
    "yoga", "pilates", "movement", "posture", "ergonomic", "alignment",
    "decompression", "traction", "brace", "support",

    # Modalities
    "chiropract", "orthoped", "surgeon", "mri", "x-ray", "xray",
    "diagnosis", "treatment", "heal", "relief", "improve",
    "success story", "what helped", "fixed", "cured",

    # Running / sports injury
    "running form", "gait", "overuse", "runner", "marathon",
    "it band", "shin splint", "plantar", "stride",

    # Golf / cycling / CrossFit injury angles
    "golf swing", "golf back", "golf shoulder", "bike fit",
    "saddle sore", "handlebar", "wod injury", "box jump",
    "kipping", "snatch form", "clean form",

    # Cancer exercise
    "cancer", "chemo", "oncolog", "survivor", "fatigue",

    # Longevity
    "longevity", "aging", "functional", "mobility drill",
}

# Keywords that indicate a post is NOT relevant (strong negative signal)
_NEGATIVE_KEYWORDS = {
    "meme", "shitpost", "rant wednesday", "gym story saturday",
    "victory sunday", "daily thread", "weekly thread",
    "selfie", "progress pic", "physique", "dating", "nsfw", "political",
    "super bowl", "game thread", "match thread", "episode",
    "salary", "hiring", "fired", "quit my job", "interview",
    "recipe", "protein powder", "creatine", "preworkout",
    "what should i eat", "calorie count", "bulk or cut",
    "favorite golf course", "handicap", "putting",
    "what bike should", "new bike day", "strava",
}


def score_post_relevance(title: str, subreddit: str = "") -> float:
    """Score a Reddit post's relevance from 0.0 to 1.0.

    Uses keyword matching on the title (case-insensitive).
    Pain/therapy subreddits get a baseline boost.
    Broad subs require strong keyword matches to pass threshold.
    """
    title_lower = title.lower()
    # Tokenize for word-boundary matching of short ambiguous terms
    words = set(title_lower.split())

    # Check negative keywords first — strong disqualifier
    for neg in _NEGATIVE_KEYWORDS:
        if neg in title_lower:
            return 0.0

    # Base score from subreddit reputation
    high_relevance_subs = {
        "backpain", "sciatica", "chronicpain", "physicaltherapy",
        "pelvicfloor", "tmj", "posture", "ergonomics",
    }
    medium_relevance_subs = {
        "fibromyalgia", "flexibility", "bodyweightfitness",
        "yogatherapy", "cancer", "cancerfighters", "breastcancer",
        "advancedrunning", "ultrarunning",
    }
    # Broad subs (Fitness, CrossFit, golf, running, etc.) get low base (0.1)
    # so only posts with 2+ keyword matches survive the 0.35 threshold

    sub_lower = subreddit.lower()
    if sub_lower in high_relevance_subs:
        base = 0.4
    elif sub_lower in medium_relevance_subs:
        base = 0.25
    else:
        base = 0.1

    # Keyword match scoring — strong matches worth 0.2, weak worth 0.1
    strong_matches = 0
    weak_matches = 0
    for kw in _POSITIVE_KEYWORDS:
        if len(kw) <= 4:
            # Short words ("back", "hip", "knee") — require word boundary
            # to avoid "back off", "hip hop", "knee-jerk reaction to..."
            if kw in words:
                weak_matches += 1
        else:
            # Multi-char keywords — substring match is fine
            if kw in title_lower:
                strong_matches += 1

    keyword_score = min(strong_matches * 0.2 + weak_matches * 0.1, 0.6)

    return min(base + keyword_score, 1.0)


def filter_reddit_posts(
    reddit_data: dict[str, list[dict[str, Any]]] | None,
    min_relevance: float = 0.35,
    max_per_sub: int = 5,
) -> dict[str, list[dict[str, Any]]] | None:
    """Filter Reddit posts by relevance score.

    Args:
        reddit_data: Raw Reddit data {subreddit: [post_dicts]}
        min_relevance: Minimum relevance score to keep (0.0-1.0)
        max_per_sub: Max posts to keep per subreddit after filtering

    Returns:
        Filtered Reddit data with only relevant posts, or None.
    """
    if not reddit_data:
        return None

    filtered: dict[str, list[dict[str, Any]]] = {}
    total_before = 0
    total_after = 0

    for sub, posts in reddit_data.items():
        if not isinstance(posts, list):
            continue

        total_before += len(posts)
        scored = []
        for post in posts:
            title = post.get("title", "")
            score = score_post_relevance(title, sub)
            if score >= min_relevance:
                post["relevance_score"] = round(score, 2)
                scored.append(post)

        # Sort by relevance, then by Reddit score
        scored.sort(
            key=lambda p: (p.get("relevance_score", 0), p.get("score", 0)),
            reverse=True,
        )

        if scored:
            filtered[sub] = scored[:max_per_sub]
            total_after += len(filtered[sub])

    if filtered:
        print(f"[Reddit Filter] Kept {total_after}/{total_before} posts "
              f"({total_after/max(total_before,1)*100:.0f}% relevant)")
    else:
        print("[Reddit Filter] No relevant posts found after filtering")

    return filtered if filtered else None
