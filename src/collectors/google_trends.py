"""
Google Trends collector with multi-layer resilience.

Architecture:
  Layer 1: trendspy library (active replacement for archived pytrends)
  Layer 2: File cache (12h TTL — avoids repeat 429s during testing)
  Layer 3: Exponential backoff with jitter (30s base, random 5-30s added)
  Layer 4: Partial result acceptance (getting 40/60 keywords is fine)
  Layer 5: Stale cache fallback (any cached data beats no data)

pytrends was archived April 2025. trendspy is its actively-maintained
successor with proxy support and smarter batch handling.
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Cache location
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_CACHE_TRENDS = _CACHE_DIR / "cache_trends.json"
_CACHE_RISING = _CACHE_DIR / "cache_rising.json"
_CACHE_TTL_HOURS = 12

# Try trendspy first (actively maintained), fall back to pytrends
_ENGINE = None
try:
    from trendspy import Trends
    _ENGINE = "trendspy"
except ImportError:
    pass

if _ENGINE is None:
    try:
        from pytrends.request import TrendReq
        _ENGINE = "pytrends"
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache(cache_file: Path, max_age_hours: int = _CACHE_TTL_HOURS) -> dict | None:
    """Load cached data if within TTL."""
    if not cache_file.exists():
        return None
    try:
        raw = json.loads(cache_file.read_text())
        cached_at = datetime.fromisoformat(raw.get("_cached_at", "2000-01-01"))
        age = datetime.now() - cached_at
        if age > timedelta(hours=max_age_hours):
            return None
        print(f"[Google Trends] Using cache ({age.seconds // 60}m old)")
        return raw.get("results")
    except Exception:
        return None


def _load_stale_cache(cache_file: Path) -> dict | None:
    """Load cache regardless of age — last resort fallback."""
    if not cache_file.exists():
        return None
    try:
        raw = json.loads(cache_file.read_text())
        cached_at = raw.get("_cached_at", "unknown")
        print(f"[Google Trends] Using STALE cache from {cached_at} (all live requests failed)")
        return raw.get("results")
    except Exception:
        return None


def _save_cache(cache_file: Path, results: dict) -> None:
    """Save data to cache file."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "_cached_at": datetime.now().isoformat(),
        "results": results,
    }
    try:
        cache_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    except Exception as exc:
        print(f"[Google Trends] Cache write failed: {exc}")


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def _pct_change(old: float, new: float) -> float | None:
    """Percentage change between two values."""
    if old == 0:
        return None
    return round(((new - old) / old) * 100, 2)


def _trend_direction(values: list[float]) -> str:
    """Determine trend from a time series: rising, falling, or stable."""
    if not values or len(values) < 2:
        return "stable"

    midpoint = len(values) // 2
    first_half_avg = sum(values[:midpoint]) / max(len(values[:midpoint]), 1)
    second_half_avg = sum(values[midpoint:]) / max(len(values[midpoint:]), 1)

    if first_half_avg == 0:
        return "rising" if second_half_avg > 0 else "stable"

    change = ((second_half_avg - first_half_avg) / first_half_avg) * 100

    if change > 5:
        return "rising"
    elif change < -5:
        return "falling"
    return "stable"


def _compute_metrics(series: list) -> dict[str, Any]:
    """Compute trend metrics from a time series."""
    current = int(series[-1])
    prev_week = int(series[-8]) if len(series) >= 8 else int(series[0])
    wow_pct = _pct_change(prev_week, current)
    four_weeks = series[-28:] if len(series) >= 28 else series
    four_w_avg = round(sum(four_weeks) / len(four_weeks), 2)
    four_w_trend = _trend_direction(four_weeks)
    return {
        "current": current,
        "prev_week": prev_week,
        "wow_pct": wow_pct,
        "4w_trend": four_w_trend,
        "4w_avg": four_w_avg,
    }


# ---------------------------------------------------------------------------
# trendspy engine
# ---------------------------------------------------------------------------

