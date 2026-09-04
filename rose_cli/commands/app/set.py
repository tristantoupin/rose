from __future__ import annotations

import shutil

import click

from rose_cli.config import CONFIG_PATH, SUPPORTED_APPS, config_exists, set_app


@click.command()
@click.argument(
    "app_name",
    type=click.Choice(SUPPORTED_APPS, case_sensitive=False),
)
def set_app_cmd(app_name: str) -> None:
    """Set the global development application."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)

    app_name = app_name.lower()
    set_app(app_name)
    if not shutil.which(app_name):
        click.echo(f"  ⚠  '{app_name}' not found in PATH. You can install it later.")
    click.echo(f"  ✓  Application set to {app_name}")
    click.echo(f"  ✓  Config saved to {CONFIG_PATH}")
