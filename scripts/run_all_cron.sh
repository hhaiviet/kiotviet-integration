#!/bin/bash#!/bin/bash



# Load environment variables from .env file# Load environment variables from .env file

if [ -f "/workspaces/kiotviet-integration/.env" ]; thenif [ -f "/workspaces/kiotviet-integration/.env" ]; then

    export $(grep -v '^#' /workspaces/kiotviet-integration/.env | xargs)    export $(grep -v '^#' /workspaces/kiotviet-integration/.env | xargs)

fifi



# Set default values if not set# Set default values if not set

export AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-kiotviet-data}"export AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-kiotviet-data}"

export KIOTVIET_USERNAME="${KIOTVIET_USERNAME:-}"export KIOTVIET_USERNAME="${KIOTVIET_USERNAME:-}"

export KIOTVIET_PASSWORD="${KIOTVIET_PASSWORD:-}"export KIOTVIET_PASSWORD="${KIOTVIET_PASSWORD:-}"



/home/codespace/.python/current/bin/python3 /workspaces/kiotviet-integration/scripts/kiotviet_run_all.py >> /workspaces/kiotviet-integration/cron.log 2>&1/home/codespace/.python/current/bin/python3 /workspaces/kiotviet-integration/scripts/kiotviet_run_all.py >> /workspaces/kiotviet-integration/cron.log 2>&1