# n8n Workflow Setup Guide - KiotViet ETL Pipeline

## 📍 Quick Start

**n8n URL:** http://116.102.136.220:5678

## 🚀 Import Workflow

### Method 1: Import from File (Recommended)

1. **Open n8n UI**
   - Go to: http://116.102.136.220:5678
   - Login with:
     - Email: `hhaiviet@gmail.com`
     - Password: `Hoangviet12`

2. **Import Workflow**
   - Click the **"+"** button in top-left
   - Select **"Import from file"**
   - Upload: `n8n_kiotviet_workflow_v2.json`
   - Click **"Import"**

3. **Verify Workflow**
   - You should see 7 nodes connected:
     - 🔓 Fetch Token
     - 📦 Export Products
     - 📋 Export Invoices
     - ☁️ Upload Products
     - ☁️ Upload Invoices
     - ✅ Success Summary

## 🔧 Configuration

### Set up Trigger (Choose one):

#### Option A: Cron Schedule (Automatic - Every 6 Hours)
1. In workflow editor, add a new node
2. Search for **"Cron"**
3. Configure:
   - **Cron expression:** `0 */6 * * *` (every 6 hours)
   - Connect to **"Fetch Token"** node

#### Option B: Webhook (Manual)
- Use the webhook URL provided by n8n
- Trigger: POST to webhook URL
- Payload: empty `{}`

#### Option C: Interval
1. Add **"Interval"** node
2. Set interval to **6 hours**

## 🎯 Workflow Overview

```
┌──────────────────┐
│ Cron Trigger     │ (Every 6 hours)
│ or Webhook       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│ 🔓 Fetch Token from KiotViet API    │
│ - Username: 0913431718               │
│ - Password: 68686868                 │
│ - Retailer: 248minimart              │
└────────┬─────────────────────────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
┌──────────────┐  ┌──────────────┐
│ 📦 Products │  │ 📋 Invoices  │
└────┬────────┘  └────┬─────────┘
     │                │
     ▼                ▼
┌──────────────┐  ┌──────────────┐
│ ☁️ Upload   │  │ ☁️ Upload   │
│ Products    │  │ Invoices     │
└────┬────────┘  └────┬─────────┘
     └────┬──────────┘
          ▼
    ┌──────────────────┐
    │ ✅ Summary       │
    │ - Execution time │
    │ - Item counts    │
    │ - Blob URLs      │
    └──────────────────┘
```

## 📝 API Endpoints Used

The workflow calls these endpoints on the Pi:

1. **Token Fetch**
   - `POST https://api-man1.kiotviet.vn/api/account/login`
   - Headers: `Retailer: 248minimart`

2. **Product Export**
   - `POST http://localhost:5678/api/kiotviet/products/export`
   - Uses token from Step 1

3. **Invoice Sync**
   - `POST http://localhost:5678/api/kiotviet/invoices/sync`
   - Body: `{"incremental": true}`

4. **Upload to Blob**
   - `POST http://localhost:5678/api/kiotviet/blob/upload/products`
   - `POST http://localhost:5678/api/kiotviet/blob/upload/invoices`

## ✅ Testing

### Manual Trigger
1. Open workflow in n8n
2. Click **"Execute Workflow"** button (play icon)
3. Watch execution in real-time
4. Check **"Success Summary"** node output

### Verify Results
- Products CSV: `data/output/master_products.csv` (should update)
- Invoices CSV: `data/output/invoice_details.csv` (should update)
- Blob Storage:
  - https://kiotvietintegration.blob.core.windows.net/kiotviet-data/master_products.csv
  - https://kiotvietintegration.blob.core.windows.net/kiotviet-data/invoice_details.csv

## 🐛 Troubleshooting

**Issue: Nodes showing errors**
- Check if HTTP endpoints are correct
- Verify token fetch is working
- Check logs in n8n UI (click node → "Logs" tab)

**Issue: 401 Unauthorized**
- Token may be expired
- Re-run workflow to get fresh token
- Check credentials in "Fetch Token" node

**Issue: Files not uploading**
- Check Azure Blob Storage connection string on Pi
- Verify `.env` file exists with `AZURE_STORAGE_CONNECTION_STRING`
- Check blob container name: `kiotviet-data`

## 📊 Monitoring

### View Execution History
1. In n8n UI, click **"Executions"** tab
2. See all past runs with timestamps
3. Check individual node outputs

### Enable Email Alerts
1. Edit workflow
2. Add **"Send Email"** node after failure
3. Configure email notifications

## 🔄 Scheduling Options

### Option 1: Every 6 Hours
```
Cron: 0 */6 * * *
Times: 00:00, 06:00, 12:00, 18:00
```

### Option 2: Every 3 Hours
```
Cron: 0 */3 * * *
Times: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
```

### Option 3: Daily at 8 AM
```
Cron: 0 8 * * *
```

## 📚 n8n Documentation

- n8n Docs: https://docs.n8n.io
- HTTP Request Node: https://docs.n8n.io/nodes/n8n-nodes-base.httpRequest/
- Cron Node: https://docs.n8n.io/nodes/n8n-nodes-base.cron/

---

**Last Updated:** November 9, 2025
**Workflow Version:** 2.0
**Status:** ✅ Ready for deployment
