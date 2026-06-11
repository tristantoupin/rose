from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from rose_cli import git, github
from rose_cli.cache import (
    get_cached_repos,
    load_history,
    save_repo_cache,
    update_history,
)
from rose_cli.commands.workspace._helpers import load_and_validate_config, open_cursor

_SEARCH_SENTINEL = "🔍  Not there? Search GitHub..."
_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


# ── helpers ───────────────────────────────────────────────────────────────────

def _ensure_repo_cache(org: str, force_refresh: bool) -> list[str]:
    if not force_refresh:
        cached = get_cached_repos(org)
        if cached is not None:
            return cached

    click.echo(f"  Fetching repo list for {org}...")
    try:
        repos = github.repo_list(org)
    except RuntimeError as exc:
        click.echo(f"  ✗  Failed to fetch repos: {exc}")
        raise SystemExit(1)

    save_repo_cache(org, repos)
    click.echo(f"  ✓  {len(repos)} repos cached")
    return repos


def _build_choices(recent: list[str], all_repos: list[str]) -> list[Choice]:
    """Recent repos first (★), then the rest, then the search sentinel."""
    recent_set = set(recent)
    choices = [Choice(value=r, name=f"★  {r}") for r in recent if r in set(all_repos)]
    choices += [Choice(value=r, name=r) for r in all_repos if r not in recent_set]
    choices.append(Choice(value=_SEARCH_SENTINEL, name=_SEARCH_SENTINEL))
    return choices


def _run_search_picker(org: str) -> list[str]:
    """Prompt for a search term, hit gh search, show secondary picker."""
    term = click.prompt("  Search term")
    click.echo(f"  Searching GitHub for '{term}' in {org}...")
    try:
        results = github.search_repos(term, org)
    except RuntimeError as exc:
        click.echo(f"  ✗  Search failed: {exc}")
        return []

    if not results:
        click.echo("  No results found.")
        return []

    picked = inquirer.fuzzy(
        message="Pick from search results:",
        choices=results,
        multiselect=True,
    ).execute()
    return picked or []


def _pick_repos(all_repos: list[str], org: str) -> list[str]:
    """Interactive fuzzy multiselect. Handles 'Not there?' sentinel."""
    recent = load_history()
    choices = _build_choices(recent, all_repos)

    selected = inquirer.fuzzy(
        message="Select repos (tab to mark, enter to confirm):",
        choices=choices,
        multiselect=True,
        validate=lambda result: (
            len([r for r in result if r != _SEARCH_SENTINEL]) > 0
        ),
        invalid_message="Select at least one repo",
    ).execute()

    final: list[str] = []
    needs_search = False
    for item in selected:
        if item == _SEARCH_SENTINEL:
            needs_search = True
        else:
            final.append(item)

    if needs_search:
        extra = _run_search_picker(org)
        for repo in extra:
            if repo not in final:
                final.append(repo)
        # Merge new search results into the cache
        merged = list(dict.fromkeys(all_repos + extra))
        save_repo_cache(org, merged)

    return final


def _check_branch_conflicts(repos: list[str], branch: str) -> None:
    """Abort if branch already exists in any bare clone."""
    for full_name in repos:
        bare_path = git.bare_clone_path(full_name)
        if bare_path.exists() and git.branch_exists(bare_path, branch):
            click.echo(
                f"\n  ✗  Branch '{branch}' already exists in {full_name}.\n"
                f"     Choose a different workspace name."
            )
            raise SystemExit(1)


def _ensure_bare_clones(repos: list[str]) -> None:
    """Clone (if missing) or fetch (if exists) bare clone for each repo."""
    for full_name in repos:
        bare_path = git.bare_clone_path(full_name)
        repo_short = git.repo_name_from_full(full_name)
        if bare_path.exists():
            click.echo(f"  Updating {repo_short}...")
            click.echo(f"    bare: {bare_path}")
            try:
                git.fetch(bare_path)
                click.echo(f"    fetched refs/remotes/origin/*")
            except RuntimeError as exc:
                click.echo(f"  ⚠  Fetch failed for {repo_short}: {exc}")
        else:
            click.echo(f"  Cloning {repo_short}...")
            try:
                url = github.ssh_url(full_name)
                click.echo(f"    url: {url}")
                click.echo(f"    dest: {bare_path}")
                git.clone_bare(url, bare_path)
                click.echo(f"    fixing fetch refspec → refs/remotes/origin/*")
                git.fetch(bare_path)
                click.echo(f"    fetched refs/remotes/origin/*")
            except RuntimeError as exc:
                click.echo(f"  ✗  Clone failed for {full_name}: {exc}")
                raise SystemExit(1)
        click.echo(f"  ✓  {repo_short} ready")


