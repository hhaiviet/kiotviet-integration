# 🎯 KiotViet ETL Monitoring Guide

**Ngày:** 9 November 2025  
**Bản Phát Hành:** 1.0 - Complete Monitoring Suite

---

## 📊 Monitoring Options

Có **2 cách** để monitor ETL pipeline:

### **Option 1: CLI Monitor** (Recommended - Đơn Giản) ⭐

Dùng command line để xem thống kê realtime.

**Lệnh:**

```bash
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py [command]"
```

### **Option 2: Web Dashboard** (Fancy - Phức Tạp)

Giao diện web với chart và realtime updates. Cần Flask.

```bash
# Install Flask on Pi
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && pip install flask"

# Start dashboard
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python dashboard_etl.py"

# Access from your computer
ssh -L 5000:localhost:5000 hhaiviet@116.102.136.220

# Open browser: http://localhost:5000
```

---

## 🖥️ CLI Monitor Commands

### 1️⃣ **Show Latest Run**
```bash
python monitor_etl.py latest
```

**Output:**
```
======================================================================
📊 LATEST ETL RUN
======================================================================
Time:          2025-11-09 11:55:56
Status:        ✅ SUCCESS

📤 STEP 1: Token Fetch
   Duration:   0.54s

📦 STEP 2: Products
   Count:      758 items
   Duration:   5.41s

📋 STEP 3: Invoices
   Count:      0 invoices
   Lines:      0 lines
   Duration:   2.06s

⏱️  TOTAL
   Duration:   9.44s
======================================================================
```

**Chi Tiết:**
- ✅ Status: SUCCESS / FAILED
- 📤 Token fetch duration
- 📦 Products loaded (758 items)
- 📋 Invoices loaded + lines
- ⏱️ Total execution time

---

### 2️⃣ **Show Today's Runs**
```bash
python monitor_etl.py today
```

**Output:**
```
======================================================================
📅 TODAY'S RUNS (3 total)
======================================================================
1. 2025-11-09 06:00:15 | ✅ | Products:  758 | Lines:     0 | 9.2s
2. 2025-11-09 12:00:42 | ✅ | Products:  758 | Lines:     0 | 9.5s
3. 2025-11-09 18:01:03 | ✅ | Products:  758 | Lines:     0 | 9.3s
======================================================================
```

**Chi Tiết:**
- Thời gian chạy
- Status (✅ Success / ❌ Failed)
- Số products loaded
- Số invoice lines
- Duration của mỗi run

---

### 3️⃣ **Show Last N Runs**
```bash
python monitor_etl.py last 10  # Last 10 runs (mặc định)
python monitor_etl.py last 20  # Last 20 runs
python monitor_etl.py last 50  # Last 50 runs
```

**Output:**
```
======================================================================
🔢 LAST 10 RUNS
======================================================================
#   Time                Status   Products   Lines    Duration
----------------------------------------------------------------------
1   2025-11-08 18:00    ✅ OK     758        0          9.2s
2   2025-11-09 00:00    ✅ OK     758        0          9.5s
3   2025-11-09 06:00    ✅ OK     758        0          9.3s
4   2025-11-09 12:00    ✅ OK     758        0          9.4s
5   2025-11-09 18:00    ✅ OK     758        0          9.2s
...
======================================================================
```

---

### 4️⃣ **Show Statistics**
```bash
python monitor_etl.py stats
```

**Output:**
```
======================================================================
📈 STATISTICS
======================================================================
Total Runs:           5
Successful:           5
Failed:               0
Success Rate:         100.0%

📊 AVERAGES (from successful runs)
Total Duration:       9.32s
Products per Run:     758 items
Invoice Lines:        0 lines
======================================================================
```

**Chi Tiết:**
- Tổng số run
- Số run thành công / thất bại
- Success rate (%)
- Trung bình:
  - Duration per run
  - Products per run
  - Invoice lines per run

---

### 5️⃣ **Watch Logs in Real-Time**
```bash
python monitor_etl.py watch              # Refresh mỗi 30s (mặc định)
python monitor_etl.py watch --interval 60  # Refresh mỗi 60s
python monitor_etl.py watch --idle-timeout 600  # Alert nếu no update 10 min
```

