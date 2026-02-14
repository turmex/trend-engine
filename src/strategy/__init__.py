# FormCoach Trend Engine — AI Strategy Generation

from .prompt_builder import build_claude_prompt
from .claude_client import call_claude
from .fallback import generate_fallback_strategy

__all__ = ["build_claude_prompt", "call_claude", "generate_fallback_strategy"]
