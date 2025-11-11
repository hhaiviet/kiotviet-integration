#!/usr/bin/env python3
"""
Script to run on Raspberry Pi - auto fetch token + run sync
Chạy trên Raspberry Pi - tự lấy token từ KiotViet API rồi chạy sync
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
env_path = Path('/home/hhaiviet/kiotviet-integration/.env')
if env_path.exists():
    load_dotenv(env_path)

# Add project to path
sys.path.insert(0, '/home/hhaiviet/kiotviet-integration')

from src.utils.azure_blob import upload_to_azure_blob

def log(msg, level="INFO"):
    """Simple logging."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{level}]" if level else "[*]"
    print(f"{prefix} {timestamp} - {msg}")

def fetch_token(username, password):
    """Fetch token from KiotViet API."""
    log("Fetching token from KiotViet API...", "INFO")
    
    url = "https://api-man1.kiotviet.vn/api/account/login"
    
    # IMPORTANT: Must include Retailer header!
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36",
        "Retailer": "248minimart",  # THIS IS REQUIRED!
    }
    
    # IMPORTANT: Payload must use 'model' wrapper with 'UserName' (uppercase U)
    payload = {
        "model": {
            "UserName": username,  # Uppercase U!
            "Password": password,
            "RememberMe": False,
            "ShowCaptcha": False,
            "Language": "vi-VN",
            "LatestBranchId": 291407
        }
    }
    
    try:
        log("Sending login request...", "INFO")
        response = requests.post(url, json=payload, headers=headers, params={"quan-ly": "true"}, timeout=30)
        
        if response.status_code != 200:
            log(f"HTTP Error {response.status_code}: {response.text[:200]}", "ERROR")
            return None
        
        data = response.json()
        
        # Check for success
        if not data.get("isSuccess"):
            error_msg = data.get("error") or data.get("ResponseStatus", {}).get("Message", "Unknown error")
            log(f"Login failed: {error_msg}", "ERROR")
            return None
        
        # Extract token
        token = data.get("token")
        if not token:
            log("No token in response", "ERROR")
            return None
        
        # Extract retailer and branch info
        current_branch = data.get("currentBranch")
        if isinstance(current_branch, dict):
            retailer_id = current_branch.get("Name", "248minimart")
            branch_id = current_branch.get("Id", 291407)
        else:
            # Fallback to defaults if currentBranch is not a dict
            retailer_id = "248minimart"
            branch_id = 291407
        
        log(f"Token fetched successfully! Retailer: {retailer_id}, Branch: {branch_id}", "SUCCESS")
        log(f"Token: {token[:50]}...", "INFO")
        
        return {
            "access_token": token,
            "retailer_id": retailer_id,
            "branch_id": branch_id,
            "expires_at": None
        }
        
    except requests.exceptions.RequestException as e:
        log(f"Request failed: {type(e).__name__}: {e}", "ERROR")
        return None
    except json.JSONDecodeError as e:
        log(f"JSON decode error: {e}", "ERROR")
        return None
    except Exception as e:
        log(f"Unexpected error during login: {type(e).__name__}: {e}", "ERROR")
        import traceback
        log(traceback.format_exc()[:200], "ERROR")
        return None

def save_token(token_data):
    """Save token to file."""
    token_file = Path("/home/hhaiviet/kiotviet-integration/data/credentials/token.json")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with token_file.open("w") as f:
            json.dump(token_data, f, indent=2)
        log(f"Token saved to {token_file}", "SUCCESS")
        return True
    except Exception as e:
        log(f"Failed to save token: {e}", "ERROR")
        return False

def run_product_export(retry_on_auth_error=True):
    """Run product export with auto-retry on auth error."""
    log("Running Product Export...", "INFO")
    
    try:
        from src.services.product_service import ProductService
        
        product_service = ProductService()
        result = product_service.export()
        log(f"✅ Product export done: {result.products} items", "SUCCESS")
        
        # Upload to Azure Blob Storage
        try:
            blob_url = upload_to_azure_blob(result.output_file)
            log(f"✅ Product data uploaded to Blob: {blob_url}", "SUCCESS")
        except Exception as upload_error:
            log(f"Warning: Failed to upload product data to Blob: {upload_error}", "WARN")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's auth error (token expired)
        if ("401" in error_msg or "Unauthorized" in error_msg or 
            "token" in error_msg.lower() or "auth" in error_msg.lower()) and retry_on_auth_error:
            
            log(f"Auth error detected: {error_msg[:100]}", "WARN")
            log("Token might be expired, fetching new token...", "INFO")
            
            # Fetch new token
            username = os.getenv("KIOTVIET_USERNAME", "0913431718")
            password = os.getenv("KIOTVIET_PASSWORD", "68686868")
            token_data = fetch_token(username, password)
            
            if token_data and save_token(token_data):
                log("New token fetched, retrying product export...", "INFO")
                # Retry without recursion to avoid infinite loop
                try:
                    from src.services.product_service import ProductService
                    product_service = ProductService()
                    result = product_service.export()
                    log(f"✅ Product export succeeded after token refresh: {result.products} items", "SUCCESS")
                    return True
                except Exception as retry_error:
                    log(f"Retry failed: {retry_error}", "ERROR")
                    return False
            else:
                log("Failed to fetch new token", "ERROR")
                return False
        else:
            log(f"Product export error: {error_msg}", "ERROR")
            return False

