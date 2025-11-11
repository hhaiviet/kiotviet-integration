"""
KiotViet ETL Pipeline - Unified orchestration script
Tổng hợp: Token Fetch → Product Export → Invoice Sync → Upload to Blob
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.product_service import ProductService, ProductExportResult
from src.services.invoice_service import InvoiceService, InvoiceSyncResult
from src.utils.logger import logger
from src.utils.azure_blob import upload_to_azure_blob


@dataclass
class ETLResult:
    """Result summary of entire ETL pipeline"""
    success: bool
    token_status: str
    product_count: int = 0
    invoice_count: int = 0
    invoice_lines: int = 0
    product_blob_url: Optional[str] = None
    invoice_blob_url: Optional[str] = None
    errors: list = None
    duration_seconds: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class KiotVietETLPipeline:
    """Main ETL Pipeline orchestrator"""

    def __init__(self, log_level: str = "INFO"):
        """Initialize ETL pipeline"""
        self.logger = logger
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        self.project_root = PROJECT_ROOT
        self.data_dir = self.project_root / "data"
        self.token_file = self.data_dir / "credentials" / "token.json"
        
        self.result = ETLResult(success=False, token_status="not-started")

    def fetch_token(self) -> Tuple[bool, Optional[Dict]]:
        """
        STEP 1: Fetch fresh JWT token from KiotViet API
        
        Returns:
            (success: bool, token_data: dict or None)
        """
        self.logger.info("=" * 70)
        self.logger.info("STEP 1: FETCH TOKEN FROM KIOTVIET API")
        self.logger.info("=" * 70)
        
        try:
            import requests
            
            username = os.getenv("KIOTVIET_USERNAME", "0913431718")
            password = os.getenv("KIOTVIET_PASSWORD", "68686868")
            
            url = "https://api-man1.kiotviet.vn/api/account/login?quan-ly=true"
            headers = {
                "Retailer": "248minimart",
                "Content-Type": "application/json",
            }
            payload = {
                "model": {
                    "UserName": username,
                    "Password": password,
                    "RememberMe": False,
                    "ShowCaptcha": False,
                    "Language": "vi-VN",
                    "LatestBranchId": 291407,
                }
            }
            
            self.logger.info(f"📤 Sending login request to KiotViet API...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            # Check for success flag (not "result" field)
            if not data.get("isSuccess"):
                error_msg = data.get("error") or data.get("ResponseStatus", {}).get("Message", "Unknown error")
                self.logger.error(f"❌ Login failed: {error_msg}")
                self.result.token_status = f"failed: {error_msg}"
                return False, None
            
            # Extract token from response
            token = data.get("token")
            if not token:
                self.logger.error("❌ No token in response")
                self.result.token_status = "failed: no token"
                return False, None
            
            # Save token
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            token_data = {
                "access_token": token,
                "retailer_id": "248minimart",
                "branch_id": 291407,
            }
            with open(self.token_file, "w") as f:
                json.dump(token_data, f, indent=2)
            
            self.logger.info(f"✅ Token fetched successfully!")
            self.logger.info(f"   Retailer: 248minimart, Branch: 291407")
            self.result.token_status = "success"
            return True, token_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.result.token_status = f"failed: {error_msg}"
            self.result.errors.append(error_msg)
            return False, None
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.result.token_status = f"failed: {error_msg}"
            self.result.errors.append(error_msg)
            return False, None

    def export_products(self) -> Tuple[bool, Optional[ProductExportResult]]:
        """
        STEP 2: Export products from KiotViet API
        
        Returns:
            (success: bool, result: ProductExportResult or None)
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("STEP 2: EXPORT PRODUCTS")
        self.logger.info("=" * 70)
        
        try:
            self.logger.info("📦 Starting product export...")
            service = ProductService()
            result = service.export()
            
            self.logger.info(f"✅ Product export completed!")
            self.logger.info(f"   Items: {result.products}")
            self.logger.info(f"   Duration: {result.duration_seconds:.1f}s")
            self.logger.info(f"   Output: {result.output_file}")
            
            self.result.product_count = result.products
            return True, result
            
        except Exception as e:
            error_msg = f"Product export failed: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.result.errors.append(error_msg)
            import traceback
            traceback.print_exc()
            return False, None

    def sync_invoices(self) -> Tuple[bool, Optional[InvoiceSyncResult]]:
        """
        STEP 3: Sync invoices from KiotViet API (incremental mode)
        
        Returns:
            (success: bool, result: InvoiceSyncResult or None)
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("STEP 3: SYNC INVOICES (INCREMENTAL)")
        self.logger.info("=" * 70)
        
        try:
            self.logger.info("📋 Starting invoice sync...")
            service = InvoiceService()
            result = service.sync(incremental=True)
            
            self.logger.info(f"✅ Invoice sync completed!")
            self.logger.info(f"   Invoices: {result.invoices}")
            self.logger.info(f"   Lines: {result.lines}")
            self.logger.info(f"   Duration: {result.duration_seconds:.1f}s")
            self.logger.info(f"   Output: {result.output_file}")
            if result.newest_purchase_date:
                self.logger.info(f"   Latest: {result.newest_purchase_date}")
            
            self.result.invoice_count = result.invoices
            self.result.invoice_lines = result.lines
            return True, result
            
        except Exception as e:
            error_msg = f"Invoice sync failed: {e}"
            self.logger.error(f"❌ {error_msg}")
            self.result.errors.append(error_msg)
            import traceback
            traceback.print_exc()
            return False, None

    def upload_to_blob(
        self,
        product_result: Optional[ProductExportResult],
        invoice_result: Optional[InvoiceSyncResult],
    ) -> bool:
        """
        STEP 4: Upload CSVs to Azure Blob Storage
        
        Returns:
            success: bool
        """
        self.logger.info("\n" + "=" * 70)
        self.logger.info("STEP 4: UPLOAD TO AZURE BLOB STORAGE")
        self.logger.info("=" * 70)
        
        all_success = True
        
        # Upload products
        if product_result:
            try:
                self.logger.info("☁️  Uploading products...")
                blob_url = upload_to_azure_blob(product_result.output_file, "master_products.csv")
                self.logger.info(f"✅ Products uploaded: {blob_url}")
                self.result.product_blob_url = blob_url
            except Exception as e:
                error_msg = f"Product upload failed: {e}"
                self.logger.warning(f"⚠️  {error_msg}")
                self.result.errors.append(error_msg)
                all_success = False
        
        # Upload invoices
        if invoice_result:
            try:
                self.logger.info("☁️  Uploading invoices...")
                blob_url = upload_to_azure_blob(invoice_result.output_file, "invoice_details.csv")
                self.logger.info(f"✅ Invoices uploaded: {blob_url}")
                self.result.invoice_blob_url = blob_url
            except Exception as e:
                error_msg = f"Invoice upload failed: {e}"
                self.logger.warning(f"⚠️  {error_msg}")
                self.result.errors.append(error_msg)
                all_success = False
        
        return all_success

    def run(self) -> ETLResult:
        """
        Execute complete ETL pipeline
        
        Returns:
            ETLResult with execution summary
        """
        start_time = datetime.now()
        
        self.logger.info("\n")
        self.logger.info("🚀 KIOTVIET ETL PIPELINE STARTED")
        self.logger.info(f"⏰ Time: {start_time.isoformat()}")
        self.logger.info("\n")
        
        try:
            # Step 1: Fetch token
            token_ok, token_data = self.fetch_token()
            if not token_ok:
                self.result.success = False
                raise Exception("Token fetch failed")
            
            # Step 2: Export products
            product_ok, product_result = self.export_products()
            if not product_ok:
                self.logger.warning("⚠️  Product export failed, continuing with invoice...")
            
            # Step 3: Sync invoices
            invoice_ok, invoice_result = self.sync_invoices()
            if not invoice_ok:
                self.logger.warning("⚠️  Invoice sync failed, attempting upload anyway...")
            
            # Step 4: Upload to Blob
            upload_ok = self.upload_to_blob(product_result, invoice_result)
            
            # Determine overall success
            self.result.success = token_ok and (product_ok or invoice_ok) and upload_ok
            
        except Exception as e:
            self.logger.error(f"❌ Pipeline error: {e}")
            self.result.success = False
            self.result.errors.append(str(e))
            import traceback
            traceback.print_exc()
        
        finally:
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            self.result.duration_seconds = duration
            
            # Print summary
            self._print_summary()
        
        return self.result

    def _print_summary(self):
        """Print execution summary"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("📊 ETL PIPELINE SUMMARY")
        self.logger.info("=" * 70)
        
        status = "✅ SUCCESS" if self.result.success else "❌ FAILED"
        self.logger.info(f"Status: {status}")
        self.logger.info(f"Token: {self.result.token_status}")
        self.logger.info(f"Products: {self.result.product_count} items")
        self.logger.info(f"Invoices: {self.result.invoice_count} invoices, {self.result.invoice_lines} lines")
        
        if self.result.product_blob_url:
            self.logger.info(f"Product Blob: {self.result.product_blob_url}")
        if self.result.invoice_blob_url:
            self.logger.info(f"Invoice Blob: {self.result.invoice_blob_url}")
        
        self.logger.info(f"Duration: {self.result.duration_seconds:.1f}s")
        
        if self.result.errors:
            self.logger.warning(f"Errors ({len(self.result.errors)}):")
            for err in self.result.errors:
                self.logger.warning(f"  - {err}")
        
        self.logger.info("=" * 70)
        self.logger.info("")


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="KiotViet ETL Pipeline - Run complete ETL cycle"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = KiotVietETLPipeline(log_level=args.log_level)
    result = pipeline.run()
    
    # Exit with code
    exit_code = 0 if result.success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
