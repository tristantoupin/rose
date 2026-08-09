import click

from rose_cli.commands.vault.set import set_vault_cmd


@click.group()
def vault() -> None:
    """Manage the persistent docs vault config."""


vault.add_command(set_vault_cmd, name="set")
