from __future__ import annotations

import click

from rose_cli.config import config_exists, expand_path, set_vault_path


@click.command()
@click.argument("path")
def set_vault_cmd(path: str) -> None:
    """Set the persistent docs vault path."""
    if not config_exists():
        click.echo("  ✗  No config found. Run 'rose init' first.")
        raise SystemExit(1)

    vault_path = expand_path(path)
    vault_path.mkdir(parents=True, exist_ok=True)
    set_vault_path(str(vault_path))
    click.echo(f"  ✓  Vault path set to {vault_path}")
