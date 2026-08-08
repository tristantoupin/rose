from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import click

from rose_cli.ascii import ROSE_GREETING
from rose_cli.cache import save_repo_cache
from rose_cli.config import CONFIG_PATH, config_exists, expand_path, write_config
from rose_cli import github

DEFAULT_WORKSPACE = "~/workspaces"
DEFAULT_TEMPLATE = "~/.rose/templates/default"
DEFAULT_GITHUB_ORG = ""


def check_github_cli() -> bool:
    """Check gh CLI installation and auth. Returns True if fully authed."""
    if not shutil.which("gh"):
        click.echo("  ⚠  GitHub CLI not found. Install it: https://cli.github.com")
        return False

    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo("  ⚠  GitHub CLI not authenticated. Run: gh auth login")
        return False

    click.echo("  ✓  GitHub CLI authenticated")
    return True


def scaffold_template(template_path: Path) -> None:
    """Create default workspace template with empty docs folder."""
    docs_dir = template_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / ".gitkeep").write_text("")


@click.command()
def init() -> None:
    """Initialize Rose environment."""
    click.echo(ROSE_GREETING)

    # GitHub CLI check
    click.echo("Checking prerequisites...")
    gh_ok = check_github_cli()
    click.echo()

    # Existing config check
    if config_exists():
        click.echo(f"  ⚠  Config already exists at {CONFIG_PATH}")
        if not click.confirm("  Overwrite?", default=False):
            click.echo("  Aborted.")
            return
        click.echo()

    # Workspace path
    raw_workspace = click.prompt(
        "Where should worktrees live?",
        default=DEFAULT_WORKSPACE,
    )
    workspace_path = expand_path(raw_workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"  ✓  Workspace directory ready: {workspace_path}")
    click.echo()

    # Template path
    raw_template = click.prompt(
        "Workspace template path",
        default=DEFAULT_TEMPLATE,
    )
    template_path = expand_path(raw_template)
    if template_path.is_dir():
        click.echo(f"  ✓  Using existing template: {template_path}")
    else:
        scaffold_template(template_path)
        click.echo(f"  ✓  Default template created: {template_path}")
    click.echo()

    # GitHub org
    org = click.prompt(
        "GitHub organization name",
        default=DEFAULT_GITHUB_ORG,
    )
    click.echo()

    # Write config
    write_config(str(workspace_path), str(template_path), org)
    click.echo(f"  ✓  Config saved to {CONFIG_PATH}")

    # Build initial repo cache
    click.echo(f"  Fetching repo list for {org}...")
    try:
        repo_names = github.repo_list(org)
        save_repo_cache(org, repo_names)
        click.echo(f"  ✓  {len(repo_names)} repos cached")
    except RuntimeError as exc:
        click.echo(f"  ⚠  Could not fetch repos: {exc}")
        click.echo("     Run 'rose repos sync' later to build the cache.")
    click.echo()

    # Summary
    click.echo("─" * 50)
    click.echo(f"  ✓  Workspace path:  {workspace_path}")
    click.echo(f"  ✓  Template path:   {template_path}")
    click.echo(f"  ✓  GitHub org:      {org}")
    if not gh_ok:
        click.echo("  ⚠  GitHub CLI needs attention (see above)")
    click.echo()
    click.echo("  All set! Rose is ready to grow! 🌹")