def run_invoice_export(retry_on_auth_error=True):
    """Run invoice export with auto-retry on auth error."""
    log("Running Invoice Export...", "INFO")
    
    try:
        from src.services.invoice_service import InvoiceService
        
        invoice_service = InvoiceService()
        result = invoice_service.sync(incremental=True)
        log(f"✅ Invoice export done: {result.invoices} invoices, {result.lines} lines", "SUCCESS")
        
        # Upload to Azure Blob Storage
        try:
            blob_url = upload_to_azure_blob(result.output_file)
            log(f"✅ Invoice data uploaded to Blob: {blob_url}", "SUCCESS")
        except Exception as upload_error:
            log(f"Warning: Failed to upload invoice data to Blob: {upload_error}", "WARN")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        
        # Check if it's auth error (token expired)
        if ("401" in error_msg or "Unauthorized" in error_msg or 
            "token" in error_msg.lower() or "auth" in error_msg.lower()) and retry_on_auth_error:
            
            log(f"Auth error detected: {error_msg[:100]}", "WARN")
            log("Token might be expired, fetching new token...", "INFO")
            
            # Fetch new token
            username = os.getenv("KIOTVIET_USERNAME", "0913431718")
            password = os.getenv("KIOTVIET_PASSWORD", "68686868")
            token_data = fetch_token(username, password)
            
            if token_data and save_token(token_data):
                log("New token fetched, retrying invoice export...", "INFO")
                # Retry without recursion to avoid infinite loop
                try:
                    from src.services.invoice_service import InvoiceService
                    invoice_service = InvoiceService()
                    result = invoice_service.export()
                    log(f"✅ Invoice export succeeded after token refresh: {result.invoices} items", "SUCCESS")
                    return True
                except Exception as retry_error:
                    log(f"Retry failed: {retry_error}", "ERROR")
                    return False
            else:
                log("Failed to fetch new token", "ERROR")
                return False
        else:
            log(f"Invoice export error: {error_msg}", "ERROR")
            return False

def run_sync_scripts():
    """Run sync scripts - product and invoice export."""
    log("Running sync scripts...", "INFO")
    
    os.chdir("/home/hhaiviet/kiotviet-integration")
    
    all_success = True
    
    try:
        # Product export
        if not run_product_export(retry_on_auth_error=True):
            all_success = False
        
        log("", "")
        
        # Invoice export
        if not run_invoice_export(retry_on_auth_error=True):
            all_success = False
        
        if all_success:
            log("All sync scripts completed successfully!", "SUCCESS")
            return True
        else:
            log("Some sync scripts failed.", "ERROR")
            return False
        
    except Exception as e:
        log(f"Sync error: {e}", "ERROR")
        import traceback
        log(traceback.format_exc()[:300], "ERROR")
        return False

def main():
    """Main function."""
    log("="*70, "")
    log("KIOTVIET INTEGRATION - AUTO SYNC ON RASPBERRY PI", "")
    log("="*70, "")
    log("")
    
    # Step 1: Try to fetch fresh token (optional)
    log("STEP 1: Fetch Fresh Token (Optional)", "INFO")
    log("-"*70, "")
    
    username = os.getenv("KIOTVIET_USERNAME", "0913431718")
    password = os.getenv("KIOTVIET_PASSWORD", "68686868")
    
    token_data = fetch_token(username, password)
    
    if token_data:
        if save_token(token_data):
            log("Fresh token fetched and saved!", "SUCCESS")
        else:
            log("Failed to save token, will use existing one.", "WARN")
    else:
        log("Failed to fetch fresh token, will use existing token from file.", "WARN")
        # Check if token file exists
        token_file = Path("/home/hhaiviet/kiotviet-integration/data/credentials/token.json")
        if token_file.exists():
            log(f"Using existing token from {token_file}", "INFO")
        else:
            log("No token file found and couldn't fetch new one. Exiting.", "ERROR")
            return 1
    
    log("", "")
    
    # Step 2: Run sync scripts (product and invoice)
    log("STEP 2: Run Sync Scripts (Product & Invoice)", "INFO")
    log("-"*70, "")
    
    if not run_sync_scripts():
        log("Sync scripts failed.", "ERROR")
        return 1
    
    log("", "")
    log("="*70, "")
    log("ALL COMPLETED SUCCESSFULLY!", "SUCCESS")
    log("="*70, "")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
