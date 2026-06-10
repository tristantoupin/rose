from __future__ import annotations

import subprocess
from pathlib import Path

from rose_cli.config import ROSE_HOME

BARE_REPOS_DIR = ROSE_HOME / "repos"


# ── path helpers ──────────────────────────────────────────────────────────────

def bare_clone_path(full_name: str) -> Path:
    """~/.rose/repos/org__repo.git"""
    safe = full_name.replace("/", "__")
    return BARE_REPOS_DIR / f"{safe}.git"


def repo_name_from_full(full_name: str) -> str:
    """'myorg/my-repo' → 'my-repo'"""
    return full_name.split("/")[-1]


# ── git operations ────────────────────────────────────────────────────────────

def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def clone_bare(ssh_url: str, bare_path: Path) -> None:
    """Clone a repo as a bare clone and fix the fetch refspec.

    git clone --bare maps refs/heads/* → refs/heads/* by default, so
    'origin/<branch>' refs never exist. Reconfigure to map into
    refs/remotes/origin/* so worktree creation can use origin/<branch>.
    """
    BARE_REPOS_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--bare", ssh_url, str(bare_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    # Fix refspec: bare clones default to refs/heads/*:refs/heads/* which
    # does not create refs/remotes/origin/* entries needed for worktree add.
    subprocess.run(
        [
            "git", "-C", str(bare_path),
            "config", "remote.origin.fetch",
            "+refs/heads/*:refs/remotes/origin/*",
        ],
        check=True,
    )


def fetch(bare_path: Path) -> None:
    """Fetch + prune a bare clone into refs/remotes/origin/*."""
    _git(bare_path, "fetch", "--prune", "origin")


def branch_exists(bare_path: Path, branch_name: str) -> bool:
    """Return True if branch_name exists in the bare clone."""
    output = _git(bare_path, "branch", "--list", branch_name)
    return bool(output.strip())


def add_worktree(bare_path: Path, worktree_path: Path, branch: str, from_ref: str) -> None:
    """Create a new worktree at worktree_path on a new branch from from_ref."""
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _git(bare_path, "worktree", "add", str(worktree_path), "-b", branch, from_ref)


def worktree_status(worktree_path: Path) -> dict:
    """Return status info for a live worktree.

    Returns:
        {
          "branch": str,     # current branch name (or "(detached)")
          "ahead": int,      # commits ahead of upstream
          "behind": int,     # commits behind upstream
          "modified": int,   # staged + unstaged changed files
          "untracked": int,  # untracked files
        }
    """
    branch = _git(worktree_path, "rev-parse", "--abbrev-ref", "HEAD")

    ahead = behind = 0
    try:
        lr = _git(worktree_path, "rev-list", "--count", "--left-right", "@{upstream}...HEAD")
        parts = lr.split("\t")
        if len(parts) == 2:
            behind, ahead = int(parts[0]), int(parts[1])
    except RuntimeError:
        pass

    status_output = _git(worktree_path, "status", "--porcelain")
    modified = untracked = 0
    for line in status_output.splitlines():
        if line.startswith("??"):
            untracked += 1
        elif line.strip():
            modified += 1

    return {
        "branch": branch,
        "ahead": ahead,
        "behind": behind,
        "modified": modified,
        "untracked": untracked,
    }


def remove_worktree(bare_path: Path, worktree_path: Path, force: bool = False) -> None:
    """Remove a worktree via the bare clone."""
    args = ["worktree", "remove", str(worktree_path)]
    if force:
        args.append("--force")
    _git(bare_path, *args)


def prune_worktrees(bare_path: Path) -> None:
    """Prune stale worktree entries from a bare clone."""
    _git(bare_path, "worktree", "prune")
