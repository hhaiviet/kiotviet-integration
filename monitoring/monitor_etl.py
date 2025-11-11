#!/usr/bin/env python3
"""
ETL Monitor - Real-time monitoring and statistics for KiotViet ETL Pipeline
Theo dõi quá trình ETL: dòng dữ liệu, thời gian refresh, duration, thống kê
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import subprocess

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ETLRun:
    """Single ETL execution record"""
    timestamp: datetime
    status: str  # "success" or "failed"
    token_duration: float = 0
    product_count: int = 0
    product_duration: float = 0
    invoice_count: int = 0
    invoice_lines: int = 0
    invoice_duration: float = 0
    upload_duration: float = 0
    total_duration: float = 0
    error_message: str = ""

    @property
    def formatted_time(self) -> str:
        """Return formatted timestamp"""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_success(self) -> bool:
        """Check if run was successful"""
        return self.status == "success"


class ETLMonitor:
    """Monitor ETL pipeline executions"""

    def __init__(self, log_file: Path = None):
        """Initialize monitor"""
        if log_file is None:
            # Try kiotviet.log first (main log file), fall back to etl.log
            kiotviet_log = PROJECT_ROOT / "data" / "logs" / "kiotviet.log"
            etl_log = PROJECT_ROOT / "data" / "logs" / "etl.log"
            log_file = kiotviet_log if kiotviet_log.exists() else etl_log
        
        self.log_file = Path(log_file)
        self.runs: List[ETLRun] = []

    def parse_log(self) -> List[ETLRun]:
        """Parse ETL log file and extract execution records"""
        self.runs = []
        
        if not self.log_file.exists():
            print(f"⚠️  Log file not found: {self.log_file}")
            return self.runs

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading log: {e}")
            return self.runs

        # Split by pipeline start markers (handle both formats)
        # Format 1: Full pipeline with 🚀 marker
        # Format 2: Simple script runs starting with "Starting invoice synchronization"
        
        # First try the full pipeline format
        pipeline_blocks = re.split(r'🚀 KIOTVIET ETL PIPELINE STARTED', content)
        
        for block_idx, block in enumerate(pipeline_blocks[1:], 1):  # Skip first (empty)
            try:
                run = self._parse_block(block)
                if run:
                    self.runs.append(run)
            except Exception as e:
                # Silently skip malformed blocks
                pass
        
        # Also parse simple script runs (kiotviet_run_all.py format)
        # Find all blocks that start with "Starting invoice synchronization"
        lines = content.split('\n')
        current_block_lines = []
        
        for line in lines:
            if 'Starting invoice synchronization' in line:
                # Start of a new block
                if current_block_lines:
                    # Process previous block
                    try:
                        block_text = '\n'.join(current_block_lines)
                        run = self._parse_script_block(block_text)
                        if run and not any(r.timestamp == run.timestamp for r in self.runs):
                            self.runs.append(run)
                    except:
                        pass
                current_block_lines = [line]
            else:
                current_block_lines.append(line)
        
        # Process last block
        if current_block_lines:
            try:
                block_text = '\n'.join(current_block_lines)
                run = self._parse_script_block(block_text)
                if run and not any(r.timestamp == run.timestamp for r in self.runs):
                    self.runs.append(run)
            except:
                pass

        return sorted(self.runs, key=lambda r: r.timestamp)

    def _parse_block(self, block: str) -> Optional[ETLRun]:
        """Parse a single pipeline block from log"""
        lines = block.split('\n')
        
        # Extract timestamp (first line should have it)
        timestamp = None
        for line in lines[:5]:
            # Pattern: 2025-11-09 11:48:24,967
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if match:
                try:
                    timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    break
                except:
                    pass

        if not timestamp:
            return None

        run = ETLRun(timestamp=timestamp, status="unknown")

        # Extract token duration
        for line in lines:
            if "Login failed" in line or "✅ Token fetched" in line:
                run.token_duration = self._extract_duration(lines, line)

        # Extract product data
        for line in lines:
            if "Product export finished" in line or "products=" in line:
                match = re.search(r'products=(\d+)', line)
                if match:
                    run.product_count = int(match.group(1))
                
                match = re.search(r'duration=([\d.]+)s', line)
                if match:
                    run.product_duration = float(match.group(1))

        # Extract invoice data
        for line in lines:
            if "Invoice sync finished" in line or "invoices=" in line:
                match = re.search(r'invoices=(\d+)', line)
                if match:
                    run.invoice_count = int(match.group(1))
                
                match = re.search(r'lines=(\d+)', line)
                if match:
                    run.invoice_lines = int(match.group(1))
                
                match = re.search(r'duration=([\d.]+)s', line)
                if match:
                    run.invoice_duration = float(match.group(1))

        # Extract total duration
        for line in lines:
            if "Duration:" in line and "Duration: ✅ SUCCESS" not in line:
                match = re.search(r'Duration: ([\d.]+)s', line)
                if match:
                    run.total_duration = float(match.group(1))

        # Check status (look for success/failure indicator)
        if "Status: ✅ SUCCESS" in block:
            run.status = "success"
        elif "Status: ❌ FAILED" in block or "Pipeline error" in block:
            run.status = "failed"
            # Extract error message
            for line in lines:
                if "Pipeline error" in line or "failed" in line.lower():
                    run.error_message = line.strip()
                    break
        else:
            # Default to success if we got most fields
            if run.product_count > 0:
                run.status = "success"

        # Require at least product data to be valid
        if run.status != "unknown" or run.product_count > 0:
            return run

        return None

    def _parse_script_block(self, block: str) -> Optional[ETLRun]:
        """Parse a script run block (kiotviet_run_all.py format without pipeline marker)"""
        lines = block.split('\n')
        
        # Extract timestamp from first line with "Starting invoice synchronization"
        timestamp = None
        for line in lines:
            if "Starting invoice synchronization" in line:
                # Pattern: 2025-11-09 14:13:41,753
                match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if match:
                    try:
                        timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                        break
                    except:
                        pass
        
        if not timestamp:
            return None
        
        run = ETLRun(timestamp=timestamp, status="success")
        
        # Extract invoice data
        for line in lines:
            if "Invoice sync finished" in line:
                match = re.search(r'invoices=(\d+)', line)
                if match:
                    run.invoice_count = int(match.group(1))
                
                match = re.search(r'lines=(\d+)', line)
                if match:
                    run.invoice_lines = int(match.group(1))
                
                match = re.search(r'duration=([\d.]+)s', line)
                if match:
                    run.invoice_duration = float(match.group(1))
        
        # Extract product data
        for line in lines:
            if "Product export finished" in line:
                match = re.search(r'products=(\d+)', line)
                if match:
                    run.product_count = int(match.group(1))
                
                match = re.search(r'duration=([\d.]+)s', line)
                if match:
                    run.product_duration = float(match.group(1))
        
        # Calculate total duration if both services ran
        if run.invoice_duration and run.product_duration:
            # Total is approximately sum of both durations (they run sequentially)
            run.total_duration = run.invoice_duration + run.product_duration
        elif run.product_duration:
            # If only product ran, use that duration
            run.total_duration = run.product_duration
        
        # Require at least product data
        if run.product_count > 0:
            return run
        
        return None

    def _extract_duration(self, lines: List[str], reference_line: str) -> float:
        """Extract duration from nearby lines"""
        # Look for "duration=X.Xs" pattern in the block
        for line in lines:
            match = re.search(r'duration=([\d.]+)s', line)
            if match:
                return float(match.group(1))
        return 0

    def get_latest_run(self) -> Optional[ETLRun]:
        """Get most recent run"""
        return self.runs[-1] if self.runs else None

    def get_today_runs(self) -> List[ETLRun]:
        """Get all runs from today"""
        today = datetime.now().date()
        return [r for r in self.runs if r.timestamp.date() == today]

    def get_last_n_runs(self, n: int) -> List[ETLRun]:
        """Get last N runs"""
        return self.runs[-n:]

    def get_statistics(self) -> Dict:
        """Calculate statistics"""
        if not self.runs:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "success_rate": 0,
            }

        total = len(self.runs)
        successful = len([r for r in self.runs if r.is_success])
        failed = total - successful

        success_rate = (successful / total * 100) if total > 0 else 0

        # Calculate averages
        avg_total_duration = sum(r.total_duration for r in self.runs if r.is_success) / successful if successful > 0 else 0
        avg_products = sum(r.product_count for r in self.runs if r.is_success) / successful if successful > 0 else 0
        avg_invoices = sum(r.invoice_lines for r in self.runs if r.is_success) / successful if successful > 0 else 0

        return {
            "total_runs": total,
            "successful_runs": successful,
            "failed_runs": failed,
            "success_rate": success_rate,
            "avg_total_duration": avg_total_duration,
            "avg_products": avg_products,
            "avg_invoice_lines": avg_invoices,
        }

    def print_latest(self):
        """Print latest run"""
        if not self.runs:
            print("❌ No runs found in log")
            return

        run = self.get_latest_run()
        
        print("\n" + "=" * 70)
        print("📊 LATEST ETL RUN")
        print("=" * 70)
        print(f"Time:          {run.formatted_time}")
        print(f"Status:        {'✅ SUCCESS' if run.is_success else '❌ FAILED'}")
        print()
        print("📤 STEP 1: Token Fetch")
        print(f"   Duration:   {run.token_duration:.2f}s")
        print()
        print("📦 STEP 2: Products")
        print(f"   Count:      {run.product_count} items")
        print(f"   Duration:   {run.product_duration:.2f}s")
        print()
        print("📋 STEP 3: Invoices")
        print(f"   Count:      {run.invoice_count} invoices")
        print(f"   Lines:      {run.invoice_lines} lines")
        print(f"   Duration:   {run.invoice_duration:.2f}s")
        print()
        print("⏱️  TOTAL")
        print(f"   Duration:   {run.total_duration:.2f}s")
        
        if run.error_message:
            print()
            print(f"❌ Error: {run.error_message}")
        
        print("=" * 70 + "\n")

    def print_today_runs(self):
        """Print all runs from today"""
        runs = self.get_today_runs()
        
        print("\n" + "=" * 70)
        print(f"📅 TODAY'S RUNS ({len(runs)} total)")
        print("=" * 70)
        
        if not runs:
            print("No runs today yet")
            print("=" * 70 + "\n")
            return

        for i, run in enumerate(runs, 1):
            status_icon = "✅" if run.is_success else "❌"
            print(f"{i}. {run.formatted_time} | {status_icon} | Products: {run.product_count:4d} | Lines: {run.invoice_lines:5d} | {run.total_duration:.1f}s")

        print("=" * 70 + "\n")

    def print_last_n(self, n: int = 10):
        """Print last N runs"""
        runs = self.get_last_n_runs(n)
        
        print("\n" + "=" * 70)
        print(f"🔢 LAST {n} RUNS")
        print("=" * 70)
        print(f"{'#':<3} {'Time':<19} {'Status':<8} {'Products':<10} {'Lines':<8} {'Duration':<10}")
        print("-" * 70)
        
        for i, run in enumerate(runs, 1):
            status = "✅ OK" if run.is_success else "❌ FAIL"
            time_str = run.timestamp.strftime("%Y-%m-%d %H:%M")
            print(f"{i:<3} {time_str:<19} {status:<8} {run.product_count:<10} {run.invoice_lines:<8} {run.total_duration:>6.1f}s")

        print("=" * 70 + "\n")

    def print_statistics(self):
        """Print statistics"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("📈 STATISTICS")
        print("=" * 70)
        print(f"Total Runs:           {stats['total_runs']}")
        print(f"Successful:           {stats['successful_runs']}")
        print(f"Failed:               {stats['failed_runs']}")
        print(f"Success Rate:         {stats['success_rate']:.1f}%")
        print()
        print("📊 AVERAGES (from successful runs)")
        print(f"Total Duration:       {stats['avg_total_duration']:.2f}s")
        print(f"Products per Run:     {stats['avg_products']:.0f} items")
        print(f"Invoice Lines:        {stats['avg_invoice_lines']:.0f} lines")
        print("=" * 70 + "\n")

    def print_summary_live(self):
        """Print live summary (single line, can be updated)"""
        if not self.runs:
            print("⏳ No ETL runs yet. Waiting for first execution...")
            return

        run = self.get_latest_run()
        today_runs = self.get_today_runs()
        stats = self.get_statistics()

        print("\r" + "=" * 70, end="")
        print(f"\n⏰ LIVE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Latest:     {run.formatted_time} | {run.product_count} products | {run.invoice_lines} lines | {run.total_duration:.1f}s")
        print(f"Today:      {len(today_runs)} runs | {stats['success_rate']:.0f}% success")
        print("=" * 70)


