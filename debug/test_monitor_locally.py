#!/usr/bin/env python3
"""
Local test to verify monitor parsing works with fresh data
"""

import sys
sys.path.insert(0, '/home/hhaiviet/kiotviet-integration')

# Simulate the log content from the Pi
sample_log = """2025-11-09 11:55:56,789 - kiotviet - INFO - kiotviet_run_all.py:107 - Starting invoice synchronization
2025-11-09 11:55:56,792 - kiotviet.InvoiceService - INFO - invoice_service.py:89 - Starting invoice sync | mode=incremental
2025-11-09 11:56:01,195 - kiotviet.InvoiceService - INFO - invoice_service.py:167 - Invoice sync finished | invoices=0 | lines=0 | duration=4.4s
2025-11-09 11:56:02,296 - kiotviet - INFO - kiotviet_run_all.py:113 - Starting product export
2025-11-09 11:56:02,299 - kiotviet.ProductService - INFO - product_service.py:90 - Starting product export | page_size=100
2025-11-09 11:56:08,186 - kiotviet.ProductService - INFO - product_service.py:100 - Product export finished | products=758 | duration=5.8s

2025-11-09 14:13:41,753 - kiotviet - INFO - kiotviet_run_all.py:107 - Starting invoice synchronization
2025-11-09 14:13:41,756 - kiotviet.InvoiceService - INFO - invoice_service.py:89 - Starting invoice sync | mode=incremental
2025-11-09 14:13:46,158 - kiotviet.InvoiceService - INFO - invoice_service.py:167 - Invoice sync finished | invoices=0 | lines=0 | duration=4.4s
2025-11-09 14:13:47,259 - kiotviet - INFO - kiotviet_run_all.py:113 - Starting product export
2025-11-09 14:13:47,262 - kiotviet.ProductService - INFO - product_service.py:90 - Starting product export | page_size=100
2025-11-09 14:13:53,086 - kiotviet.ProductService - INFO - product_service.py:100 - Product export finished | products=758 | duration=5.8s

2025-11-09 14:15:07,009 - kiotviet - INFO - kiotviet_run_all.py:107 - Starting invoice synchronization
2025-11-09 14:15:07,012 - kiotviet.InvoiceService - INFO - invoice_service.py:89 - Starting invoice sync | mode=incremental
2025-11-09 14:15:11,398 - kiotviet.InvoiceService - INFO - invoice_service.py:167 - Invoice sync finished | invoices=0 | lines=0 | duration=3.6s
2025-11-09 14:15:12,499 - kiotviet - INFO - kiotviet_run_all.py:113 - Starting product export
2025-11-09 14:15:12,502 - kiotviet.ProductService - INFO - product_service.py:90 - Starting product export | page_size=100
2025-11-09 14:15:13,965 - kiotviet.ProductService - INFO - product_service.py:100 - Product export finished | products=758 | duration=7.0s"""

# Test parsing
from monitor_etl import ETLMonitor, ETLRun
from datetime import datetime
import tempfile
import os

# Create a temporary log file
with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
    f.write(sample_log)
    temp_log = f.name

try:
    # Create monitor with temp log
    monitor = ETLMonitor(log_file=temp_log)
    
    # Parse the log
    runs = monitor.parse_log()
    
    print(f"\n✅ Successfully parsed {len(runs)} runs!\n")
    
    for i, run in enumerate(runs, 1):
        print(f"Run {i}:")
        print(f"  Time:           {run.timestamp}")
        print(f"  Status:         {run.status}")
        print(f"  Products:       {run.product_count} items")
        print(f"  Invoices:       {run.invoice_count}")
        print(f"  Product time:   {run.product_duration}s")
        print(f"  Invoice time:   {run.invoice_duration}s")
        print(f"  Total time:     {run.total_duration}s")
        print()
    
    # Check latest
    latest = monitor.get_latest_run()
    if latest:
        print(f"✅ Latest run: {latest.timestamp} - {latest.product_count} products, {latest.total_duration}s total")
    else:
        print("❌ No latest run found!")
        
finally:
    # Clean up
    os.unlink(temp_log)
