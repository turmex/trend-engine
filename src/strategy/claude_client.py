"""Trend Engine V2.0 — Claude API Client.

Sends a fully-assembled prompt to the Anthropic Messages API, parses the
JSON response, and validates the required top-level keys. Includes retry
logic with backoff for transient server errors.
"""

from __future__ import annotations

import json
import time

import requests

# Keys that must be present in a valid playbook response
_REQUIRED_KEYS = frozenset(
    {"theme_narrative", "monday_video", "wednesday_post", "friday_card", "seo_notes"}
)


def _extract_json(text: str) -> dict | None:
    """Attempt to parse *text* as JSON, falling back to brace extraction.

    First tries ``json.loads`` on the raw text.  If that fails, locates the
    first ``{`` and last ``}`` and tries to parse the substring between them.

    Returns
    -------
    dict | None
        Parsed dictionary on success, ``None`` on failure.
    """
    # Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # Brace extraction fallback
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


def _validate_keys(data: dict) -> bool:
    """Return ``True`` if *data* contains all required top-level keys."""
    return _REQUIRED_KEYS.issubset(data.keys())


def call_claude(
    prompt: str,
    api_key: str,
    model: str = "claude-sonnet-4-5-20250929",
    max_tokens: int = 4096,
) -> dict | None:
    """Send *prompt* to the Claude Messages API and return parsed JSON.

    Parameters
    ----------
    prompt:
        The fully-assembled prompt string (from ``build_claude_prompt``).
    api_key:
        Anthropic API key (``ANTHROPIC_API_KEY``).
    model:
        Model identifier to use.
    max_tokens:
        Maximum tokens for the response.

    Returns
    -------
    dict | None
        Parsed playbook dictionary on success.  ``None`` when the API call
        fails, the response is not valid JSON, or required keys are missing.
    """
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}],
    }

    max_attempts = 2  # 1 initial + 1 retry
    backoff_seconds = 5

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=120
            )

            # Retry on server errors (5xx)
            if response.status_code >= 500:
                print(
                    f"[claude_client] Server error {response.status_code} "
                    f"(attempt {attempt}/{max_attempts})"
                )
                if attempt < max_attempts:
                    time.sleep(backoff_seconds)
                    continue
                print("[claude_client] All retries exhausted on server error.")
                return None

            # Rate limited — wait and retry
            if response.status_code == 429:
                print(
                    f"[claude_client] Rate limited (429), waiting 30s "
                    f"(attempt {attempt}/{max_attempts})"
                )
                if attempt < max_attempts:
                    time.sleep(30)
                    continue
                print("[claude_client] Rate limit retries exhausted.")
                return None

            # Insufficient balance or auth error — no retry, fall to template
            if response.status_code in (401, 402, 403):
                print(
                    f"[claude_client] Auth/billing error {response.status_code}: "
                    f"{response.text[:300]}"
                )
                return None

            # Other non-retryable client errors
            if response.status_code != 200:
                print(
                    f"[claude_client] API returned status {response.status_code}: "
                    f"{response.text[:500]}"
                )
                return None

            # Parse the API envelope
            envelope = response.json()
            content_blocks = envelope.get("content", [])
            if not content_blocks:
                print("[claude_client] Empty content in API response.")
                return None

            raw_text: str = content_blocks[0].get("text", "")
            if not raw_text:
                print("[claude_client] Empty text in first content block.")
                return None

            # Extract and validate JSON
            parsed = _extract_json(raw_text)
            if parsed is None:
                print("[claude_client] Failed to parse JSON from response text.")
                return None

            if not _validate_keys(parsed):
                missing = _REQUIRED_KEYS - parsed.keys()
                print(
                    f"[claude_client] Response missing required keys: {missing}"
                )
                return None

            return parsed

        except requests.exceptions.Timeout:
            print(
                f"[claude_client] Request timed out (attempt {attempt}/{max_attempts})"
            )
            if attempt < max_attempts:
                time.sleep(backoff_seconds)
                continue
            print("[claude_client] All retries exhausted on timeout.")
            return None

        except requests.exceptions.RequestException as exc:
            print(f"[claude_client] Request error: {exc}")
            if attempt < max_attempts:
                time.sleep(backoff_seconds)
                continue
            return None

        except (KeyError, IndexError, TypeError) as exc:
            print(f"[claude_client] Unexpected response structure: {exc}")
            return None

    return None
