#!/bin/bash

PID=$(pgrep -f "python.*test_strategy.py")

if [ -z "$PID" ]; then
    echo "cannot find running test_strategy.py "
else
    echo "find running test_strategy.py, PID: $PID, killing..."
    kill -9 $PID
    
    if [ $? -eq 0 ]; then
        echo "killed"
    else
        echo "failed to kill"
    fi
fi
