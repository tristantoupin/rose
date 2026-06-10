from __future__ import annotations

import json
import subprocess


def _gh(*args: str) -> str:
    """Run a gh command, return stdout. Raises RuntimeError on failure."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh {' '.join(args)} failed")
    return result.stdout.strip()


def repo_list(org: str) -> list[str]:
    """Return all repo full names (org/repo) for the given org."""
    raw = _gh(
        "repo", "list", org,
        "--limit", "9999",
        "--json", "nameWithOwner",
    )
    data = json.loads(raw)
    return [item["nameWithOwner"] for item in data]


def search_repos(term: str, org: str) -> list[str]:
    """Search repos by name within org. Returns list of full names."""
    raw = _gh(
        "search", "repos",
        f"{term} in:name",
        "--owner", org,
        "--limit", "20",
        "--json", "fullName",
    )
    data = json.loads(raw)
    return [item["fullName"] for item in data]


def default_branch(full_name: str) -> str:
    """Return default branch name for a repo (e.g. 'main', 'master')."""
    return _gh(
        "repo", "view", full_name,
        "--json", "defaultBranchRef",
        "--jq", ".defaultBranchRef.name",
    )


def ssh_url(full_name: str) -> str:
    """Return SSH clone URL for a repo."""
    return _gh(
        "repo", "view", full_name,
        "--json", "sshUrl",
        "--jq", ".sshUrl",
    )


def repo_exists(full_name: str) -> bool:
    """Return True if the repo is accessible via gh."""
    try:
        _gh("repo", "view", full_name, "--json", "name")
        return True
    except RuntimeError:
        return False
