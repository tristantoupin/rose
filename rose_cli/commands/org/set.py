from __future__ import annotations

import click

from rose_cli.cache import save_repo_cache
from rose_cli.config import config_exists, get_org, set_org
from rose_cli import github


@click.command()
@click.argument("orgname")
def set_org_cmd(orgname: str) -> None:
    """Set GitHub organization and rebuild repo cache."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)

    set_org(orgname)
    click.echo(f"  ✓  Org set to {orgname}")

    click.echo(f"  Fetching repo list for {orgname}...")
    try:
        repo_names = github.repo_list(orgname)
    except RuntimeError as exc:
        click.echo(f"  ✗  Failed to fetch repos: {exc}")
        raise SystemExit(1)

    save_repo_cache(orgname, repo_names)
    click.echo(f"  ✓  {len(repo_names)} repos cached")
