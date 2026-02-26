#!/bin/bash
# Engagement Summary Delivery Wrapper
# Generates yesterday's engagement summary and outputs for WhatsApp delivery

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PYTHON=/usr/bin/python3

# Generate summary
SUMMARY=$($PYTHON engagement_summary.py hn_digest_v2.db)

# Only output if there's a summary (not NO_SUMMARY)
if [ "$SUMMARY" != "NO_SUMMARY" ]; then
    echo "$SUMMARY"
fi

# Note: If empty output, cron job should skip WhatsApp send
