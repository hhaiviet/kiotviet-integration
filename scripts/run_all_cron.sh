#!/bin/bash

export AZURE_STORAGE_CONNECTION_STRING='DefaultEndpointsProtocol=https;AccountName=kiotvietintegration;AccountKey=FEigNAELqRRYMuJRvTKqJM//Y3L7KUd8mmz0rEA4/0yx7fUQ5kEwMAxFUe2XoV/GsbinmsgHdgv7+ASt/oir6A==;EndpointSuffix=core.windows.net'
export AZURE_STORAGE_CONTAINER="kiotviet-data"
export KIOTVIET_USERNAME="0913431718"
export KIOTVIET_PASSWORD="68686868"

/home/codespace/.python/current/bin/python3 /workspaces/kiotviet-integration/scripts/kiotviet_run_all.py >> /workspaces/kiotviet-integration/cron.log 2>&1