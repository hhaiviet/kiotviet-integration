"""Invoice synchronization service."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

from src.api.client import KiotVietClient
from src.api.exceptions import ConfigurationError, KiotVietAPIError
from src.models.credentials import AccessCredentials
from src.services.token_service import TokenService
from src.utils.config import config
from src.utils.logger import logger


INVOICE_HEADERS = [
    "InvoiceId",
    "InvoiceCode",
    "PurchaseDate",
    "ProductId",
    "ProductCode",
    "ProductName",
    "Quantity",
    "Price",
    "SubTotal",
]


@dataclass
class InvoiceSyncResult:
    """Execution summary for an invoice sync run."""

    invoices: int
    lines: int
    newest_purchase_date: Optional[str]
    output_file: Path
    duration_seconds: float
    incremental: bool
    checkpoint_updated: bool


class InvoiceService:
    """Fetch invoice details from KiotViet API and persist them to CSV."""

    def __init__(
        self,
        client: Optional[KiotVietClient] = None,
        token_service: Optional[TokenService] = None,
    ) -> None:
        api_cfg = config.get("api", {})
        invoice_cfg = config.get("invoices", {})
        data_cfg = config.get("data", {})
        credentials_cfg = config.get("credentials", {})

        base_url = api_cfg.get("base_url", "https://api-man1.kiotviet.vn/api")
        timeout = int(api_cfg.get("timeout", 30))
        max_retries = int(api_cfg.get("max_retries", 3))
        retry_delay = float(invoice_cfg.get("detail_retry_delay", 0.2))
        page_size = int(invoice_cfg.get("page_size", api_cfg.get("page_size", 100)))

        self.client = client or KiotVietClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        token_path = credentials_cfg.get("token_file", "data/credentials/token.json")
        self.token_service = token_service or TokenService(token_path)

        output_dir = Path(data_cfg.get("output_dir", "data/output"))
        checkpoint_dir = Path(data_cfg.get("checkpoint_dir", "data/checkpoints"))

        output_file = invoice_cfg.get("output_file", "invoice_details.csv")
        checkpoint_file = invoice_cfg.get("checkpoint_file", "invoices_checkpoint.json")

        self.output_path = Path(output_file)
        if not self.output_path.is_absolute():
            self.output_path = output_dir / self.output_path

        self.checkpoint_path = Path(checkpoint_file)
        if not self.checkpoint_path.is_absolute():
            self.checkpoint_path = checkpoint_dir / self.checkpoint_path

        self.page_size = page_size
        self.retry_delay = retry_delay
        self._logger = logger.getChild(self.__class__.__name__)

    def sync(self, incremental: bool = True) -> InvoiceSyncResult:
        """Run invoice synchronization."""
        credentials = self.token_service.load()
        headers = TokenService.build_headers(credentials)

        last_purchase_date = self._load_checkpoint() if incremental else None
        is_incremental_run = incremental and last_purchase_date is not None

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        file_mode = "a" if (is_incremental_run and self.output_path.exists()) else "w"
        total_invoices = 0
        total_lines = 0
        newest_purchase_date = last_purchase_date

        start_time = time.time()
        self._logger.info(
            "Starting invoice sync | mode=%s | checkpoint=%s | output=%s",
            "incremental" if is_incremental_run else "full",
            last_purchase_date or "none",
            self.output_path,
        )

        with self.output_path.open(file_mode, newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=INVOICE_HEADERS)
            if file_mode == "w":
                writer.writeheader()

            skip = 0
            page = 1
            seen_ids: Set[int] = set()

            while True:
                self._logger.debug(
                    "Fetching invoice page | page=%s | skip=%s",
                    page,
                    skip,
                )

                page_payload = self._fetch_invoice_page(
                    credentials=credentials,
                    headers=headers,
                    skip=skip,
                    from_purchase_date=last_purchase_date if is_incremental_run else None,
                )
                invoices_raw = page_payload.get("Data", []) or []
                invoices = self._filter_invoices(
                    invoices_raw,
                    seen_ids,
                    last_purchase_date,
                    is_incremental_run,
                )

                if not invoices:
                    break

                processed_invoices, processed_lines, batch_newest = self._process_batch(
                    invoices,
                    headers,
                    writer,
                    page,
                    start_time,
                )

                total_invoices += processed_invoices
                total_lines += processed_lines

                if batch_newest and (
                    not newest_purchase_date or batch_newest > newest_purchase_date
                ):
                    newest_purchase_date = batch_newest

                if not self._should_continue(invoices, is_incremental_run):
                    break

                skip += self.page_size
                page += 1

        duration = time.time() - start_time
        checkpoint_updated = False

        if (
            newest_purchase_date
            and (
                not last_purchase_date
                or newest_purchase_date > last_purchase_date
            )
        ):
            self._save_checkpoint(newest_purchase_date)
            checkpoint_updated = True
            self._logger.info("Checkpoint updated to %s", newest_purchase_date)
        else:
            self._logger.info("No checkpoint change")

        self._logger.info(
            "Invoice sync finished | invoices=%s | lines=%s | duration=%.1fs",
            total_invoices,
            total_lines,
            duration,
        )

        return InvoiceSyncResult(
            invoices=total_invoices,
            lines=total_lines,
            newest_purchase_date=newest_purchase_date,
            output_file=self.output_path,
            duration_seconds=duration,
            incremental=is_incremental_run,
            checkpoint_updated=checkpoint_updated,
        )

    def _fetch_invoice_page(
        self,
        *,
        credentials: AccessCredentials,
        headers: Dict[str, str],
        skip: int,
        from_purchase_date: Optional[str],
    ) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "BranchIds": [credentials.branch_id],
            "InvoiceStatus": [1],
            "Skip": skip,
            "Take": self.page_size,
            "ForSummaryRow": False,
        }

        if from_purchase_date:
            payload["PurchaseDateFrom"] = from_purchase_date
        else:
            payload["TimeRange"] = "month"

        return self.client.post(
            "/invoices/list",
            headers=headers,
            params={"format": "json"},
            json_payload=payload,
        )

    def _process_batch(
        self,
        invoices: List[Dict[str, object]],
        headers: Dict[str, str],
        writer: csv.DictWriter,
        page: int,
        start_time: float,
    ) -> Tuple[int, int, Optional[str]]:
        processed_invoices = 0
        processed_lines = 0
        newest_purchase_date: Optional[str] = None

        progress = tqdm(
            invoices,
            desc=f"Page {page}",
            unit="invoice",
            leave=False,
        )

        for invoice in progress:
            invoice_id = int(invoice.get("Id", 0) or 0)
            invoice_code = str(invoice.get("Code", "") or "")
            purchase_date = str(invoice.get("PurchaseDate", "") or "")

            details = self._fetch_invoice_details(invoice_id, headers)

            for detail in details:
                writer.writerow(
                    {
                        "InvoiceId": invoice_id,
                        "InvoiceCode": invoice_code,
                        "PurchaseDate": purchase_date,
                        "ProductId": detail.get("ProductId", ""),
                        "ProductCode": detail.get("ProductCode", ""),
                        "ProductName": detail.get("ProductName", ""),
                        "Quantity": detail.get("Quantity", 0),
                        "Price": detail.get("Price", 0),
                        "SubTotal": detail.get("SubTotal", 0),
                    }
                )

            processed_invoices += 1
            processed_lines += len(details)

            if purchase_date and (
                not newest_purchase_date or purchase_date > newest_purchase_date
            ):
                newest_purchase_date = purchase_date

            elapsed = time.time() - start_time
            rate = processed_invoices / elapsed if elapsed > 0 else 0
            progress.set_postfix(
                invoices=processed_invoices,
                lines=processed_lines,
                rate=f"{rate:.1f}/s",
            )

        progress.close()
        return processed_invoices, processed_lines, newest_purchase_date

    def _fetch_invoice_details(
        self,
        invoice_id: int,
        headers: Dict[str, str],
    ) -> List[Dict[str, object]]:
        if invoice_id <= 0:
            raise ConfigurationError("invoice_id must be positive")

        try:
            response = self.client.get(
                f"/invoices/{invoice_id}/details",
                headers=headers,
                params={
                    "format": "json",
                    "Includes": [
                        "ProductName",
                        "ProductCode",
                        "SubTotal",
                        "Product",
                    ],
                },
            )
        except KiotVietAPIError as exc:
            self._logger.warning(
                "Failed to fetch details for invoice %s: %s",
                invoice_id,
                exc,
            )
            return []

        data = response.get("Data", []) if isinstance(response, dict) else []
        if not isinstance(data, list):
            self._logger.warning("Unexpected detail payload for invoice %s", invoice_id)
            return []
        return data

    def _filter_invoices(
        self,
        invoices: List[Dict[str, object]],
        seen_ids: Set[int],
        last_purchase_date: Optional[str],
        is_incremental: bool,
    ) -> List[Dict[str, object]]:
        filtered: List[Dict[str, object]] = []

        for invoice in invoices:
            invoice_id = int(invoice.get("Id", 0) or 0)
            if invoice_id <= 0 or invoice_id in seen_ids:
                continue

            purchase_date = str(invoice.get("PurchaseDate", "") or "")
            if (
                is_incremental
                and last_purchase_date
                and not (purchase_date > last_purchase_date)
            ):
                continue

            seen_ids.add(invoice_id)
            filtered.append(invoice)

        return filtered

    def _should_continue(
        self,
        invoices: List[Dict[str, object]],
        is_incremental: bool,
    ) -> bool:
        if not invoices:
            return False
        if is_incremental and len(invoices) < self.page_size:
            return False
        return True

    def _load_checkpoint(self) -> Optional[str]:
        if not self.checkpoint_path.exists():
            return None

        try:
            with self.checkpoint_path.open("r", encoding="utf-8") as handler:
                payload = json.load(handler)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Invalid checkpoint file {self.checkpoint_path}: {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot read checkpoint file {self.checkpoint_path}: {exc}"
            ) from exc

        checkpoint = payload.get("last_purchase_date") if isinstance(payload, dict) else None
        if checkpoint is not None and not isinstance(checkpoint, str):
            raise ConfigurationError("last_purchase_date must be a string")
        return checkpoint

    def _save_checkpoint(self, purchase_date: str) -> None:
        if not purchase_date:
            raise ConfigurationError("purchase_date must be non-empty")

        payload = {"last_purchase_date": purchase_date}
        try:
            with self.checkpoint_path.open("w", encoding="utf-8") as handler:
                json.dump(payload, handler, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise ConfigurationError(
                f"Cannot write checkpoint file {self.checkpoint_path}: {exc}"
            ) from exc