def watch_logs(interval: int = 30, max_idle_time: int = 300):
    """Watch logs and update every N seconds"""
    import time
    
    monitor = ETLMonitor()
    last_update = None
    idle_time = 0

    print("🔍 Watching ETL logs... (Press Ctrl+C to exit)")
    print(f"   Refresh every {interval} seconds")
    print(f"   Alert if no update for {max_idle_time} seconds")
    print()

    try:
        while True:
            # Parse logs
            monitor.parse_log()
            
            # Check if we have new data
            current_run = monitor.get_latest_run()
            
            if current_run and current_run.timestamp != last_update:
                # Clear screen and print fresh
                os.system('clear' if os.name == 'posix' else 'cls')
                
                monitor.print_summary_live()
                monitor.print_latest()
                
                last_update = current_run.timestamp
                idle_time = 0
            else:
                idle_time += interval
                
                if idle_time >= max_idle_time:
                    print(f"⚠️  No update for {idle_time}s. ETL might not be running.")
                    print(f"   Next scheduled run: Check crontab with: crontab -l")
                    print()
                    idle_time = 0

            # Wait before checking again
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped")


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="ETL Pipeline Monitor - Real-time monitoring and statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_etl.py latest          # Show latest run
  python monitor_etl.py today           # Show today's runs
  python monitor_etl.py last 20         # Show last 20 runs
  python monitor_etl.py stats           # Show statistics
  python monitor_etl.py watch           # Watch logs in real-time
  python monitor_etl.py watch --interval 60  # Watch with 60s refresh
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Latest command
    subparsers.add_parser("latest", help="Show latest ETL run")

    # Today command
    subparsers.add_parser("today", help="Show all runs from today")

    # Last N command
    last_parser = subparsers.add_parser("last", help="Show last N runs")
    last_parser.add_argument("count", type=int, nargs='?', default=10, help="Number of runs to show (default: 10)")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch logs in real-time")
    watch_parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds (default: 30)")
    watch_parser.add_argument("--idle-timeout", type=int, default=300, help="Alert after N seconds idle (default: 300)")

    # Log file option
    parser.add_argument("--log-file", type=str, help="Path to ETL log file")

    args = parser.parse_args()

    # Create monitor
    monitor = ETLMonitor(log_file=Path(args.log_file) if args.log_file else None)
    monitor.parse_log()

    # Execute command
    if args.command == "latest":
        monitor.print_latest()
    elif args.command == "today":
        monitor.print_today_runs()
    elif args.command == "last":
        monitor.print_last_n(args.count)
    elif args.command == "stats":
        monitor.print_statistics()
    elif args.command == "watch":
        watch_logs(interval=args.interval, max_idle_time=args.idle_timeout)
    else:
        # Default: show latest
        monitor.print_latest()
        monitor.print_today_runs()
        monitor.print_statistics()


if __name__ == "__main__":
    main()
