import click

from rose_cli.commands.workspace.create import create
from rose_cli.commands.workspace.edit import edit
from rose_cli.commands.workspace.list import list_cmd
from rose_cli.commands.init import init
from rose_cli.commands.org import org
from rose_cli.commands.repos import repos


@click.group()
def cli() -> None:
    """Rose CLI root command."""


cli.add_command(init)
cli.add_command(org)
cli.add_command(repos)
cli.add_command(create)
cli.add_command(edit)
cli.add_command(list_cmd, name="list")


@cli.command()
def hello() -> None:
    """Print bootstrap greeting."""
    click.echo("Hello from rose!")


if __name__ == "__main__":
    cli()
