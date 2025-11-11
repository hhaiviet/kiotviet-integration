# KiotViet Integration - Production Setup Guide

## 📋 Project Structure (Standardized)

```
kiotviet-integration/
├── src/
│   ├── orchestration/          ← NEW: Main orchestration
│   │   ├── __init__.py
│   │   ├── etl_pipeline.py     ← Main ETL class
│   │   └── scheduler.py        ← (Future: advanced scheduling)
│   ├── services/               ← Existing services (no change)
│   │   ├── product_service.py
│   │   ├── invoice_service.py
│   │   ├── token_service.py
│   │   └── ...
│   ├── api/
│   ├── utils/
│   └── models/
├── config/
│   └── default.yml
├── data/
│   ├── output/
│   ├── credentials/
│   ├── checkpoints/
│   └── logs/                   ← ETL logs
├── run_etl.py                  ← ✨ NEW: Main entry point
├── setup_cron.py               ← ✨ NEW: Cron configuration
├── pi_auto_sync.py             ← (Legacy, still works)
└── requirements.txt
```

## 🚀 Quick Start

### 1. Copy files to Pi

```bash
# On Windows
scp run_etl.py setup_cron.py hhaiviet@116.102.136.220:/home/hhaiviet/kiotviet-integration/
scp -r src/orchestration hhaiviet@116.102.136.220:/home/hhaiviet/kiotviet-integration/src/
```

### 2. Test ETL locally

```bash
# On Pi
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python run_etl.py
```

Expected output:
```
🚀 KIOTVIET ETL PIPELINE STARTED
========================================================================
STEP 1: FETCH TOKEN FROM KIOTVIET API
========================================================================
...
✅ Token fetched successfully!
...
STEP 2: EXPORT PRODUCTS
...
✅ Product export completed!
...
STEP 3: SYNC INVOICES (INCREMENTAL)
...
✅ Invoice sync completed!
...
STEP 4: UPLOAD TO AZURE BLOB STORAGE
...
✅ Products uploaded
✅ Invoices uploaded
...
📊 ETL PIPELINE SUMMARY
Status: ✅ SUCCESS
```

### 3. Setup Cron Job

```bash
# On Pi
python setup_cron.py

# OR with custom schedule (every 3 hours)
python setup_cron.py --schedule "0 */3 * * *"

# OR with custom log file
python setup_cron.py --log-file /path/to/custom.log
```

### 4. Verify Cron

```bash
# Check installed cron job
crontab -l

# Watch cron logs
tail -f /home/hhaiviet/kiotviet-integration/data/logs/etl.log
```

## 📊 ETL Pipeline Overview

### What it does:

**1. Fetch Token (Step 1)**
- Login to KiotViet API with credentials
- Store JWT token for API calls
- Retailer: 248minimart, Branch: 291407

**2. Export Products (Step 2)**
- Fetch all 758 products from inventory
- Save to: `data/output/master_products.csv`
- Duration: ~7 seconds

**3. Sync Invoices (Step 3)**
- Fetch new invoices since last sync
- Incremental mode (only new invoices)
- Save to: `data/output/invoice_details.csv`
- Updates checkpoint with latest invoice date

**4. Upload to Blob (Step 4)**
- Upload CSV files to Azure Blob Storage
- URLs:
  - Products: `https://kiotvietintegration.blob.core.windows.net/kiotviet-data/master_products.csv`
  - Invoices: `https://kiotvietintegration.blob.core.windows.net/kiotviet-data/invoice_details.csv`

**Total execution time:** ~15-20 seconds

### Execution Flow:

```
START
  ↓
FETCH TOKEN (KiotViet API)
  ├─→ EXPORT PRODUCTS (parallel)
  └─→ SYNC INVOICES (parallel)
        ↓
      UPLOAD TO BLOB (both files)
        ↓
      SUMMARY & EXIT
```

## 🔧 Configuration

### Environment Variables

Required (in `.env` or Pi cron):

```bash
# KiotViet API
KIOTVIET_USERNAME=0913431718
KIOTVIET_PASSWORD=68686868

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER=kiotviet-data
```

### Cron Schedules

**Every 6 hours (default):**
```
0 */6 * * * cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python run_etl.py >> data/logs/etl.log 2>&1
```

