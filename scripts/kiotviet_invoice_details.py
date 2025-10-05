from __future__ import annotations

"""CLI wrapper for invoice synchronization."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services import InvoiceService
from src.utils.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch invoice details from KiotViet and write them to CSV."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run a full sync (ignore existing checkpoint).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = InvoiceService()

    try:
        result = service.sync(incremental=not args.full)
    except (ConfigurationError, KiotVietAPIError) as exc:
        logger.error("Invoice sync failed: %s", exc)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during invoice sync: %s", exc)
        sys.exit(1)

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


if __name__ == "__main__":
    main()
