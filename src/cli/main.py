"""Main CLI entry point"""

import click
from src.cli.commands import auth, sync, export

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """KiotViet Integration CLI Tool"""
    pass

cli.add_command(auth.auth_group)
cli.add_command(sync.sync_group)
cli.add_command(export.export_group)

if __name__ == "__main__":
    cli()
