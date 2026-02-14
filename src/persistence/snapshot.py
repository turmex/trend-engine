"""
Trend Engine V2.0 — Snapshot Persistence
====================================================
Save/load/diff weekly data snapshots as JSON in data/.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_snapshot(data: dict) -> Path:
    """
    Save this week's complete data to data/snapshot_YYYY-MM-DD.json.
    Auto-increments brief_number based on existing snapshots.
    Returns the path to the saved file.
    """
    ensure_data_dir()
    existing = sorted(DATA_DIR.glob("snapshot_*.json"))
    data["brief_number"] = len(existing) + 1
    data["version"] = "1.5"

    ts = datetime.now().strftime("%Y-%m-%d")
    path = DATA_DIR / f"snapshot_{ts}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Snapshot saved: {path.name} (Brief #{data['brief_number']})")
    return path


def load_latest_snapshot() -> Optional[dict]:
    """
    Load the most recent prior snapshot.
    Returns None if no snapshots exist (first run).
    """
    ensure_data_dir()
    files = sorted(DATA_DIR.glob("snapshot_*.json"), reverse=True)
    if not files:
        return None
    try:
        with open(files[0]) as f:
            data = json.load(f)
        print(f"  Loaded prior snapshot: {files[0].name}")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Warning: Could not load snapshot {files[0].name}: {e}")
        return None


def load_snapshot_by_date(date_str: str) -> Optional[dict]:
    """Load a specific snapshot by date string (YYYY-MM-DD)."""
    path = DATA_DIR / f"snapshot_{date_str}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def get_brief_number() -> int:
    """Return the next brief number based on existing snapshots."""
    ensure_data_dir()
    return len(list(DATA_DIR.glob("snapshot_*.json"))) + 1


def list_snapshots() -> list[Path]:
    """List all snapshot files, newest first."""
    ensure_data_dir()
    return sorted(DATA_DIR.glob("snapshot_*.json"), reverse=True)


def save_html(html: str, filename: str = "latest_brief.html") -> Path:
    """Save the rendered HTML email for artifact upload and debugging."""
    ensure_data_dir()
    path = DATA_DIR / filename
    path.write_text(html, encoding="utf-8")
    print(f"  HTML saved: {path.name}")
    return path
