#!/usr/bin/env python3
"""
Auto-fetch token on Pi and run all sync scripts
Tự động lấy token từ KiotViet API rồi chạy toàn bộ script
"""

import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', 
                allow_agent=False, look_for_keys=False, timeout=10)
    
    print("\n" + "="*70)
    print("KIOTVIET INTEGRATION - AUTO-SYNC ON PI")
    print("="*70 + "\n")
    
    # Combined script: fetch token + run all sync
    cmd = """cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python3 << 'MAIN_SCRIPT'
import sys, os, json, requests
from pathlib import Path
sys.path.insert(0, '.')

print("[STEP 1] Fetching fresh token from KiotViet API...")
USERNAME = '0913431718'
PASSWORD = '68686868'
LOGIN_URL = "https://api-man1.kiotviet.vn/api/account/login"

try:
    response = requests.post(
        LOGIN_URL,
        json={"username": USERNAME, "password": PASSWORD, "RememberMe": False, "ShowCaptcha": False, "Language": "VI", "LatestBranchId": 291407},
        params={"quan-ly": "true"},
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("isSuccess"):
        print(f"[ERROR] Login failed")
        sys.exit(1)
    token = data["token"]
    retailer_id = data.get("currentBranch", {}).get("Name", "248minimart")
    branch_id = data.get("currentBranch", {}).get("Id", 291407)
    token_file = Path("data/credentials/token.json")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_data = {"access_token": token, "retailer_id": retailer_id, "branch_id": branch_id, "expires_at": None}
    with token_file.open("w") as f:
        json.dump(token_data, f, indent=2)
    print(f"[OK] Token saved: {retailer_id} / {branch_id}")
except Exception as e:
    print(f"[ERROR] Token fetch failed: {e}")
    sys.exit(1)

print("[STEP 2] Running sync scripts...")
from src.services.product_service import ProductService
from src.services.invoice_service import InvoiceService

print(">>> Product Export...")
try:
    product_service = ProductService()
    result = product_service.export()
    print(f"[OK] {result.products} products exported")
except Exception as e:
    print(f"[!] Product error: {e}")

print(">>> Invoice Export...")
try:
    invoice_service = InvoiceService()
    result = invoice_service.export()
    print(f"[OK] {result.invoices} invoices exported")
except Exception as e:
    print(f"[!] Invoice error: {e}")

print("[OK] Sync completed!")
MAIN_SCRIPT
"""
    
    print("[CONNECTING TO PI...]\n")
    
    # Execute with longer timeout for API calls
    _, stdout, stderr = ssh.exec_command(cmd, timeout=600)
    
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.rstrip())
    
    # Check for errors
    err = stderr.read(4096).decode()
    if err:
        print("\n[STDERR]:")
        print(err[:1000])
    
    exit_code = stdout.channel.recv_exit_status()
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("[OK] SYNC COMPLETED SUCCESSFULLY!")
    else:
        print(f"[!] Exit code: {exit_code}")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n[ERROR] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    ssh.close()
