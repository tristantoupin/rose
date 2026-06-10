from __future__ import annotations

import json
import shutil
from pathlib import Path

import click
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from rose_cli import git, github
from rose_cli.cache import get_cached_repos, load_history, save_repo_cache, update_history
from rose_cli.commands.workspace._helpers import load_and_validate_config, open_cursor
from rose_cli.commands.workspace.create import (
    _SEARCH_SENTINEL,
    _ensure_bare_clones,
    _run_search_picker,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _find_workspace(workspace_root: Path, name: str) -> tuple[Path, dict, Path]:
    """Return (workspace_dir, code_workspace_data, ws_file) or abort."""
    for ws_dir in sorted(workspace_root.iterdir()):
        if not ws_dir.is_dir():
            continue
        ws_files = list(ws_dir.glob("*.code-workspace"))
        if not ws_files:
            continue
        ws_file = ws_files[0]
        try:
            data = json.loads(ws_file.read_text())
        except Exception:
            continue
        if data.get("rose", {}).get("name") == name:
            return ws_dir, data, ws_file
    click.echo(f"  ✗  Workspace '{name}' not found in {workspace_root}")
    raise SystemExit(1)


def _infer_workspace_from_cwd(workspace_root: Path) -> str | None:
    """Infer workspace name from current directory when inside workspace root."""
    workspace_root_resolved = workspace_root.resolve()
    cwd = Path.cwd().resolve()

    for candidate in (cwd, *cwd.parents):
        if candidate.parent != workspace_root_resolved:
            continue

        ws_files = sorted(candidate.glob("*.code-workspace"))
        if not ws_files:
            continue

        for ws_file in ws_files:
            try:
                data = json.loads(ws_file.read_text())
            except Exception:
                continue
            name = data.get("rose", {}).get("name")
            if isinstance(name, str) and name:
                return name
    return None


def _pick_repos_for_edit(
    all_repos: list[str],
    current_repos: list[str],
    org: str,
) -> list[str]:
    recent = load_history()
    recent_set = set(recent)
    current_set = set(current_repos)

    # Build choices with current repos pre-selected via enabled=True.
    # InquirerPy's `default` on a fuzzy prompt sets filter text, not selection.
    choices: list[Choice] = [
        Choice(value=r, name=f"★  {r}", enabled=(r in current_set))
        for r in recent if r in set(all_repos)
    ]
    choices += [
        Choice(value=r, name=r, enabled=(r in current_set))
        for r in all_repos if r not in recent_set
    ]
    choices.append(Choice(value=_SEARCH_SENTINEL, name=_SEARCH_SENTINEL))

    selected = inquirer.fuzzy(
        message="Select repos (space to mark, enter to confirm):",
        choices=choices,
        multiselect=True,
        validate=lambda result: len([r for r in result if r != _SEARCH_SENTINEL]) > 0,
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
        merged = list(dict.fromkeys(all_repos + extra))
        save_repo_cache(org, merged)

    return final


def _check_removal_safety(
    workspace_dir: Path,
    removed: list[str],
    force: bool,
) -> None:
    blocked: list[tuple[str, dict]] = []
    for full_name in removed:
        repo_short = git.repo_name_from_full(full_name)
        worktree_path = workspace_dir / "repos" / repo_short
        if not worktree_path.exists():
            continue
        try:
            status = git.worktree_status(worktree_path)
        except RuntimeError:
            continue
        if status["modified"] > 0 or status["untracked"] > 0 or status["ahead"] > 0:
            blocked.append((repo_short, status))

    if blocked and not force:
        click.echo("  ✗  Cannot remove repos — they have uncommitted or unpushed work:")
        for repo_short, status in blocked:
            parts = []
            if status["modified"] > 0:
                parts.append(f"{status['modified']} modified")
            if status["untracked"] > 0:
                parts.append(f"{status['untracked']} untracked")
            if status["ahead"] > 0:
                n = status["ahead"]
                parts.append(f"{n} unpushed commit{'s' if n != 1 else ''}")
            click.echo(f"     {repo_short:<20} {', '.join(parts)}")
        click.echo("  Run with --force to remove anyway (changes will be lost).")
        raise SystemExit(1)


# ── command ───────────────────────────────────────────────────────────────────

@click.command()
@click.argument("name", required=False, default=None)
@click.option("--force", is_flag=True, help="Skip uncommitted/unpushed safety checks on removed repos.")
def edit(name: str | None, force: bool) -> None:
    """Add or remove repos from an existing active workspace."""
    workspace_root, _, org = load_and_validate_config()

    if name is None:
        name = _infer_workspace_from_cwd(workspace_root)
        if name is None:
            click.echo("  ✗  No workspace name given and cwd is not inside a workspace.")
            click.echo("     Usage: rose workspace edit <name>")
            raise SystemExit(1)
        click.echo(f"  ✓  Inferred workspace: {name}")
        click.echo()

    workspace_dir, data, ws_file = _find_workspace(workspace_root, name)

    if data.get("rose", {}).get("status") == "inactive":
        click.echo(
            f"  ✗  Workspace '{name}' is inactive. "
            f"Run 'rose workspace reactivate {name}' first."
        )
        raise SystemExit(1)

    current_repos: list[str] = list(data.get("rose", {}).get("repos", {}).keys())
    branch = next(iter(data["rose"]["repos"].values()))["branch"] if current_repos else name

    click.echo(f"Editing workspace: {name}")
    click.echo()
    short_names = [git.repo_name_from_full(r) for r in current_repos]
    click.echo(f"  Current repos: {', '.join(short_names) or '(none)'}")
    click.echo()

    # Ensure repo cache
    all_repos = get_cached_repos(org)
    if all_repos is None:
        click.echo(f"  Fetching repo list for {org}...")
        try:
            all_repos = github.repo_list(org)
            save_repo_cache(org, all_repos)
            click.echo(f"  ✓  {len(all_repos)} repos cached")
        except RuntimeError as exc:
            click.echo(f"  ✗  Failed to fetch repos: {exc}")
            raise SystemExit(1)
        click.echo()

    new_repos = _pick_repos_for_edit(all_repos, current_repos, org)
    click.echo()

    current_set = set(current_repos)
    new_set = set(new_repos)
    added = [r for r in new_repos if r not in current_set]
    removed = [r for r in current_repos if r not in new_set]

    if not added and not removed:
        click.echo("  No changes.")
        return

    # Safety check on removals
    _check_removal_safety(workspace_dir, removed, force)

    added_default_branches: dict[str, str] = {}

    # Process removals
    if removed:
        click.echo("  Removing repos...")
        for full_name in removed:
            repo_short = git.repo_name_from_full(full_name)
            worktree_path = workspace_dir / "repos" / repo_short
            bare_path = git.bare_clone_path(full_name)
            if worktree_path.exists():
                try:
                    git.remove_worktree(bare_path, worktree_path, force=force)
                    shutil.rmtree(worktree_path, ignore_errors=True)
                    try:
                        git.prune_worktrees(bare_path)
                    except RuntimeError:
                        pass
                    click.echo(f"  ✓  {repo_short:<20} removed")
                except RuntimeError as exc:
                    click.echo(f"  ✗  {repo_short}: {exc}")
                    raise SystemExit(1)
            else:
                click.echo(f"  ⚠  {repo_short:<20} (already removed)")
        click.echo()

    # Process additions
    if added:
        click.echo("  Adding repos...")
        _ensure_bare_clones(added)
        repos_dir = workspace_dir / "repos"
        repos_dir.mkdir(parents=True, exist_ok=True)
        for full_name in added:
            repo_short = git.repo_name_from_full(full_name)
            bare_path = git.bare_clone_path(full_name)
            worktree_path = repos_dir / repo_short
            try:
                default_br = github.default_branch(full_name)
            except RuntimeError:
                default_br = "main"
            added_default_branches[full_name] = default_br
            from_ref = f"origin/{default_br}"
            try:
                git.add_worktree(bare_path, worktree_path, branch, from_ref)
                click.echo(f"  ✓  {repo_short:<20} added → {branch}")
            except RuntimeError as exc:
                click.echo(f"  ✗  {repo_short}: {exc}")
                raise SystemExit(1)
        click.echo()

    # Update .code-workspace
    final_repos = [r for r in current_repos if r in new_set] + added
    updated_repos_meta: dict[str, dict] = {}
    for r in final_repos:
        if r in data["rose"]["repos"]:
            updated_repos_meta[r] = data["rose"]["repos"][r]
        else:
            updated_repos_meta[r] = {
                "branch": branch,
                "default_branch": added_default_branches.get(r, "main"),
            }
    data["rose"]["repos"] = updated_repos_meta
    data["folders"] = [
        {"path": f"repos/{git.repo_name_from_full(r)}", "name": git.repo_name_from_full(r)}
        for r in final_repos
    ]
    data["folders"].append({"path": "docs", "name": "docs"})
    ws_file.write_text(json.dumps(data, indent=2))

    update_history(added)

    # Summary
    click.echo("─" * 50)
    click.echo(f"  ✓  {name} updated")
    short_final = ", ".join(git.repo_name_from_full(r) for r in final_repos)
    click.echo(f"     Repos ({len(final_repos)}): {short_final}")
    click.echo()

    open_cursor(ws_file)
