from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rose_cli.config import ROSE_HOME

REPO_CACHE_PATH = ROSE_HOME / "repo-cache.json"
HISTORY_PATH = ROSE_HOME / "history.json"
CACHE_TTL_HOURS = 24
HISTORY_MAX = 20


# ── repo cache ────────────────────────────────────────────────────────────────

def load_repo_cache() -> dict:
    """Return parsed repo-cache.json or empty dict."""
    if not REPO_CACHE_PATH.is_file():
        return {}
    try:
        return json.loads(REPO_CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_repo_cache(org: str, repos: list[str]) -> None:
    ROSE_HOME.mkdir(parents=True, exist_ok=True)
    REPO_CACHE_PATH.write_text(
        json.dumps(
            {
                "org": org,
                "repos": repos,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


def cache_is_fresh(cache: dict, org: str) -> bool:
    """True if cache is for the given org and younger than CACHE_TTL_HOURS."""
    if not cache or cache.get("org") != org:
        return False
    cached_at_str = cache.get("cached_at", "")
    if not cached_at_str:
        return False
    try:
        cached_at = datetime.fromisoformat(cached_at_str)
        age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600
        return age_hours < CACHE_TTL_HOURS
    except ValueError:
        return False


def get_cached_repos(org: str) -> list[str] | None:
    """Return cached repo list if fresh for org, else None."""
    cache = load_repo_cache()
    if cache_is_fresh(cache, org):
        return cache.get("repos", [])
    return None


# ── history ───────────────────────────────────────────────────────────────────

def load_history() -> list[str]:
    """Return list of recently used repos (most recent first)."""
    if not HISTORY_PATH.is_file():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text())
        return data.get("recent_repos", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_history(repos: list[str]) -> None:
    ROSE_HOME.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps({"recent_repos": repos}, indent=2))


def update_history(selected_repos: list[str]) -> None:
    """Prepend selected repos to history, deduplicate, trim to HISTORY_MAX."""
    current = load_history()
    merged = selected_repos + [r for r in current if r not in selected_repos]
    save_history(merged[:HISTORY_MAX])
