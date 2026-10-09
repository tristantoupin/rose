from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import click

from rose_cli.config import config_exists, expand_path, get_app, read_config

# Longer than the t3 CLI's own desktop response timeout, so its error wins.
T3_OPEN_TIMEOUT_SECONDS = 30


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


def _path_is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def _materialize_external_folder(
    workspace_path: Path,
    folder: dict,
) -> None:
    raw_path = folder.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        return

    folder_path = Path(raw_path).expanduser()
    target = folder_path if folder_path.is_absolute() else workspace_path / folder_path
    if _path_is_inside(target, workspace_path):
        return

    folder_name = folder.get("name") or target.name
    if not isinstance(folder_name, str) or not folder_name or Path(folder_name).name != folder_name:
        click.echo(f"  ⚠  Cannot expose external workspace folder with name '{folder_name}'.")
        return

    if not target.is_dir():
        click.echo(f"  ⚠  Configured workspace folder does not exist: {target}")
        return

    link_path = workspace_path / folder_name
    if link_path.is_symlink():
        if link_path.resolve(strict=False) == target.resolve(strict=False):
            return
        click.echo(f"  ⚠  Not replacing existing workspace link: {link_path}")
        return
    if link_path.exists():
        click.echo(f"  ⚠  Not replacing existing workspace path: {link_path}")
        return

    try:
        link_path.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        click.echo(f"  ⚠  Could not link {target}: {exc}")
        return
    click.echo(f"  ✓  Linked folder:   {link_path} → {target}")


def _materialize_external_folders(workspace_path: Path, ws_file: Path) -> None:
    """Expose external workspace folders under the workspace root for directory-based apps."""
    try:
        data = json.loads(ws_file.read_text())
    except (OSError, json.JSONDecodeError):
        return

    for folder in data.get("folders", []):
        if isinstance(folder, dict):
            _materialize_external_folder(workspace_path, folder)


def _open_in_t3(
    app_bin: str,
    args: list[str],
    workspace_path: Path,
    manual_command: str,
) -> None:
    """Ask the running T3 Code desktop app to open the workspace and report the result."""
    try:
        result = subprocess.run(
            [app_bin, *args],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=T3_OPEN_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        reason = str(exc)
    else:
        if result.returncode == 0:
            click.echo("  ✓  Opened workspace in t3")
            return
        output = f"{result.stderr}\n{result.stdout}"
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        # t3 logs "<time> ERROR (#n): SomeError: <message>" followed by a stack trace.
        error_line = next((line for line in lines if "Error: " in line), lines[0] if lines else "")
        reason = error_line.partition("Error: ")[2] or error_line or f"exit code {result.returncode}"

    click.echo(f"  ⚠  t3 could not open the workspace: {reason}")
    click.echo("     Start the T3 Code desktop app, then run:")
    click.echo(f"     {manual_command}")


def open_workspace(workspace_path: Path, ws_file: Path) -> None:
    """Open a Rose workspace in the configured development application."""
    workspace_path = workspace_path.expanduser().resolve()
    ws_file = ws_file.expanduser().resolve()

    try:
        app_name = get_app()
    except ValueError as exc:
        click.echo(f"  ✗  Invalid application configuration: {exc}")
        raise SystemExit(1)

    if app_name in ("codex", "t3"):
        _materialize_external_folders(workspace_path, ws_file)

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

    if app_name == "t3":
        _open_in_t3(app_bin, args, workspace_path, manual_command)
        return

    try:
        subprocess.Popen([app_bin, *args], cwd=workspace_path)
    except OSError as exc:
        click.echo(f"  ⚠  Failed to open workspace in {app_name}: {exc}")
        return
    click.echo(f"  ✓  Opening workspace in {app_name}...")
