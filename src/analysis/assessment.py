"""
FormCoach Trend Engine — Weekly Movement Assessment Suggestions
================================================================
Maps common pain/fitness theme keywords to self-assessment tests that
viewers can perform at home.  Each assessment connects the test result
back to the video content, driving engagement and credibility.
"""

from __future__ import annotations

from typing import Any


# ─── Theme -> assessment mapping ─────────────────────────────────────
# Each entry carries the full assessment payload: name, step-by-step
# instructions, what the result reveals, and a call-to-action that
# ties the test back to video content.

THEME_ASSESSMENTS: dict[str, dict[str, str]] = {
    "sciatica": {
        "assessment_name": "Straight Leg Raise Test",
        "instructions": (
            "Lie flat on your back on a firm surface. Keep both legs "
            "straight. Slowly lift one leg upward, keeping the knee "
            "locked. Note the angle at which you feel pain, tingling, "
            "or tightness down the back of your leg. Repeat on the "
            "other side."
        ),
        "what_it_reveals": (
            "Pain or tingling before reaching 60 degrees suggests "
            "sciatic nerve involvement — the nerve is being tensioned "
            "by a disc bulge or piriformis tightness."
        ),
        "cta": (
            "If you feel symptoms before 60 degrees, the nerve "
            "flossing and decompression exercises in today's video "
            "are exactly what you need to start relieving that tension."
        ),
    },
    "lower back pain": {
        "assessment_name": "Wall Test for Lordosis",
        "instructions": (
            "Stand with your heels, buttocks, shoulders, and the back "
            "of your head all touching a wall. Now try to slide your "
            "hand between your lower back and the wall. Note how much "
            "space there is."
        ),
        "what_it_reveals": (
            "If your entire hand (or more) fits easily behind your "
            "lower back, you likely have excess lumbar lordosis — an "
            "exaggerated curve that compresses discs and facet joints."
        ),
        "cta": (
            "If your hand slides through easily, the core bracing "
            "and pelvic tilt drills in today's video will help you "
            "restore a neutral spine position."
        ),
    },
    "posture": {
        "assessment_name": "Wall Posture Check",
        "instructions": (
            "Stand with your back against a wall. Try to touch your "
            "heels, buttocks, shoulder blades, AND the back of your "
            "head to the wall simultaneously. Hold for 10 seconds and "
            "note what feels difficult or impossible."
        ),
        "what_it_reveals": (
            "Most desk workers cannot get all four contact points at "
            "once. If your head won't reach, your thoracic spine is "
            "likely in kyphosis. If your lower back arches away, your "
            "hip flexors may be tight."
        ),
        "cta": (
            "If you can't hit all four points, the posture correction "
            "sequence in today's video targets exactly the areas that "
            "are pulling you out of alignment."
        ),
    },
    "hip pain": {
        "assessment_name": "Single-Leg Balance Test",
        "instructions": (
            "Stand on one leg with your arms relaxed at your sides. "
            "Close your eyes and try to hold the position for 30 "
            "seconds. Time yourself on each side and note any wobbling "
            "or inability to maintain balance."
        ),
        "what_it_reveals": (
            "Lasting under 15 seconds suggests hip stabilizer weakness "
            "— specifically the gluteus medius and deep rotators. A "
            "large side-to-side difference reveals asymmetry that may "
            "be driving your hip pain."
        ),
        "cta": (
            "If you can't hold 30 seconds with eyes closed, the hip "
            "stabilizer exercises in today's video will build exactly "
            "the control you're missing."
        ),
    },
    "neck pain": {
        "assessment_name": "Chin Tuck Test",
        "instructions": (
            "Sit or stand tall. Without tilting your head up or down, "
            "gently draw your chin straight back — as if making a "
            "'double chin.' Hold for 5 seconds and note whether you "
            "feel pain, a blocking sensation, or difficulty performing "
            "the movement."
        ),
        "what_it_reveals": (
            "If the chin tuck hurts or feels blocked, your deep neck "
            "flexors are likely inhibited — a hallmark of forward-head "
            "posture. These muscles are the 'core' of your neck."
        ),
        "cta": (
            "If the chin tuck felt painful or stuck, the deep neck "
            "flexor activation drills in today's video are your "
            "starting point for lasting neck pain relief."
        ),
    },
    "shoulder pain": {
        "assessment_name": "Apley Scratch Test",
        "instructions": (
            "Reach one hand over the top of your shoulder and down "
            "your back. Simultaneously reach the other hand behind "
            "your back and up. Try to touch your fingertips together. "
            "Measure the gap (or overlap) and then switch sides to "
            "compare."
        ),
        "what_it_reveals": (
            "A gap larger than two inches — or a significant "
            "difference between sides — indicates restricted shoulder "
            "rotation. The tight side often points to the rotator cuff "
            "or lat that's driving the pain."
        ),
        "cta": (
            "If your hands can't meet — or one side is noticeably "
            "tighter — the shoulder mobility drills in today's video "
            "address those exact restrictions."
        ),
    },
    "knee pain": {
        "assessment_name": "Single-Leg Squat Test",
        "instructions": (
            "Stand on one leg near a wall or chair for safety. Slowly "
            "perform a shallow squat on that single leg, going down "
            "about 4-6 inches. Watch your knee in a mirror or have "
            "someone observe: does it cave inward, drift outward, or "
            "track straight over your toes?"
        ),
        "what_it_reveals": (
            "If your knee collapses inward (valgus), it signals "
            "weakness in the VMO (inner quad) and gluteus medius. This "
            "medial collapse is one of the most common drivers of "
            "runner's knee, IT band syndrome, and patellofemoral pain."
        ),
        "cta": (
            "If your knee caved inward, the VMO and glute activation "
            "exercises in today's video target the exact muscles that "
            "need to fire to protect your knee."
        ),
    },
    "cancer fatigue exercise": {
        "assessment_name": "Talk Test for Exercise Intensity",
        "instructions": (
            "Go for a walk at your current comfortable pace. While "
            "walking, try to carry on a conversation and then try to "
            "sing a line from a song. Note whether you can talk "
            "comfortably, talk but not sing, or struggle to talk."
        ),
        "what_it_reveals": (
            "If you can talk but not sing, you're in Zone 2 — the "
            "ideal aerobic recovery intensity. This is the sweet spot "
            "for building endurance without triggering excessive "
            "fatigue, which is especially important for managing "
            "cancer-related fatigue."
        ),
        "cta": (
            "If you found your 'talk but can't sing' pace, the "
            "gentle movement progressions in today's video are "
            "designed to keep you right in that recovery zone."
        ),
    },
    "runner's knee": {
        "assessment_name": "Step-Down Test",
        "instructions": (
            "Stand on a step or sturdy platform (6-8 inches high) on "
            "one leg. Slowly lower the opposite heel toward the floor "
            "by bending the standing knee. Watch your standing knee "
            "carefully — does it cave inward, shake, or do you feel "
            "pain under the kneecap?"
        ),
        "what_it_reveals": (
            "Knee caving inward during the step-down reveals the same "
            "VMO/glute medius weakness pattern that drives runner's "
            "knee. Pain under the kneecap during this movement "
            "confirms patellofemoral involvement."
        ),
        "cta": (
            "If your knee caved inward or you felt kneecap pain, the "
            "targeted strengthening exercises in today's video were "
            "designed for exactly this pattern."
        ),
    },
    "yoga": {
        "assessment_name": "Forward Fold Baseline Assessment",
        "instructions": (
            "Stand with feet hip-width apart, knees straight but not "
            "locked. Slowly fold forward from the hips, reaching your "
            "hands toward the floor. Note where your fingertips reach: "
            "mid-shin, ankles, floor, or past your toes. Do not bounce "
            "or force the stretch."
        ),
        "what_it_reveals": (
            "Your forward fold reach is a reliable baseline for "
            "posterior chain flexibility — hamstrings, glutes, and "
            "spinal extensors. Retesting after 4-6 weeks shows real "
            "progress that's hard to see day-to-day."
        ),
        "cta": (
            "Note where your hands reach today. Follow the flexibility "
            "sequence in today's video for four weeks and retest — "
            "you'll have objective proof of your progress."
        ),
    },
}