**Output:**
```
🔍 Watching ETL logs... (Press Ctrl+C to exit)
   Refresh every 30 seconds
   Alert if no update for 300 seconds

======================================================================
⏰ LIVE MONITOR - 2025-11-09 14:32:45
Latest:     2025-11-09 12:00:45 | 758 products | 0 lines | 9.4s
Today:      2 runs | 100% success
======================================================================

======================================================================
📊 LATEST ETL RUN
======================================================================
Time:          2025-11-09 12:00:45
Status:        ✅ SUCCESS
...
```

---

## 📈 Web Dashboard Features

Nếu bạn setup Flask, có thể truy cập web dashboard:

```bash
# 1. Install Flask
pip install flask

# 2. Start dashboard on Pi
python dashboard_etl.py

# 3. Access from your computer (port forwarding)
ssh -L 5000:localhost:5000 hhaiviet@116.102.136.220

# 4. Open browser
http://localhost:5000
```

**Dashboard hiển thị:**
- ✅ Latest run time & status
- 📊 Products exported (latest run)
- 📋 Invoice lines (latest run)
- ⏱️ Execution duration
- 📅 Today's runs count
- 📈 Success rate
- 📊 Last 10 runs table
- ⏳ Auto-refresh mỗi 10 seconds

---

## 🔄 Monitoring Strategy

### **Daily Check** (Hàng Ngày)
```bash
# Morning
python monitor_etl.py today

# Evening
python monitor_etl.py stats
```

### **Weekly Check** (Hàng Tuần)
```bash
# Check last 70 runs (1 tuần = 7 days × 4 runs/day = 28 runs)
python monitor_etl.py last 70

# Check statistics
python monitor_etl.py stats
```

### **Real-Time Monitoring** (24/7 Watch)
```bash
# Watch logs live (Ctrl+C to stop)
python monitor_etl.py watch

# Or use Web Dashboard:
python dashboard_etl.py
# Then http://localhost:5000
```

---

## 📊 What to Look For

### ✅ Good Indicators

```
Status: ✅ SUCCESS
Products: 758 items
Duration: 9-11 seconds
Lines: Vary (0-100 depending on new invoices)
Success Rate: 100%
```

### ⚠️ Warning Signs

| Warning | Cause | Action |
|---------|-------|--------|
| Duration > 20s | Slow network or API | Check `Duration: X.Xs` in logs |
| Status: ❌ FAILED | Token/API error | Check error message in latest run |
| Success Rate < 95% | Intermittent failures | Review failed runs, check logs |
| No new Lines | All invoices already synced | Normal - check checkpoint date |
| Same Products 758 | No new products today | Normal - depends on KiotViet data |

---

## 🔍 Deep Dive: Reading the Logs

### Log Location
```
/home/hhaiviet/kiotviet-integration/data/logs/etl.log
```

### View Raw Log
```bash
# Last 50 lines
tail -50 /home/hhaiviet/kiotviet-integration/data/logs/etl.log

# Follow log live
tail -f /home/hhaiviet/kiotviet-integration/data/logs/etl.log

# Count successful runs
grep "Status: ✅ SUCCESS" /home/hhaiviet/kiotviet-integration/data/logs/etl.log | wc -l

# Find errors
grep "❌" /home/hhaiviet/kiotviet-integration/data/logs/etl.log

# See run duration stats
grep "Duration:" /home/hhaiviet/kiotviet-integration/data/logs/etl.log | grep -o "[0-9]*\.[0-9]*"
```

### Sample Log Entry
```
2025-11-09 11:48:24,973 - kiotviet - INFO - ======================================================================
2025-11-09 11:48:24,973 - kiotviet - INFO - STEP 1: FETCH TOKEN FROM KIOTVIET API
2025-11-09 11:48:24,973 - kiotviet - INFO - ======================================================================
2025-11-09 11:48:24,974 - kiotviet - INFO - 📤 Sending login request to KiotViet API...
2025-11-09 11:48:25,507 - kiotviet - INFO - ✅ Token fetched successfully!
2025-11-09 11:48:25,508 - kiotviet - INFO -    Retailer: 248minimart, Branch: 291407
...
2025-11-09 11:48:34,357 - kiotviet - INFO - Status: ✅ SUCCESS
2025-11-09 11:48:34,357 - kiotviet - INFO - Duration: 9.4s
```

---

## 📱 Monitoring from Your Machine

### Option A: SSH + CLI Monitor
```bash
# Quick check
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest"

# Create alias (add to ~/.bashrc or ~/.zshrc)
alias kiotviet-monitor='ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py"'

# Then use:
kiotviet-monitor latest
kiotviet-monitor stats
kiotviet-monitor today
```

