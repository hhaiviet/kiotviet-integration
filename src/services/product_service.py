"""Product export service."""

from __future__ import annotations

import csv
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from tqdm import tqdm

from src.api.client import KiotVietClient
from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.services.token_service import TokenService
from src.utils.config import config
from src.utils.logger import logger


DEFAULT_PRODUCT_FIELDS: Sequence[str] = (
    "Id",
    "ProductId",
    "MasterCode",
    "Code",
    "Barcode",
    "Name",
    "FullName",
    "CategoryName",
    "CategoryNameTree",
    "BasePrice",
    "Cost",
    "LatestPurchasePrice",
    "OnHand",
    "OnOrder",
    "ProductImage",
    "CreatedDate",
)


@dataclass
class ProductExportResult:
    """Execution summary for a product export run."""

    products: int
    output_file: Path
    duration_seconds: float


class ProductService:
    """Fetch products from KiotViet API and export them to CSV."""

    def __init__(
        self,
        client: Optional[KiotVietClient] = None,
        token_service: Optional[TokenService] = None,
    ) -> None:
        api_cfg = config.get("api", {})
        product_cfg = config.get("products", {})
        data_cfg = config.get("data", {})
        credentials_cfg = config.get("credentials", {})

        base_url = api_cfg.get("base_url", "https://api-man1.kiotviet.vn/api")
        timeout = int(api_cfg.get("timeout", 30))
        max_retries = int(api_cfg.get("max_retries", 3))
        page_size = int(product_cfg.get("page_size", api_cfg.get("page_size", 100)))

        self.client = client or KiotVietClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=0.5,
        )

        token_path = credentials_cfg.get("token_file", "data/credentials/token.json")
        self.token_service = token_service or TokenService(token_path)

        output_dir = Path(data_cfg.get("output_dir", "data/output"))
        output_file = product_cfg.get("output_file", "master_products.csv")
        self.output_path = Path(output_file)
        if not self.output_path.is_absolute():
            self.output_path = output_dir / self.output_path

        self.page_size = page_size
        self._logger = logger.getChild(self.__class__.__name__)

    def export(
        self,
        *,
        page_size: Optional[int] = None,
        fields: Sequence[str] = DEFAULT_PRODUCT_FIELDS,
        output_file: Optional[Path] = None,
    ) -> ProductExportResult:
        """Fetch products and export them to CSV."""
        credentials = self.token_service.load()
        headers = TokenService.build_headers(credentials)
        page_size = int(page_size or self.page_size)
        if page_size <= 0:
            raise ConfigurationError("page_size must be positive")
        if page_size > 1000:
            raise ConfigurationError("page_size cannot exceed 1000")

        output_path = Path(output_file) if output_file else self.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        self._logger.info(
            "Starting product export | page_size=%s | output=%s",
            page_size,
            output_path,
        )

        products = self._fetch_all_products(credentials.branch_id, headers, page_size)
        self._write_csv(products, output_path, fields)

        duration = time.time() - start_time
        self._logger.info(
            "Product export finished | products=%s | duration=%.1fs",
            len(products),
            duration,
        )

        return ProductExportResult(
            products=len(products),
            output_file=output_path,
            duration_seconds=duration,
        )

    def _fetch_all_products(
        self,
        branch_id: int,
        headers: Dict[str, str],
        page_size: int,
    ) -> List[Dict[str, object]]:
        total = self._fetch_total_products(branch_id, headers)
        if total == 0:
            return []

        products: List[Dict[str, object]] = []
        total_pages = max(1, math.ceil(total / page_size))
        progress = tqdm(
            range(total_pages),
            desc="Products",
            unit="page",
            leave=False,
        )

        for index in progress:
            skip = index * page_size
            page_data = self._fetch_product_page(branch_id, headers, skip, page_size)
            items = page_data.get("Data", []) if isinstance(page_data, dict) else []
            if not isinstance(items, list):
                raise KiotVietAPIError("Unexpected payload while fetching products")
            if not items:
                break
            products.extend(items)
            progress.set_postfix(fetched=len(products))

        progress.close()
        return products

    def _fetch_total_products(
        self,
        branch_id: int,
        headers: Dict[str, str],
    ) -> int:
        response = self._perform_master_product_request(
            branch_id=branch_id,
            headers=headers,
            skip=0,
            take=1,
        )
        total = response.get("TotalProduct", 0) if isinstance(response, dict) else 0
        if isinstance(total, int):
            return total
        raise ConfigurationError("Unexpected total product value")

    def _fetch_product_page(
        self,
        branch_id: int,
        headers: Dict[str, str],
        skip: int,
        take: int,
    ) -> Dict[str, object]:
        return self._perform_master_product_request(
            branch_id=branch_id,
            headers=headers,
            skip=skip,
            take=take,
        )

    def _perform_master_product_request(
        self,
        *,
        branch_id: int,
        headers: Dict[str, str],
        skip: int,
        take: int,
    ) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "Id": branch_id,
            "Skip": skip,
            "Take": take,
            "Includes": ["ProductAttributes"],
            "ForSummaryRow": True,
            "IsActive": True,
            "IsNewFilter": True,
        }

        return self.client.post(
            f"/branchs/{branch_id}/masterproducts",
            headers=headers,
            params={
                "format": "json",
                "Includes": "ProductAttributes",
                "ForSummaryRow": "true",
            },
            json_payload=payload,
        )

    def _write_csv(
        self,
        products: List[Dict[str, object]],
        output_path: Path,
        fields: Sequence[str],
    ) -> None:
        if not products:
            self._logger.warning("No products returned from API")
            return

        try:
            with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(fields))
                writer.writeheader()
                for product in products:
                    row = {field: product.get(field, "") for field in fields}
                    writer.writerow(row)
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot write product export file {output_path}: {exc}"
            ) from exc
