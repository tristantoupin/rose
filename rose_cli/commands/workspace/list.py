from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import click
from InquirerPy import inquirer

from rose_cli import git
from rose_cli.commands.workspace._helpers import load_and_validate_config, open_cursor


@dataclass
class WorkspaceInfo:
    name: str
    created: str
    repos: list[str]
    ws_file: Path
    workspace_path: Path


def _scan_workspaces(root: Path) -> list[WorkspaceInfo]:
    if not root.is_dir():
        return []

    results: list[WorkspaceInfo] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        ws_files = list(entry.glob("*.code-workspace"))
        if not ws_files:
            continue
        ws_file = ws_files[0]
        name = entry.name
        created = ""
        repos: list[str] = []
        try:
            data = json.loads(ws_file.read_text())
            rose = data.get("rose", {})
            name = rose.get("name", name)
            created = rose.get("created", "")
            repos = list(rose.get("repos", {}).keys())
        except Exception:
            pass
        results.append(
            WorkspaceInfo(
                name=name,
                created=created,
                repos=repos,
                ws_file=ws_file,
                workspace_path=entry,
            )
        )

    results.sort(key=lambda w: (w.created or "0000-00-00"), reverse=True)
    return results


def _build_label(info: WorkspaceInfo) -> str:
    short_repos = [git.repo_name_from_full(r) for r in info.repos]
    parts = [info.name]
    if short_repos:
        parts.append(f"[{', '.join(short_repos)}]")
    if info.created:
        parts.append(f"({info.created})")
    return "  ".join(parts)


def _pick_workspace(infos: list[WorkspaceInfo]) -> WorkspaceInfo | None:
    choices = [{"name": _build_label(i), "value": i} for i in infos]
    try:
        return inquirer.fuzzy(
            message="Select workspace:",
            choices=choices,
        ).execute()
    except KeyboardInterrupt:
        return None


@click.command("list")
def list_cmd() -> None:
    """List workspaces and open one in Cursor."""
    workspace_root, _, _ = load_and_validate_config()

    workspaces = _scan_workspaces(workspace_root)
    if not workspaces:
        click.echo(f"  No workspaces found in {workspace_root}.")
        return

    selected = _pick_workspace(workspaces)
    if selected is None:
        return

    open_cursor(selected.ws_file)
