#!/usr/bin/env python3
"""
Python-based scheduler using APScheduler
Alternative to cron for container environments
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sync_job():
    """Run the sync job"""
    try:
        logger.info("Starting scheduled sync job")
        result = subprocess.run(
            ["/workspaces/kiotviet-integration/scripts/run_all_cron.sh"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info("Sync job completed successfully")
        else:
            logger.error(f"Sync job failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("Sync job timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Error running sync job: {e}")

def main():
    """Main scheduler function"""
    logger.info("Starting Python scheduler (APScheduler)")

    # Create scheduler
    scheduler = BlockingScheduler()

    # Schedule job to run every 2 minutes
    trigger = CronTrigger(
        minute='*/2',  # Every 2 minutes
        timezone='UTC'
    )

    scheduler.add_job(
        run_sync_job,
        trigger=trigger,
        id='kiotviet_sync',
        name='KiotViet Data Sync',
        max_instances=1,  # Only one instance at a time
        replace_existing=True
    )

    logger.info("Scheduler started. Jobs will run every 2 minutes from 8 AM to 11 PM UTC")
    logger.info("Press Ctrl+C to stop the scheduler")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        scheduler.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()