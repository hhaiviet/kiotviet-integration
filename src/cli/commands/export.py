"""Export commands."""

from pathlib import Path

import click

from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services import ProductService


@click.group(name="export")
def export_group() -> None:
    """Data export."""


@export_group.command()
@click.option(
    "--format",
    type=click.Choice(["csv"], case_sensitive=False),
    default="csv",
    help="Export format (currently only CSV).",
)
@click.option(
    "--page-size",
    type=int,
    help="Page size override when fetching products.",
)
@click.option(
    "--output",
    type=click.Path(path_type=str),
    help="Optional output path for the exported file.",
)
def products(format: str, page_size: int, output: str) -> None:
    """Export product data."""
    if format.lower() != "csv":
        raise click.ClickException("Only CSV export is supported at the moment.")

    service = ProductService()
    output_path = Path(output) if output else None

    try:
        result = service.export(
            page_size=page_size,
            output_file=output_path,
        )
    except (ConfigurationError, KiotVietAPIError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(
        "Product export completed: "
        f"products={result.products}"
        f" duration={result.duration_seconds:.1f}s"
        f" output={result.output_file}"
    )
