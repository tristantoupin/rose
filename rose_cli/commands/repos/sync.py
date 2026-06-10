from __future__ import annotations

import click

from rose_cli.cache import save_repo_cache
from rose_cli.config import config_exists, get_org
from rose_cli import github


@click.command()
def sync() -> None:
    """Rebuild the local repo cache from GitHub."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)

    org = get_org()
    if not org:
        click.echo("  ✗  No org configured. Run 'rose org set <orgname>' first.")
        raise SystemExit(1)

    click.echo(f"  Syncing repo list for {org}...")
    try:
        repo_names = github.repo_list(org)
    except RuntimeError as exc:
        click.echo(f"  ✗  Failed to fetch repos: {exc}")
        raise SystemExit(1)

    save_repo_cache(org, repo_names)
    click.echo(f"  ✓  Repo cache updated ({len(repo_names)} repos)")
