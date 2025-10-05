from __future__ import annotations

"""Run invoice sync and product export in one go."""

import argparse
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services import InvoiceService, ProductService
from src.utils.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run invoice synchronization and product export sequentially.",
    )
    parser.add_argument(
        "--full-invoice",
        action="store_true",
        help="Run invoice sync in full mode (ignore checkpoint).",
    )
    parser.add_argument(
        "--product-page-size",
        type=int,
        help="Override page size for product export.",
    )
    parser.add_argument(
        "--product-output",
        type=Path,
        help="Optional custom output file for product export.",
    )
    parser.add_argument(
        "--skip-invoice",
        action="store_true",
        help="Skip invoice synchronization.",
    )
    parser.add_argument(
        "--skip-product",
        action="store_true",
        help="Skip product export.",
    )
    return parser.parse_args()


def run_invoice(full: bool) -> None:
    service = InvoiceService()
    result = service.sync(incremental=not full)

    print(
        "Invoice sync completed:"
        f" invoices={result.invoices}"
        f" lines={result.lines}"
        f" duration={result.duration_seconds:.1f}s"
        f" output={result.output_file}"
    )
    if result.newest_purchase_date:
        print(f"Newest purchase date: {result.newest_purchase_date}")
    print(
        "Checkpoint updated" if result.checkpoint_updated else "Checkpoint unchanged"
    )


def run_product(page_size: Optional[int], output: Optional[Path]) -> None:
    service = ProductService()
    result = service.export(page_size=page_size, output_file=output)

    print(
        "Product export completed:"
        f" products={result.products}"
        f" duration={result.duration_seconds:.1f}s"
        f" output={result.output_file}"
    )


def main() -> None:
    args = parse_args()

    if args.skip_invoice and args.skip_product:
        print("Nothing to do: both invoice and product steps are skipped.")
        return

    try:
        if not args.skip_invoice:
            logger.info("Starting invoice synchronization")
            run_invoice(full=args.full_invoice)
        else:
            logger.info("Invoice sync skipped by flag")

        if not args.skip_product:
            logger.info("Starting product export")
            run_product(
                page_size=args.product_page_size,
                output=args.product_output,
            )
        else:
            logger.info("Product export skipped by flag")

    except (ConfigurationError, KiotVietAPIError, ValueError) as exc:
        logger.error("Run failed: %s", exc)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - unexpected
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
