#!/bin/bash

CUR_DIR=$(pwd)

LOG_FILE="$CUR_DIR/test_strategy.log"

nohup python3 -u test_strategy.py > "$LOG_FILE" 2>&1 &

PID=$!

echo "test_strategy is running... check log file: $LOG_FILE"
echo "PID: $PID"