**Every 3 hours:**
```
0 */3 * * * ...
```

**Every hour:**
```
0 * * * * ...
```

**Daily at 8 AM:**
```
0 8 * * * ...
```

**Every 30 minutes:**
```
*/30 * * * * ...
```

## 📝 Logging

### Log Locations

- **Main ETL log:** `data/logs/etl.log`
- **Service logs:** `data/logs/` (from individual services)

### Log Levels

Default: `INFO`

To view with different level:
```bash
python run_etl.py --log-level DEBUG
```

### Sample Log Output

```
2025-11-09 11:45:14,686 - kiotviet - INFO - 🚀 KIOTVIET ETL PIPELINE STARTED
2025-11-09 11:45:14,688 - kiotviet - INFO - STEP 1: FETCH TOKEN FROM KIOTVIET API
2025-11-09 11:45:15,128 - kiotviet - INFO - ✅ Token fetched successfully!
2025-11-09 11:45:24,560 - kiotviet - INFO - STEP 2: EXPORT PRODUCTS
2025-11-09 11:45:31,742 - kiotviet - INFO - ✅ Product export completed: 758 items
...
```

## 🐛 Troubleshooting

### Issue: Token fetch fails with "Unknown error"

**Possible causes:**
- API endpoint down
- Invalid credentials
- Network connectivity issue

**Solution:**
```bash
# Check API connectivity
curl -X POST https://api-man1.kiotviet.vn/api/account/login \
  -H "Retailer: 248minimart" \
  -d '{"model":{"UserName":"0913431718","Password":"68686868"}}'

# Check env vars
echo $KIOTVIET_USERNAME
echo $KIOTVIET_PASSWORD
```

### Issue: Products/Invoices not exporting

**Check:**
- ProductService/InvoiceService code runs independently
- Check individual service logs in `data/logs/`

**Test individually:**
```bash
python -c "from src.services import ProductService; ProductService().export()"
python -c "from src.services import InvoiceService; InvoiceService().sync()"
```

### Issue: Blob upload fails

**Check:**
- Azure Blob Storage connection string
- Container name is `kiotviet-data`
- Files exist before upload

```bash
# Verify connection
echo $AZURE_STORAGE_CONNECTION_STRING | head -20

# Check output files
ls -lh data/output/
```

### Issue: Cron job not running

**Check:**
```bash
# Verify cron is installed
crontab -l

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Verify permissions
ls -la /home/hhaiviet/kiotviet-integration/run_etl.py
```

## 📈 Monitoring

### Check latest run

```bash
tail -50 /home/hhaiviet/kiotviet-integration/data/logs/etl.log
```

### Check execution history

```bash
grep "ETL PIPELINE SUMMARY" /home/hhaiviet/kiotviet-integration/data/logs/etl.log -A 10
```

### Count successful runs

```bash
grep "Status: ✅ SUCCESS" /home/hhaiviet/kiotviet-integration/data/logs/etl.log | wc -l
```

## 🔄 Graceful Shutdown

If ETL is running:

```bash
# Find process
ps aux | grep "python run_etl"

# Kill gently
kill -TERM <PID>

# Or restart cron
sudo systemctl restart cron
```

## 📚 API References

### KiotViet API

**Endpoint:** `https://api-man1.kiotviet.vn/api`

**Token Endpoint:**
```
POST /account/login?quan-ly=true
Header: Retailer: 248minimart
Body: {"model": {"UserName": "...", "Password": "..."}}
Response: {"result": {"access_token": "..."}}
```

### Azure Blob Storage

**Container:** `kiotviet-data`

**Files uploaded:**
- `master_products.csv` (758 rows)
- `invoice_details.csv` (dynamic, incremental)

## 🎯 Next Steps

1. ✅ **Production deployment** - All files ready
2. ✅ **Cron scheduling** - Setup script included
3. 🔄 **Monitoring** - View logs via `tail -f data/logs/etl.log`
4. 🔄 **Alerting** - Add email notifications (future)
5. 🔄 **Dashboard** - Web UI for status (future)

---

**Last Updated:** November 9, 2025  
**Version:** 1.0 Production Ready  
**Status:** ✅ Tested and Verified
