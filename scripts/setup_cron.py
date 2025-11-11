#!/usr/bin/env python3
"""
Setup Cron Job for KiotViet ETL Pipeline
Configures automated scheduling on Raspberry Pi
"""

import os
import subprocess
from pathlib import Path


def setup_cron_job(
    project_dir: str = "/home/hhaiviet/kiotviet-integration",
    schedule: str = "0 */6 * * *",  # Every 6 hours
    log_file: str = None,
) -> bool:
    """
    Setup cron job for ETL pipeline
    
    Args:
        project_dir: Path to project directory
        schedule: Cron expression (default: every 6 hours)
        log_file: Output log file (default: data/logs/etl.log)
    
    Returns:
        success: bool
    """
    
    if not log_file:
        log_file = f"{project_dir}/data/logs/etl.log"
    
    # Ensure log directory exists
    log_dir = str(Path(log_file).parent)
    
    # Build cron command
    cron_command = (
        f"{schedule} "
        f"cd {project_dir} && "
        f"export PYTHONUNBUFFERED=1 && "
        f"source venv/bin/activate && "
        f"python run_etl.py >> {log_file} 2>&1"
    )
    
    print(f"📝 Setting up cron job:")
    print(f"   Schedule: {schedule}")
    print(f"   Command: python run_etl.py")
    print(f"   Log file: {log_file}")
    print(f"   Directory: {project_dir}")
    print()
    
    try:
        # Get current crontab
        print("📖 Reading current crontab...")
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_crontab = result.stdout if result.returncode == 0 else ""
        
        # Check if job already exists
        job_identifier = "python run_etl.py"
        if job_identifier in current_crontab:
            print(f"⚠️  Job already exists in crontab")
            print(f"   Use 'crontab -e' to modify manually")
            return False
        
        # Add new job
        new_crontab = current_crontab + "\n" + cron_command + "\n"
        
        # Write new crontab
        print("✏️  Installing cron job...")
        process = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=new_crontab)
        
        if process.returncode != 0:
            print(f"❌ Failed to install cron job: {stderr}")
            return False
        
        print(f"✅ Cron job installed successfully!")
        print()
        print("📋 To verify, run:")
        print("   crontab -l")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """CLI for cron setup"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup cron job for KiotViet ETL Pipeline"
    )
    parser.add_argument(
        "--project-dir",
        default="/home/hhaiviet/kiotviet-integration",
        help="Project directory path",
    )
    parser.add_argument(
        "--schedule",
        default="0 */6 * * *",
        help="Cron expression (default: every 6 hours)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Log file path (default: data/logs/etl.log)",
    )
    
    args = parser.parse_args()
    
    success = setup_cron_job(
        project_dir=args.project_dir,
        schedule=args.schedule,
        log_file=args.log_file,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
