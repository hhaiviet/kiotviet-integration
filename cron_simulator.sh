#!/bin/bash
# Cron replacement for container environments
# Run this script in background to simulate cron behavior

while true; do
    current_minute=$(date +%M)
    current_hour=$(date +%H)

    # Simple check: run every 2 minutes from 8-23 UTC
    hour_no_zero=$(echo $current_hour | sed 's/^0*//')  # Remove leading zeros
    if [ $hour_no_zero -ge 8 ] && [ $hour_no_zero -le 23 ] && [ $(($current_minute % 2)) -eq 0 ]; then
        echo "$(date): Running scheduled task"
        /workspaces/kiotviet-integration/scripts/run_all_cron.sh
        # Wait 60 seconds to avoid duplicate runs
        sleep 60
    fi

    sleep 10  # Check every 10 seconds
done