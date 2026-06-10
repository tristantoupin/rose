import click

from rose_cli.commands.org.set import set_org_cmd


@click.group()
def org() -> None:
    """Manage GitHub organization config."""


org.add_command(set_org_cmd, name="set")