def _new_trendspy_session() -> "Trends":
    """Create a trendspy session with tuned rate limiting."""
    tr = Trends()
    tr.request_delay = 10.0   # 10s between internal requests (default 1s)
    return tr


def _fetch_trendspy(
    keywords: list[str],
    batch_size: int = 5,
) -> dict[str, dict[str, Any]]:
    """Fetch interest-over-time data using trendspy."""
    tr = _new_trendspy_session()
    results: dict[str, dict[str, Any]] = {}
    batches = [keywords[i : i + batch_size] for i in range(0, len(keywords), batch_size)]
    consecutive_429s = 0

    for batch_idx, batch in enumerate(batches):
        if consecutive_429s >= 3:
            print(
                f"[Google Trends] 3 consecutive 429s — stopping early. "
                f"Got {len(results)}/{len(keywords)} keywords."
            )
            break

        print(f"[Google Trends] Batch {batch_idx + 1}/{len(batches)}: {batch}")

        success = False
        for attempt in range(3):
            try:
                df = tr.interest_over_time(batch, timeframe="today 3-m", geo="US")

                if df is not None and not df.empty:
                    if "isPartial" in df.columns:
                        df = df.drop(columns=["isPartial"])
                    for kw in batch:
                        if kw in df.columns:
                            series = df[kw].tolist()
                            if series:
                                results[kw] = _compute_metrics(series)

                consecutive_429s = 0
                success = True
                break

            except Exception as exc:
                error_msg = str(exc)
                if "429" in error_msg:
                    consecutive_429s += 1
                    wait = (30 * (2 ** attempt)) + random.randint(5, 30)
                    print(
                        f"[Google Trends] 429 on batch {batch_idx + 1}, "
                        f"attempt {attempt + 1}/3. Waiting {wait}s..."
                    )
                    time.sleep(wait)
                    tr = _new_trendspy_session()  # fresh session
                else:
                    print(f"[Google Trends] Error: {exc}")
                    break

        if not success:
            print(f"[Google Trends] Skipping batch {batch_idx + 1} after failures")

        # Delay between batches — randomized to avoid pattern detection
        if batch_idx < len(batches) - 1:
            delay = 25 + random.randint(5, 20)
            time.sleep(delay)

    return results


