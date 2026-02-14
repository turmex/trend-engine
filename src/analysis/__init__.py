# FormCoach Trend Engine — Analysis Layer

from .emerging import detect_emerging_signals, deduplicate_reddit_posts
from .theme import select_theme, build_analysis
from .engagement import rank_engagement_opportunities
from .seasonal import get_seasonal_context, SEASONAL_CALENDAR
from .assessment import suggest_assessment, THEME_ASSESSMENTS

__all__ = [
    "detect_emerging_signals",
    "deduplicate_reddit_posts",
    "select_theme",
    "build_analysis",
    "rank_engagement_opportunities",
    "get_seasonal_context",
    "SEASONAL_CALENDAR",
    "suggest_assessment",
    "THEME_ASSESSMENTS",
]
