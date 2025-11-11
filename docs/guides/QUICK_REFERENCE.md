# 🎯 ETL Monitoring Quick Reference

## One-Liner Commands

```bash
# Show latest run (phiên bản gần nhất)
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest"

# Show today's runs (hôm nay chạy bao nhiêu lần)
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py today"

# Show statistics (thống kê overall)
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py stats"

# Show last 10 runs (10 lần chạy gần nhất)
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py last 10"

# Watch live (theo dõi realtime, cập nhật mỗi 30s)
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py watch"

# View raw logs (xem log thô)
ssh hhaiviet@116.102.136.220 "tail -50 /home/hhaiviet/kiotviet-integration/data/logs/etl.log"

# Follow logs live (theo dõi log realtime)
ssh hhaiviet@116.102.136.220 "tail -f /home/hhaiviet/kiotviet-integration/data/logs/etl.log"
```

---

## What Each Shows

| Command | Shows What | Use When |
|---------|-----------|----------|
| `latest` | Last run details | Quick sanity check |
| `today` | All runs from today | Check how many times ran |
| `stats` | Overall statistics | Check health & averages |
| `last N` | Last N runs | Trend analysis |
| `watch` | Real-time updates | Monitor while working |
| Raw logs | Unfiltered output | Debug specific issues |

---

## Normal Output Examples

### Latest Run (Everything Good)
```
Status:        ✅ SUCCESS
Products:      758 items
Duration:      9.4s
Invoices:      0 lines
```

### Today's Runs (Running Every 6h)
```
1. 2025-11-09 06:00:15 | ✅ | Products: 758 | Lines: 0 | 9.2s
2. 2025-11-09 12:00:42 | ✅ | Products: 758 | Lines: 0 | 9.5s
3. 2025-11-09 18:01:03 | ✅ | Products: 758 | Lines: 0 | 9.3s
```

### Statistics (All Healthy)
```
Total Runs:       15
Successful:       15
Failed:           0
Success Rate:     100.0%
Avg Duration:     9.32s
Avg Products:     758 items
```

---

## Red Flags to Watch For

| Problem | Looks Like | Action |
|---------|-----------|--------|
| Failed run | ❌ FAILED | Check latest run for error |
| Slow run | Duration > 20s | Check network or API status |
| Low success rate | 90-94% | Investigate failed runs |
| No new lines | Lines: 0 | Normal - check checkpoint |
| Missing run | Gap > 6h | Check cron job: `crontab -l` |

---

## Access from Windows

### Option 1: Direct SSH (Easiest)

```bash
# Copy-paste in PowerShell
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py latest"
```

### Option 2: Create Alias (PowerShell)

```powershell
# Add to Profile (open with: $PROFILE)
function kiotviet-monitor {
    param(
        [string]$cmd = "latest"
    )
    ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py $cmd"
}

# Then use:
kiotviet-monitor latest
kiotviet-monitor today
kiotviet-monitor stats
```

### Option 3: Web Dashboard

```bash
# Terminal 1: SSH tunnel
ssh -L 5000:localhost:5000 hhaiviet@116.102.136.220

# Terminal 2: Start dashboard
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python dashboard_etl.py"

# Browser: http://localhost:5000
```

---

## Expected Normal Behavior

```
Every 6 hours:
  00:00 ✅ Products: 758 | Duration: 9.2s
  06:00 ✅ Products: 758 | Duration: 9.3s
  12:00 ✅ Products: 758 | Duration: 9.4s
  18:00 ✅ Products: 758 | Duration: 9.3s

Monthly:
  Total runs: 4 × 30 = 120
  Success rate: 100%
  CSV files: Always up-to-date in Blob
```

---

## Cron Schedule

```
0 */6 * * * = Every 6 hours (00:00, 06:00, 12:00, 18:00)
0 0 * * *   = Daily at midnight
0 */3 * * * = Every 3 hours
```

Check current: `ssh hhaiviet@116.102.136.220 "crontab -l"`

---

## Key Metrics

| Metric | Normal Range | Warning | Critical |
|--------|-------------|---------|----------|
| Duration | 9-11s | 12-20s | > 20s |
| Products | 758 | 758 | ≠ 758 |
| Success Rate | 100% | 95-99% | < 95% |
| Lines (Daily) | 0-100 | - | - |
| Run Interval | 6h | > 7h | > 8h |

---

## Quick Checks

```bash
# Is cron running?
ssh hhaiviet@116.102.136.220 "crontab -l | grep run_etl"

# How many runs today?
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && grep 'LATEST ETL' data/logs/etl.log | wc -l"

# Success rate?
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && grep 'Status: ✅' data/logs/etl.log | wc -l"

# Average duration?
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python monitor_etl.py stats | grep 'Total Duration'"
```

---

## Troubleshooting Quick Fixes

```bash
# Cron not running? Check syntax
ssh hhaiviet@116.102.136.220 "crontab -e"

# Log file missing? Create it
ssh hhaiviet@116.102.136.220 "mkdir -p /home/hhaiviet/kiotviet-integration/data/logs"

# Monitor shows no data? Run ETL
ssh hhaiviet@116.102.136.220 "cd /home/hhaiviet/kiotviet-integration && source venv/bin/activate && python run_etl.py"

# Python not found? Activate venv
source /home/hhaiviet/kiotviet-integration/venv/bin/activate
```

---

## Summary

**Most Used Commands:**

```bash
# Quick check (daily)
python monitor_etl.py latest

# Check today's activity
python monitor_etl.py today

# Check overall health
python monitor_etl.py stats

# Real-time monitor (24/7)
python monitor_etl.py watch
```

**Dashboard URL (if Flask installed):**
```
http://localhost:5000
```

---

**Created:** November 9, 2025  
**Status:** Ready to Use ✅
