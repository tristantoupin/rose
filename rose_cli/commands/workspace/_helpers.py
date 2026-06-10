from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click

from rose_cli.config import config_exists, expand_path, read_config


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


def open_cursor(ws_file: Path) -> None:
    cursor_bin = shutil.which("cursor")
    if not cursor_bin:
        click.echo("  ⚠  'cursor' not found in PATH. Open manually:")
        click.echo(f"     cursor {ws_file}")
        return
    subprocess.Popen([cursor_bin, str(ws_file)])
    click.echo("  ✓  Opening in Cursor...")
