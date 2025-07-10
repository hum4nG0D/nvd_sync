#!/bin/bash

# Set your NVD API key
export NVD_API_KEY="your_actual_api_key_here"

# Path to your Python script
SCRIPT_PATH="./nvd_delta_sync.py"

# Infinite loop to run every 3 hours
while true; do
    echo "[`date`] Starting NVD delta sync..."
    /usr/bin/python3 "$SCRIPT_PATH"

    echo "[`date`] Sync complete. Sleeping for 3 hours..."
    sleep 10800  # 3 hours = 10800 seconds
done
