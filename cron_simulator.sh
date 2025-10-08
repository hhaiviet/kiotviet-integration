#!/bin/bash
# Cron replacement for container environments
# Run this script in background to simulate cron behavior

while true; do
    current_minute=$(date +%M)
    current_hour=$(date +%H)

    # Check if it's time to run (every 30 minutes from 8-23 UTC)
    if [ $current_hour -ge 8 ] && [ $current_hour -le 23 ] && [ $(($current_minute % 30)) -eq 0 ]; then
        echo "$(date): Running scheduled task"
        /workspaces/kiotviet-integration/scripts/run_all_cron.sh
        # Wait 60 seconds to avoid duplicate runs
        sleep 60
    fi

    sleep 30
done