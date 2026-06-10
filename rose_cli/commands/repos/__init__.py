import click

from rose_cli.commands.repos.sync import sync


@click.group()
def repos() -> None:
    """Manage the local repo cache."""


repos.add_command(sync)
