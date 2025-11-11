#!/usr/bin/env python3
"""
Setup n8n workflow for KiotViet ETL on Raspberry Pi
Creates a workflow with: Token Fetch -> Product Export -> Invoice Sync -> Upload to Blob
"""

import requests
import json
import subprocess
import time
from pathlib import Path

# Configuration
N8N_URL = "http://116.102.136.220:5678"
N8N_EMAIL = "hhaiviet@gmail.com"
N8N_PASSWORD = "Hoangviet12"
PROJECT_DIR = Path(__file__).parent

print("🚀 Setting up n8n workflow for KiotViet ETL...\n")

# Step 1: Get auth token via n8n API
print("📝 Step 1: Authenticating with n8n...")
try:
    # Try different endpoints
    auth_endpoints = [
        f"{N8N_URL}/api/v1/auth/login",
        f"{N8N_URL}/api/auth/login",
    ]
    
    token = None
    for endpoint in auth_endpoints:
        try:
            print(f"  Trying {endpoint}...")
            response = requests.post(
                endpoint,
                json={"email": N8N_EMAIL, "password": N8N_PASSWORD},
                timeout=10
            )
            print(f"    Response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "token" in data["data"]:
                    token = data["data"]["token"]
                    print(f"  ✅ Token obtained: {token[:20]}...")
                    break
                elif "token" in data:
                    token = data["token"]
                    print(f"  ✅ Token obtained: {token[:20]}...")
                    break
        except Exception as e:
            print(f"    Failed: {e}")
            continue
    
    if not token:
        print("  ⚠️ Could not obtain token via API")
        print("  → You'll need to import workflow manually via n8n UI")
        print("  → Go to http://116.102.136.220:5678 → Import workflow\n")
        
except Exception as e:
    print(f"  ❌ Authentication failed: {e}\n")

# Step 2: Create workflow JSON
print("📋 Step 2: Creating workflow definition...")

workflow = {
    "name": "KiotViet ETL Pipeline",
    "description": "Automated ETL: Fetch Token → Export Products → Export Invoices → Upload to Blob",
    "nodes": [
        {
            "parameters": {
                "url": "http://localhost:5678/api/kiotviet/token",
                "method": "POST",
                "bodyParametersJson": '{\n  "username": "0913431718",\n  "password": "68686868"\n}'
            },
            "id": "fetch-token",
            "name": "🔓 Fetch Token",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [250, 300]
        },
        {
            "parameters": {
                "url": "http://localhost:5678/api/kiotviet/products/export",
                "method": "POST",
                "bodyParametersJson": "{}"
            },
            "id": "export-products",
            "name": "📦 Export Products",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [550, 150]
        },
        {
            "parameters": {
                "url": "http://localhost:5678/api/kiotviet/invoices/sync",
                "method": "POST",
                "bodyParametersJson": '{"incremental": true}'
            },
            "id": "export-invoices",
            "name": "📋 Export Invoices",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [550, 450]
        },
        {
            "parameters": {
                "url": "http://localhost:5678/api/kiotviet/upload/products",
                "method": "POST",
                "bodyParametersJson": "{}"
            },
            "id": "upload-products",
            "name": "☁️ Upload Products",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [850, 150]
        },
        {
            "parameters": {
                "url": "http://localhost:5678/api/kiotviet/upload/invoices",
                "method": "POST",
                "bodyParametersJson": "{}"
            },
            "id": "upload-invoices",
            "name": "☁️ Upload Invoices",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [850, 450]
        },
        {
            "parameters": {
                "content": "✅ **KiotViet ETL Pipeline Completed!**\n\n📊 Summary:\n- ✅ Token fetched from KiotViet API\n- ✅ Products exported: {{$node[\"export-products\"].json.count || 'N/A'}} items\n- ✅ Invoices synced: {{$node[\"export-invoices\"].json.count || 'N/A'}} invoices\n- ✅ All data uploaded to Azure Blob Storage\n\n⏰ Execution time: {{$execution.duration}}ms\n🔗 Blob URLs:\n- Products: https://kiotvietintegration.blob.core.windows.net/kiotviet-data/master_products.csv\n- Invoices: https://kiotvietintegration.blob.core.windows.net/kiotviet-data/invoice_details.csv"
            },
            "id": "success-notification",
            "name": "✅ Success Summary",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [1100, 300]
        }
    ],
    "connections": {
        "fetch-token": {
            "main": [
                [
                    {"node": "export-products", "type": "main", "index": 0},
                    {"node": "export-invoices", "type": "main", "index": 0}
                ]
            ]
        },
        "export-products": {
            "main": [[{"node": "upload-products", "type": "main", "index": 0}]]
        },
        "export-invoices": {
            "main": [[{"node": "upload-invoices", "type": "main", "index": 0}]]
        },
        "upload-products": {
            "main": [[{"node": "success-notification", "type": "main", "index": 0}]]
        },
        "upload-invoices": {
            "main": [[{"node": "success-notification", "type": "main", "index": 0}]]
        }
    }
}

workflow_file = PROJECT_DIR / "n8n_kiotviet_workflow.json"
with open(workflow_file, 'w') as f:
    json.dump(workflow, f, indent=2)

print(f"  ✅ Workflow saved: {workflow_file}\n")

# Step 3: Instructions for manual import
print("📥 Step 3: Import workflow into n8n")
print("=" * 60)
print("""
Since API authentication is complex, please import manually:

1. Open n8n UI: http://116.102.136.220:5678
2. Click "+" (New) → "Import from file"
3. Select: n8n_kiotviet_workflow.json
4. Click "Import"
5. Configure triggers:
   - Add "Cron" node for scheduling (every 6 hours)
   - Or keep webhook trigger for manual execution

Workflow nodes:
├─ 🔓 Fetch Token        → Get JWT from KiotViet API
├─ 📦 Export Products    → Run product export (758 items)
├─ 📋 Export Invoices    → Run invoice sync (incremental)
├─ ☁️  Upload Products   → Upload CSV to Blob Storage
├─ ☁️  Upload Invoices   → Upload CSV to Blob Storage
└─ ✅ Success Summary    → Display execution summary

Execution flow:
  Fetch Token
    ├─→ Export Products → Upload Products ─┐
    └─→ Export Invoices → Upload Invoices ─┴─→ Success Summary

""")

print("=" * 60)
print("\n✨ Setup complete!")
print(f"\n📍 Workflow file: {workflow_file}")
print(f"🌐 n8n URL: {N8N_URL}")
print(f"👤 Email: {N8N_EMAIL}")