# ─── Default assessment for unrecognized themes ──────────────────────

_DEFAULT_ASSESSMENT: dict[str, str] = {
    "assessment_name": "Overhead Squat Assessment",
    "instructions": (
        "Stand with feet shoulder-width apart. Raise both arms straight "
        "overhead, biceps by your ears. Slowly squat down as far as "
        "comfortable. Note where you feel limited: ankles, hips, upper "
        "back, or shoulders."
    ),
    "what_it_reveals": (
        "The overhead squat reveals your body's priority compensation "
        "pattern. Heels rising = ankle mobility. Knees caving = hip "
        "weakness. Arms falling forward = thoracic stiffness. The first "
        "thing that breaks down is your starting point."
    ),
    "cta": (
        "Whatever broke down first in your overhead squat, the exercises "
        "in today's video are designed to address that exact limitation."
    ),
}


# ─── Internal: fuzzy matching ────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase and strip a string for matching."""
    return text.lower().strip()


def _token_overlap_score(query_tokens: set[str], key_tokens: set[str]) -> float:
    """Compute a simple token-overlap similarity score.

    Returns the fraction of key tokens found in the query, giving
    partial credit for substring matches within tokens.

    Args:
        query_tokens: Set of lowercased words from the input theme.
        key_tokens: Set of lowercased words from a dictionary key.

    Returns:
        A float in [0.0, 1.0].
    """
    if not key_tokens:
        return 0.0

    matched = 0.0
    for kt in key_tokens:
        # Exact token match
        if kt in query_tokens:
            matched += 1.0
            continue
        # Substring match: query token contains key token or vice versa
        for qt in query_tokens:
            if kt in qt or qt in kt:
                matched += 0.75
                break

    return matched / len(key_tokens)


