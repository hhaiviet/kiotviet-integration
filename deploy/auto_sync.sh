#!/bin/bash
# Script to run on Pi - auto sync with token fetching

cd /home/hhaiviet/kiotviet-integration

echo "=================================="
echo "KiotViet Auto Sync on Raspberry Pi"
echo "=================================="
echo ""

# Activate venv
source venv/bin/activate

# Run the Python script
python << 'EOF'
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, '/home/hhaiviet/kiotviet-integration')
os.chdir('/home/hhaiviet/kiotviet-integration')

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{level}]" if level else "[*]"
    print(f"{prefix} {timestamp} - {msg}")

# Step 1: Fetch token
log("STEP 1: Fetching token...", "INFO")

url = "https://api-man1.kiotviet.vn/api/account/login"
headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=utf-8",
    "User-Agent": "Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36",
}
payload = {
    "model": {
        "RememberMe": True,
        "ShowCaptcha": False,
        "UserName": "0913431718",
        "Password": "68686868",
        "Language": "vi-VN",
        "LatestBranchId": 291407
    },
    "IsManageSide": True
}

try:
    response = requests.post(url, json=payload, headers=headers, params={"quan-ly": "true"}, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if not data.get("isSuccess"):
        log(f"Login failed", "ERROR")
        sys.exit(1)
    
    token = data.get("token")
    branch = data.get("currentBranch", {})
    retailer_id = branch.get("Name", "248minimart")
    branch_id = branch.get("Id", 291407)
    
    token_data = {
        "access_token": token,
        "retailer_id": retailer_id,
        "branch_id": branch_id,
        "expires_at": None
    }
    
    # Save token
    token_file = Path("data/credentials/token.json")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with token_file.open("w") as f:
        json.dump(token_data, f, indent=2)
    
    log(f"Token fetched and saved! Retailer: {retailer_id}, Branch: {branch_id}", "SUCCESS")
    
except Exception as e:
    log(f"Error: {e}", "ERROR")
    sys.exit(1)

# Step 2: Run sync scripts
log("STEP 2: Running sync scripts...", "INFO")

try:
    from src.services.product_service import ProductService
    from src.services.invoice_service import InvoiceService
    
    # Product export
    log("Running Product Export...", "INFO")
    product_service = ProductService()
    result = product_service.export()
    log(f"Products exported: {result.products}", "SUCCESS")
    
    # Invoice export
    log("Running Invoice Export...", "INFO")
    invoice_service = InvoiceService()
    result = invoice_service.export()
    log(f"Invoices exported: {result.invoices}", "SUCCESS")
    
    log("All sync completed!", "SUCCESS")
    
except Exception as e:
    log(f"Sync error: {e}", "ERROR")
    sys.exit(1)

EOF

echo ""
echo "=================================="
echo "Done!"
echo "=================================="
