# KiotViet Auto Sync on Raspberry Pi - Setup Guide

## Mục đích
Script tự động:
1. **Lấy token mới** từ KiotViet API (không cần upload từ Window)
2. **Lưu token** vào `data/credentials/token.json`
3. **Chạy sync** (Product, Invoice, Full)
4. **Chạy định kỳ** mà không cần can thiệp

## Files Created

### 1. `pi_auto_sync.py` - Main Script
Chạy trên Pi, tự lấy token từ API rồi chạy sync

**Credentials:**
```python
username = "0913431718"
password = "68686868"
```

**Usage:**
```bash
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python pi_auto_sync.py
```

### 2. `auto_sync.sh` - Bash Wrapper
Alternative shell script wrapper

**Usage:**
```bash
cd /home/hhaiviet/kiotviet-integration
bash auto_sync.sh
```

## Setup on Raspberry Pi

### Option 1: Manual Run (Test)
```bash
ssh hhaiviet@116.102.136.220
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate

# Copy script từ local hoặc download
python pi_auto_sync.py
```

### Option 2: Cron Job (Every 30 minutes)
```bash
ssh hhaiviet@116.102.136.220

# Edit crontab
crontab -e

# Add line:
*/30 * * * * cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python pi_auto_sync.py >> data/logs/cron.log 2>&1
```

### Option 3: Systemd Service (Recommended)
```bash
ssh hhaiviet@116.102.136.220

# Create service file
sudo nano /etc/systemd/system/kiotviet-auto-sync.service
```

Paste:
```ini
[Unit]
Description=KiotViet Auto Sync Service
After=network.target

[Service]
Type=simple
User=hhaiviet
WorkingDirectory=/home/hhaiviet/kiotviet-integration
Environment="PATH=/home/hhaiviet/kiotviet-integration/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/hhaiviet/kiotviet-integration/venv/bin/python pi_auto_sync.py
Restart=always
RestartSec=300

StandardOutput=append:/home/hhaiviet/kiotviet-integration/data/logs/auto-sync.log
StandardError=append:/home/hhaiviet/kiotviet-integration/data/logs/auto-sync-error.log

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kiotviet-auto-sync.service
sudo systemctl start kiotviet-auto-sync.service

# Check status
sudo systemctl status kiotviet-auto-sync.service

# View logs
tail -f data/logs/auto-sync.log
```

## How It Works

1. **Token Fetching:**
   - Sends POST to: `https://api-man1.kiotviet.vn/api/account/login`
   - Credentials: 0913431718 / 68686868
   - Saves JWT token to `data/credentials/token.json`

2. **Sync Services:**
   - ProductService: Exports all products to CSV
   - InvoiceService: Exports invoices to CSV
   - Full sync: All operations

3. **Logging:**
   - Logs to: `data/logs/auto-sync.log`
   - Errors to: `data/logs/auto-sync-error.log`
   - If using systemd, logs are captured automatically

## Troubleshooting

### Token fetch fails (401 Unauthorized)
- Check credentials in `pi_auto_sync.py`
- Verify KiotViet account credentials are correct
- Check network connectivity

### Service fails to start
```bash
sudo systemctl status kiotviet-auto-sync.service
sudo journalctl -u kiotviet-auto-sync.service -n 50
```

### Permissions issue
```bash
# Make sure hhaiviet owns the directory
sudo chown -R hhaiviet:hhaiviet /home/hhaiviet/kiotviet-integration
```

### View live logs
```bash
# Systemd service
sudo journalctl -u kiotviet-auto-sync.service -f

# Or direct file
tail -f /home/hhaiviet/kiotviet-integration/data/logs/auto-sync.log
```

## What Gets Synced

After running, check outputs:
```bash
ls -lh /home/hhaiviet/kiotviet-integration/data/output/
```

Typical files:
- `master_products.csv` - All products
- `invoice_details.csv` - All invoices
- Other export files depending on full sync

## Environment Variables (Optional)

Override credentials via env vars:
```bash
export KIOTVIET_USERNAME="different_username"
export KIOTVIET_PASSWORD="different_password"
python pi_auto_sync.py
```

Or modify directly in `pi_auto_sync.py`:
```python
username = os.getenv("KIOTVIET_USERNAME", "0913431718")
password = os.getenv("KIOTVIET_PASSWORD", "68686868")
```

## Testing from Local Machine

Run from Windows:
```powershell
python run_bash_sync.py
```

This uploads and executes the script on Pi.

---

**Status:** ✅ Ready for deployment
**Last Updated:** 2025-11-09