def _fetch_rising_trendspy(
    keywords: list[str],
    batch_size: int = 5,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Fetch rising/top related queries using trendspy.

    trendspy.related_queries() takes a single keyword string.
    We query one keyword at a time with delays between.
    """
    tr = _new_trendspy_session()
    results: dict[str, dict[str, list[dict[str, Any]]]] = {}
    consecutive_429s = 0

    for kw_idx, kw in enumerate(keywords):
        if consecutive_429s >= 3:
            print(
                f"[Rising Queries] 3 consecutive 429s — stopping early. "
                f"Got queries for {len(results)}/{len(keywords)} keywords."
            )
            break

        if (kw_idx % 10 == 0) or kw_idx == len(keywords) - 1:
            print(f"[Rising Queries] Keyword {kw_idx + 1}/{len(keywords)}: {kw}")

        for attempt in range(2):
            try:
                related = tr.related_queries(kw, timeframe="today 3-m", geo="US")
                if related:
                    # trendspy returns {keyword: {rising: df, top: df}}
                    kw_data = related.get(kw, related)
                    rising_list = _parse_df_to_list(kw_data.get("rising"))
                    top_list = _parse_df_to_list(kw_data.get("top"))
                    if rising_list or top_list:
                        results[kw] = {"rising": rising_list, "top": top_list}

                consecutive_429s = 0
                break

            except Exception as exc:
                if "429" in str(exc):
                    consecutive_429s += 1
                    wait = (30 * (2 ** attempt)) + random.randint(5, 30)
                    print(f"[Rising Queries] 429 on '{kw}', waiting {wait}s...")
                    time.sleep(wait)
                    tr = _new_trendspy_session()
                else:
                    print(f"[Rising Queries] Error on '{kw}': {exc}")
                    break

        # Delay between keywords
        if kw_idx < len(keywords) - 1:
            time.sleep(5 + random.randint(2, 8))

    return results


# ---------------------------------------------------------------------------
# pytrends engine (fallback for users who haven't switched yet)
# ---------------------------------------------------------------------------

def _fetch_pytrends(
    keywords: list[str],
    batch_size: int = 5,
) -> dict[str, dict[str, Any]]:
    """Fetch interest-over-time data using pytrends (legacy fallback)."""
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    results: dict[str, dict[str, Any]] = {}
    batches = [keywords[i : i + batch_size] for i in range(0, len(keywords), batch_size)]
    consecutive_429s = 0

    for batch_idx, batch in enumerate(batches):
        if consecutive_429s >= 3:
            print(
                f"[Google Trends] 3 consecutive 429s — stopping. "
                f"Got {len(results)}/{len(keywords)} keywords."
            )
            break

        print(f"[Google Trends] Batch {batch_idx + 1}/{len(batches)}: {batch}")

        success = False
        for attempt in range(3):
            try:
                pytrends.build_payload(batch, cat=0, timeframe="today 3-m", geo="US")
                df = pytrends.interest_over_time()
                if df is not None and not df.empty:
                    if "isPartial" in df.columns:
                        df = df.drop(columns=["isPartial"])
                    for kw in batch:
                        if kw in df.columns:
                            series = df[kw].tolist()
                            if series:
                                results[kw] = _compute_metrics(series)
                consecutive_429s = 0
                success = True
                break

            except Exception as exc:
                if "429" in str(exc):
                    consecutive_429s += 1
                    wait = (30 * (2 ** attempt)) + random.randint(5, 30)
                    print(
                        f"[Google Trends] 429, attempt {attempt + 1}/3. Waiting {wait}s..."
                    )
                    time.sleep(wait)
                    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
                else:
                    print(f"[Google Trends] Error: {exc}")
                    break

        if not success:
            print(f"[Google Trends] Skipping batch {batch_idx + 1}")

        if batch_idx < len(batches) - 1:
            delay = 20 + random.randint(5, 15)
            time.sleep(delay)

    return results


def _fetch_rising_pytrends(
    keywords: list[str],
    batch_size: int = 5,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Fetch rising queries using pytrends (legacy fallback)."""
    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
    results: dict[str, dict[str, list[dict[str, Any]]]] = {}
    batches = [keywords[i : i + batch_size] for i in range(0, len(keywords), batch_size)]
    consecutive_429s = 0

    for batch_idx, batch in enumerate(batches):
        if consecutive_429s >= 3:
            break

        print(f"[Rising Queries] Batch {batch_idx + 1}/{len(batches)}: {batch}")

        for attempt in range(2):
            try:
                pytrends.build_payload(batch, cat=0, timeframe="today 3-m", geo="US")
                related = pytrends.related_queries()
                if related:
                    for kw in batch:
                        if kw not in related:
                            continue
                        kw_data = related[kw]
                        rising_list = _parse_df_to_list(kw_data.get("rising"))
                        top_list = _parse_df_to_list(kw_data.get("top"))
                        if rising_list or top_list:
                            results[kw] = {"rising": rising_list, "top": top_list}
                consecutive_429s = 0
                break

            except Exception as exc:
                if "429" in str(exc):
                    consecutive_429s += 1
                    wait = (30 * (2 ** attempt)) + random.randint(5, 30)
                    time.sleep(wait)
                    pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
                else:
                    break

        if batch_idx < len(batches) - 1:
            delay = 20 + random.randint(5, 15)
            time.sleep(delay)

    return results


# ---------------------------------------------------------------------------
# DataFrame parser helper
# ---------------------------------------------------------------------------

def _parse_df_to_list(df_or_none) -> list[dict[str, Any]]:
    """Convert a pandas DataFrame of related queries to a list of dicts."""
    if df_or_none is None:
        return []
    try:
        if hasattr(df_or_none, "empty") and df_or_none.empty:
            return []
        items = []
        for _, row in df_or_none.iterrows():
            value = row.get("value", 0)
            if isinstance(value, str) and value.lower() == "breakout":
                value = "Breakout"
            else:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    value = 0
            items.append({"query": str(row.get("query", "")), "value": value})
        return items
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Public API — same signatures as before, drop-in replacement
# ---------------------------------------------------------------------------

def collect_google_trends(
    keywords_flat: list[str],
    use_cache: bool = False,
) -> dict[str, dict[str, Any]] | None:
    """Collect Google Trends interest-over-time data.

    Multi-layer resilience:
      1. Try trendspy (or pytrends as fallback)
      2. On 429 — exponential backoff with jitter, accept partial results
      3. On total failure — serve from 12h cache
      4. On cache miss — serve from stale cache (any age)

    Args:
        keywords_flat: Keywords to query.
        use_cache: If True, skip live fetch and serve cached data only.

    Returns:
        Dict mapping keyword -> metrics, or None on total failure.
    """
    if not keywords_flat:
        print("[Google Trends] No keywords provided.")
        return None

    if _ENGINE is None:
        print(
            "[Google Trends] Neither trendspy nor pytrends installed. "
            "Install with: pip install trendspy"
        )
        return _load_stale_cache(_CACHE_TRENDS)

    # Cache-only mode (for testing without hitting Google)
    if use_cache:
        cached = _load_cache(_CACHE_TRENDS)
        if cached:
            return cached
        return _load_stale_cache(_CACHE_TRENDS)

    # Check fresh cache first — avoids redundant requests during testing
    cached = _load_cache(_CACHE_TRENDS)
    if cached:
        return cached

    # Live fetch
    print(f"[Google Trends] Using {_ENGINE} engine for {len(keywords_flat)} keywords")

    if _ENGINE == "trendspy":
        results = _fetch_trendspy(keywords_flat)
    else:
        results = _fetch_pytrends(keywords_flat)

    if results:
        _save_cache(_CACHE_TRENDS, results)
        print(f"[Google Trends] Collected data for {len(results)}/{len(keywords_flat)} keywords.")
        return results

    # Fallback: stale cache
    stale = _load_stale_cache(_CACHE_TRENDS)
    if stale:
        return stale

    print("[Google Trends] No results collected and no cache available.")
    return None


def collect_rising_queries(
    keywords_flat: list[str],
    use_cache: bool = False,
) -> dict[str, dict[str, list[dict[str, Any]]]] | None:
    """Collect rising and top related queries for each keyword.

    Same multi-layer resilience as collect_google_trends.

    Args:
        keywords_flat: Keywords to query.
        use_cache: If True, serve cached data only.

    Returns:
        Dict mapping keyword -> {rising: [...], top: [...]}, or None.
    """
    if not keywords_flat:
        return None

    if _ENGINE is None:
        return _load_stale_cache(_CACHE_RISING)

    if use_cache:
        cached = _load_cache(_CACHE_RISING)
        if cached:
            return cached
        return _load_stale_cache(_CACHE_RISING)

    cached = _load_cache(_CACHE_RISING)
    if cached:
        return cached

    print(f"[Rising Queries] Using {_ENGINE} engine")

    if _ENGINE == "trendspy":
        results = _fetch_rising_trendspy(keywords_flat)
    else:
        results = _fetch_rising_pytrends(keywords_flat)

    if results:
        _save_cache(_CACHE_RISING, results)
        print(f"[Rising Queries] Collected queries for {len(results)} keywords.")
        return results

    stale = _load_stale_cache(_CACHE_RISING)
    if stale:
        return stale

    print("[Rising Queries] No results and no cache available.")
    return None