def _find_best_match(theme: str) -> str | None:
    """Find the best-matching THEME_ASSESSMENTS key for a theme string.

    Uses token-overlap scoring to handle partial and fuzzy matches.
    Returns ``None`` if no key scores above a minimum threshold.

    Args:
        theme: The raw theme string to match.

    Returns:
        The best-matching key from ``THEME_ASSESSMENTS``, or ``None``
        if no key meets the similarity threshold (0.4).
    """
    query_tokens = set(_normalize(theme).split())
    if not query_tokens:
        return None

    best_key: str | None = None
    best_score: float = 0.0
    threshold: float = 0.4

    for key in THEME_ASSESSMENTS:
        key_tokens = set(_normalize(key).split())

        # Check exact containment first (theme contains the full key)
        if _normalize(key) in _normalize(theme):
            return key

        score = _token_overlap_score(query_tokens, key_tokens)
        if score > best_score:
            best_score = score
            best_key = key

    if best_score >= threshold:
        return best_key

    return None


# ═════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════


def suggest_assessment(theme: str) -> dict[str, Any]:
    """Suggest a self-assessment test based on a content theme.

    Uses fuzzy matching to find the most relevant assessment from
    ``THEME_ASSESSMENTS``.  Falls back to a general overhead-squat
    assessment if no match meets the similarity threshold.

    Args:
        theme: The content theme or topic keyword to match against
            (e.g. ``"sciatica"``, ``"lower back pain"``,
            ``"hip mobility issues"``).

    Returns:
        A dict with keys:

        - ``assessment_name`` (str): Name of the test.
        - ``instructions`` (str): Step-by-step directions the viewer
          can follow at home.
        - ``what_it_reveals`` (str): What the test result means.
        - ``cta`` (str): Call-to-action connecting the test result
          to the video content.
        - ``matched_theme`` (str): The dictionary key that was
          matched, or ``"default"`` if the fallback was used.
        - ``input_theme`` (str): The original theme string passed in.

    Example::

        >>> result = suggest_assessment("my sciatica is killing me")
        >>> result["assessment_name"]
        'Straight Leg Raise Test'
        >>> result["matched_theme"]
        'sciatica'
    """
    matched_key = _find_best_match(theme)

    if matched_key is not None:
        entry = THEME_ASSESSMENTS[matched_key]
        return {
            "assessment_name": entry["assessment_name"],
            "instructions": entry["instructions"],
            "what_it_reveals": entry["what_it_reveals"],
            "cta": entry["cta"],
            "matched_theme": matched_key,
            "input_theme": theme,
        }

    return {
        "assessment_name": _DEFAULT_ASSESSMENT["assessment_name"],
        "instructions": _DEFAULT_ASSESSMENT["instructions"],
        "what_it_reveals": _DEFAULT_ASSESSMENT["what_it_reveals"],
        "cta": _DEFAULT_ASSESSMENT["cta"],
        "matched_theme": "default",
        "input_theme": theme,
    }