def _get_default_branches(repos: list[str]) -> dict[str, str]:
    """Return {full_name: default_branch} for each repo."""
    result: dict[str, str] = {}
    for full_name in repos:
        repo_short = git.repo_name_from_full(full_name)
        try:
            branch = github.default_branch(full_name)
            click.echo(f"  {repo_short}: default branch → {branch}")
            result[full_name] = branch
        except RuntimeError as exc:
            click.echo(f"  ⚠  Could not detect default branch for {repo_short}: {exc} (falling back to 'main')")
            result[full_name] = "main"
    return result


def _scaffold_template(workspace_path: Path, template_path: Path) -> None:
    """Copy template into workspace folder (skip if template missing)."""
    if not template_path.is_dir():
        return
    shutil.copytree(str(template_path), str(workspace_path), dirs_exist_ok=True)


def _create_worktrees(
    workspace_path: Path,
    repos: list[str],
    branch: str,
    default_branches: dict[str, str],
) -> None:
    repos_dir = workspace_path / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)
    for full_name in repos:
        repo_short = git.repo_name_from_full(full_name)
        bare_path = git.bare_clone_path(full_name)
        worktree_path = repos_dir / repo_short
        from_ref = f"origin/{default_branches.get(full_name, 'main')}"
        click.echo(f"  Creating worktree for {repo_short}...")
        click.echo(f"    bare:     {bare_path}")
        click.echo(f"    path:     {worktree_path}")
        click.echo(f"    branch:   {branch}")
        click.echo(f"    from ref: {from_ref}")
        try:
            git.add_worktree(bare_path, worktree_path, branch, from_ref)
        except RuntimeError as exc:
            click.echo(f"  ✗  Worktree failed for {repo_short}: {exc}")
            raise SystemExit(1)
        click.echo(f"  ✓  {repo_short} → {branch}")


def _write_code_workspace(
    workspace_path: Path,
    name: str,
    repos: list[str],
    branch: str,
    default_branches: dict[str, str],
) -> Path:
    folders = [
        {"path": f"repos/{git.repo_name_from_full(r)}", "name": git.repo_name_from_full(r)}
        for r in repos
    ]
    folders.append({"path": "docs", "name": "docs"})

    data = {
        "folders": folders,
        "settings": {},
        "rose": {
            "name": name,
            "created": date.today().isoformat(),
            "repos": {
                r: {
                    "branch": branch,
                    "default_branch": default_branches.get(r, "main"),
                }
                for r in repos
            },
        },
    }

    ws_file = workspace_path / f"{name}.code-workspace"
    ws_file.write_text(json.dumps(data, indent=2))
    return ws_file


# ── command ───────────────────────────────────────────────────────────────────

@click.command()
@click.option("--refresh", is_flag=True, help="Force repo cache refresh before selection.")
def create(refresh: bool) -> None:
    """Create a new multi-repo workspace."""
    workspace_root, template_path, org = load_and_validate_config()

    all_repos = _ensure_repo_cache(org, force_refresh=refresh)
    click.echo()

    # Workspace name
    while True:
        name = click.prompt("Workspace name")
        if not _NAME_RE.match(name):
            click.echo("  ✗  Name must contain only letters, numbers, hyphens, underscores.")
            continue
        target = workspace_root / name
        if target.exists():
            click.echo(f"  ✗  '{target}' already exists. Choose a different name.")
            continue
        break

    # Branch name
    branch = click.prompt("Feature branch name", default=name)
    click.echo()

    # Repo selection
    repos = _pick_repos(all_repos, org)
    if not repos:
        click.echo("  ✗  No repos selected. Aborted.")
        raise SystemExit(1)
    click.echo()

    # Branch conflict check
    _check_branch_conflicts(repos, branch)

    # Ensure bare clones
    _ensure_bare_clones(repos)
    click.echo()

    # Default branches
    default_branches = _get_default_branches(repos)

    # Create workspace folder + scaffold
    target.mkdir(parents=True)
    _scaffold_template(target, template_path)

    # Worktrees
    _create_worktrees(target, repos, branch, default_branches)
    click.echo()

    # .code-workspace
    ws_file = _write_code_workspace(target, name, repos, branch, default_branches)
    click.echo(f"  ✓  Workspace file: {ws_file}")

    # History
    update_history(repos)

    # Summary
    click.echo()
    click.echo("─" * 50)
    click.echo(f"  ✓  Workspace:  {target}")
    click.echo(f"  ✓  Branch:     {branch}")
    repo_names = ", ".join(git.repo_name_from_full(r) for r in repos)
    click.echo(f"  ✓  Repos ({len(repos)}): {repo_names}")
    click.echo()

    # Open Cursor
    open_cursor(ws_file)
