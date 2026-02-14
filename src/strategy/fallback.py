"""Trend Engine V2.0 — Template-Based Fallback Strategy.

Generates a content playbook using static templates when no Anthropic API
key is configured.  The output dict matches the same JSON schema that the
Claude API would return, so the rest of the pipeline can consume it
without branching.
"""

from __future__ import annotations

from config import EXERCISE_PROTOCOLS


def generate_fallback_strategy(
    analysis: dict,
    topic_solutions: dict,
) -> dict:
    """Build a template-based weekly content strategy.

    Uses the theme from *analysis* and the exercise list from
    *topic_solutions* to fill in a deterministic playbook.  Every
    ``[Bart: ...]`` placeholder is preserved so Bart can inject clinical
    detail during review.

    Parameters
    ----------
    analysis:
        Aggregated analysis dict.  Must contain at least a ``"theme"`` key.
    topic_solutions:
        Mapping of lowercase topic names to lists of exercise name strings.

    Returns
    -------
    dict
        Playbook dictionary with keys ``theme_narrative``, ``monday_video``,
        ``wednesday_post``, ``friday_card``, and ``seo_notes``.
    """
    theme: str = analysis.get("theme", "posture")
    theme_lower = theme.lower()
    exercises: list[str] = topic_solutions.get(
        theme_lower, topic_solutions.get("posture", [])
    )

    # Use clinical protocols when available (structured sets/reps/contraindications)
    clinical = EXERCISE_PROTOCOLS.get(theme_lower, [])

    return {
        "theme_narrative": (
            f"This week '{theme}' is trending across search, social, and "
            f"health forums. Based on the data we collected, this is a high-"
            f"opportunity topic for Bart's audience of desk workers, athletes, "
            f"and chronic-pain patients."
        ),
        "monday_video": {
            "title": (
                f"{theme.title()} \u2014 {len(exercises)} Exercises That "
                f"Actually Work (2026)"
            ),
            "hook": (
                f"'{theme.title()}' searches are surging right now. Most "
                f"advice online is wrong. Here's what actually works based "
                f"on 15,000 hours of clinical experience."
            ),
            "talking_points": [
                f"Open with the data: '{theme}' is trending because...",
                "Explain the biomechanics: here's what's happening in the body",
                "Common mistakes: what most people do that makes it worse",
                (
                    f"The fix: walk through {len(exercises)} exercises with "
                    f"form cues"
                ),
            ],
            "exercises": (
                [
                    {
                        "name": p["name"],
                        "form_cue": f"{p['sets']}",
                        "sets": p.get("sets", ""),
                        "progression": p.get("progression", ""),
                        "regression": p.get("regression", ""),
                        "contraindication": p.get("contraindication", ""),
                    }
                    for p in clinical
                ]
                if clinical
                else [
                    {"name": ex, "form_cue": "[Bart: add specific form cue]"}
                    for ex in exercises
                ]
            ),
            "end_cta": (
                "Try these today and tell me in the comments how you feel "
                "by Wednesday."
            ),
            "platforms": {
                "youtube": {
                    "description": (
                        f"Searches for {theme} are trending this week. In "
                        f"this video Bart Firch walks through {len(exercises)} "
                        f"evidence-based exercises you can do at your desk or "
                        f"at home. Timestamps below. Full blog post: "
                        f"https://bartonfirch.com"
                    ),
                    "tags": [
                        theme,
                        f"{theme} exercises",
                        "pain relief",
                        "posture correction",
                        "desk worker exercises",
                        f"{theme} 2026",
                        "corrective exercise",
                        "mobility",
                    ],
                },
                "linkedin": (
                    f"'{theme.title()}' searches are surging. Most advice? "
                    f"Dangerously oversimplified. Here's what 15,000 hours "
                    f"of clinical work taught me."
                ),
                "instagram_reels": (
                    f"'{theme.title()}' is trending \u2014 here's the fix\n\n"
                    f"{len(exercises)} exercises you can do right now\n\n"
                    f"Save this. Try it today.\n\n"
                    f"#{theme.replace(' ', '')} #posturecorrection "
                    f"#painrelief #mobility"
                ),
                "tiktok": (
                    f"{theme} is blowing up rn \u2014 here's what actually "
                    f"works #{theme.replace(' ', '')} #fitness #health"
                ),
            },
            "thumbnail": {
                "text_overlay": f"{theme.title()} Fix",
                "pose_suggestion": f"Bart demonstrating the first exercise for {theme}",
                "color_scheme": "Bold white text on dark background",
            },
            "viewer_assessment": (
                f"Before starting these exercises, try this quick self-test to see "
                f"where you stand. [Bart: add a 30-second assessment relevant to {theme}]"
            ),
        },
        "wednesday_post": {
            "linkedin_draft": (
                f"Monday I shared a {theme} routine that resonated with a "
                f"lot of you.\n\n"
                f"Reading through the comments, two things stood out:\n\n"
                f"1. Most of you sit 8+ hours a day and feel it.\n"
                f"2. You've tried stretching but nothing sticks.\n\n"
                f"Here's why \u2014 and what to do instead.\n\n"
                f"[Bart: add clinical detail about why static stretching "
                f"alone doesn't fix {theme}]\n\n"
                f"The exercises I showed Monday work because they target "
                f"the root cause, not just the symptom.\n\n"
                f"[Bart: add 2-3 sentences of biomechanical explanation]\n\n"
                f"If you missed Monday's video, link in comments."
            ),
            "blog_title": (
                f"How to Fix {theme.title()}: Evidence-Based Exercises"
            ),
            "blog_meta_description": (
                f"Evidence-based {theme} exercises from 15K+ hours of "
                f"clinical experience. Step-by-step guide with form cues."
            )[:155],
            "medium_subtitle": "Data-driven exercise prescription",
            "cross_post_note": (
                "Blog (bartonfirch.com) -> Medium (canonical) -> Substack"
            ),
            "study_citation": (
                f"[Bart: cite a relevant PubMed study on {theme} if available from this week's brief]"
            ),
        },
        "friday_card": {
            "stat_headline": (
                f"'{theme.title()}' searches are trending this month"
            ),
            "tip": (
                f"Start with "
                f"{exercises[0] if exercises else 'gentle mobility'} "
                f"\u2014 30 seconds, twice a day."
            ),
            "engagement_ask": (
                f"You've had the {theme} exercises for 4 days. How does "
                f"your body feel?"
            ),
            "platforms": {
                "linkedin": (
                    f"The data this week pointed to '{theme}' as a breakout "
                    f"topic. Monday we covered the exercises. Wednesday we "
                    f"went deeper. Today \u2014 one stat and one tip to carry "
                    f"into the weekend."
                ),
                "pinterest": (
                    f"{theme.title()} exercises and stretches for pain "
                    f"relief. Evidence-based routine from a pain management "
                    f"coach with 15,000+ hours of clinical experience. Save "
                    f"this pin for your next desk break."
                ),
                "twitter": (
                    f"1/ '{theme.title()}' is trending \u2014 here's one "
                    f"stat and one fix.\n\n"
                    f"2/ Tip: "
                    f"{exercises[0] if exercises else 'gentle mobility'}, "
                    f"30 sec, 2x/day.\n\n"
                    f"3/ Full routine \u2192 https://bartonfirch.com"
                ),
            },
        },
        "seo_notes": {
            "target_keyword": f"{theme} exercises",
            "secondary_keywords": [
                f"how to fix {theme}",
                f"{theme} stretches",
                f"best exercises for {theme}",
            ],
            "schema_types": ["HowTo", "FAQPage"],
            "ai_findability_tips": [
                (
                    f"Use Q&A format: 'What causes {theme}?' with a direct "
                    f"answer paragraph so LLMs and featured snippets can "
                    f"extract it"
                ),
                (
                    "Include structured data (HowTo + FAQPage schema) for "
                    "search engines and AI crawlers"
                ),
                (
                    "Write definitive statements LLMs can quote as "
                    "authoritative \u2014 e.g. 'The most effective exercise "
                    f"for {theme} is...'"
                ),
            ],
        },
        "engagement_replies": [
            {
                "post_title": "[Top engagement opportunity title]",
                "suggested_reply": (
                    f"Great question. From my clinical experience with {theme}, "
                    f"the most common mistake I see is jumping straight to stretching "
                    f"without addressing the underlying movement pattern. "
                    f"Try starting with {exercises[0] if exercises else 'gentle mobility'} — "
                    f"it targets the root cause rather than just the symptom."
                ),
            }
        ],
    }
