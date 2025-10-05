"""Authentication commands"""

import click

@click.group(name="auth")
def auth_group():
    """Authentication management"""
    pass

@auth_group.command()
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login(username, password):
    """Login and get access token"""
    click.echo(f"Logging in as {username}...")
    # TODO: Implement login logic
    click.echo("✅ Login successful!")
