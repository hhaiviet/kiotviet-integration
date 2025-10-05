"""Sync commands."""

import click

from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services import InvoiceService


@click.group(name="sync")
def sync_group() -> None:
    """Data synchronization."""


@sync_group.command()
@click.option(
    "--incremental/--full",
    default=True,
    help="Run incremental sync (default) or full sync ignoring checkpoint.",
)
def invoices(incremental: bool) -> None:
    """Sync invoice data."""
    service = InvoiceService()
    try:
        result = service.sync(incremental=incremental)
    except (ConfigurationError, KiotVietAPIError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        "Invoice sync completed: "
        f"invoices={result.invoices}"
        f" lines={result.lines}"
        f" duration={result.duration_seconds:.1f}s"
        f" output={result.output_file}"
    )
    if result.newest_purchase_date:
        click.echo(f"Newest purchase date: {result.newest_purchase_date}")
    click.echo(
        "Checkpoint updated" if result.checkpoint_updated else "Checkpoint unchanged"
    )
