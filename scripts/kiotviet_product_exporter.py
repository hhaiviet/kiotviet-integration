from __future__ import annotations

"""CLI wrapper for KiotViet product export."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services import ProductService
from src.utils.logger import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export master products from KiotViet to CSV."
    )
    parser.add_argument(
        "--page-size",
        type=int,
        help="Number of products per API page (defaults to config).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path (defaults to config setting).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = ProductService()

    try:
        result = service.export(
            page_size=args.page_size,
            output_file=args.output,
        )
    except (ConfigurationError, KiotVietAPIError) as exc:
        logger.error("Product export failed: %s", exc)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error during product export: %s", exc)
        sys.exit(1)

    print(
        "Product export completed:"
        f" products={result.products}"
        f" duration={result.duration_seconds:.1f}s"
        f" output={result.output_file}"
    )


if __name__ == "__main__":
    main()
