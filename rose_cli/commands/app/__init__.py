import click

from rose_cli.commands.app.set import set_app_cmd


@click.group()
def app() -> None:
    """Configure the development application."""


app.add_command(set_app_cmd, name="set")
