#!/usr/bin/env bash
# Generate a random build log line and append it to a CSV
STATUS_LIST=(success success failed)
STATUS=${STATUS_LIST[$RANDOM % ${#STATUS_LIST[@]}]}
DURATION=$((30 + RANDOM % 150))
FAILED_TESTS=0
if [ "$STATUS" = "failed" ]; then
  FAILED_TESTS=$((1 + RANDOM % 5))
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TIMESTAMP,$STATUS,$DURATION,$FAILED_TESTS" >> data/local_metrics.csv