### Option B: Web Dashboard via SSH Tunnel
```bash
# Terminal 1: Open SSH tunnel
ssh -L 5000:localhost:5000 hhaiviet@116.102.136.220

# Terminal 2: Start dashboard on Pi
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python dashboard_etl.py"

# Browser: Open http://localhost:5000
```

### Option C: Tail Logs Live
```bash
# Watch log file live
ssh hhaiviet@116.102.136.220 "tail -f /home/hhaiviet/kiotviet-integration/data/logs/etl.log"

# Or with grep (only show Status lines)
ssh hhaiviet@116.102.136.220 "tail -f /home/hhaiviet/kiotviet-integration/data/logs/etl.log | grep -E 'Status|Duration|Products|Lines'"
```

---

## 🎨 Custom Monitoring Scripts

### Monitor Every Hour
```bash
# Create monitor.sh
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest" | head -20
    sleep 3600  # Every hour
done

# Run: bash monitor.sh
```

### Alert on Failure
```bash
#!/bin/bash
# Check every 10 minutes
while true; do
    result=$(ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest | grep Status")
    
    if [[ $result == *"FAILED"* ]]; then
        echo "🚨 ETL FAILED! Check immediately"
        # Optional: send email/Slack alert
    fi
    
    sleep 600  # Every 10 minutes
done
```

### Collect Weekly Report
```bash
#!/bin/bash
# Run every Sunday at 9 AM
0 9 * * 0 ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py stats" | mail -s "Weekly ETL Report" your@email.com
```

---

## 🚀 Quick Commands Reference

```bash
# Navigate to project
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest"

# Latest run - show all details
python monitor_etl.py latest

# Today's runs - quick overview
python monitor_etl.py today

# Statistics - overall health
python monitor_etl.py stats

# Last 20 runs - trend analysis
python monitor_etl.py last 20

# Live monitoring - real-time updates
python monitor_etl.py watch

# Web dashboard - fancy UI
python dashboard_etl.py

# Raw log - debug issues
tail -50 data/logs/etl.log
```

---

## 📞 Troubleshooting

### "Log file not found"
```bash
# Make sure data/logs directory exists
ssh hhaiviet@116.102.136.220 "mkdir -p /home/hhaiviet/kiotviet-integration/data/logs"

# Run ETL once to create log
python run_etl.py
```

### Monitor shows no data
```bash
# Check if log file has content
ssh hhaiviet@116.102.136.220 "wc -l /home/hhaiviet/kiotviet-integration/data/logs/etl.log"

# If empty, run ETL manually
python run_etl.py
```

### Dashboard won't start
```bash
# Install Flask
pip install flask

# Check if port 5000 is available
netstat -an | grep 5000

# Try different port
python dashboard_etl.py --port 8000
```

---

## 📈 Metrics Explained

### Duration Breakdown

| Step | Typical Time | What It Does |
|------|--------------|--------------|
| Token Fetch | 0.5s | Login to KiotViet API, get JWT |
| Products | 5-7s | Fetch all 758 products (paginated) |
| Invoices | 2-3s | Sync invoices incrementally |
| Upload | 1-2s | Upload CSVs to Azure Blob |
| **TOTAL** | **9-13s** | All 4 steps combined |

### Data Volumes

| Metric | Value | Notes |
|--------|-------|-------|
| Products | 758 items | Fixed count (248minimart retailer) |
| Invoice Lines | Varies | 0 if no new invoices since last sync |
| Products CSV | 250KB | 758 rows × 330 bytes/row |
| Invoice CSV | 1.3MB | ~9897 total lines (incremental) |

### Success Rate Target

```
100% = All runs successful ✅
95-99% = Excellent (occasional transient errors)
90-94% = Good (investigate failures)
< 90% = Problem (immediate action needed)
```

---

## 🎯 Summary

**Best Monitoring Practice:**

1. **Daily:** `python monitor_etl.py today`
2. **Weekly:** `python monitor_etl.py stats`
3. **Issues:** `python monitor_etl.py latest` + check logs
4. **Real-Time:** `python monitor_etl.py watch` or Web Dashboard

**Expected Normal Behavior:**
```
✅ Status: SUCCESS
📦 Products: 758 items
⏱️ Duration: 9-11 seconds
📊 Success Rate: 100%
📅 Runs: Every 6 hours (00, 06, 12, 18)
```

---

**Last Updated:** November 9, 2025  
**Version:** 1.0 - Complete Monitoring Suite
