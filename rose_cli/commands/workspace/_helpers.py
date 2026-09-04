from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click

from rose_cli.config import config_exists, expand_path, get_app, read_config


def load_and_validate_config() -> tuple[Path, Path, str]:
    """Return (workspace_path, template_path, org) or abort."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)

    config = read_config()
    org = config.get("github", {}).get("org", "")
    if not org:
        click.echo("  ✗  No GitHub org configured. Run 'rose org set <orgname>' first.")
        raise SystemExit(1)

    workspace_path = expand_path(config.get("workspace", {}).get("path", ""))
    template_path = expand_path(config.get("template", {}).get("path", ""))
    return workspace_path, template_path, org


def open_workspace(workspace_path: Path, ws_file: Path) -> None:
    """Open a Rose workspace in the configured development application."""
    try:
        app_name = get_app()
    except ValueError as exc:
        click.echo(f"  ✗  Invalid application configuration: {exc}")
        raise SystemExit(1)

    app_bin = shutil.which(app_name)
    if app_name == "cursor":
        args = [str(ws_file)]
        manual_command = f"{app_name} {ws_file}"
    else:
        args = ["app", str(workspace_path)]
        manual_command = f"{app_name} app {workspace_path}"

    if not app_bin:
        click.echo(f"  ⚠  '{app_name}' not found in PATH. Open manually:")
        click.echo(f"     {manual_command}")
        return

    try:
        subprocess.Popen([app_bin, *args])
    except OSError as exc:
        click.echo(f"  ⚠  Failed to open workspace in {app_name}: {exc}")
        return
    click.echo(f"  ✓  Opening workspace in {app_name}...")
