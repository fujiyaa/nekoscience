#!/bin/bash

echo "-Nekoscience stack-"

API_PROC=$(pgrep -f neko_science_api)

if [ -n "$API_PROC" ]; then
    echo "Stopping API (PID: $API_PROC)"
    kill "$API_PROC"
else
    echo "Rust API is not running"
fi

WEB_PROC=$(pgrep -f "uvicorn.*main:app")

if [ -n "$WEB_PROC" ]; then
    echo "Stopping Web server (PID: $WEB_PROC)"
    kill "$WEB_PROC"
else
    echo "Web server is not running"
fi

BOT_PROC=$(pgrep -f "python main.py")

if [ -n "$BOT_PROC" ]; then
    echo "Stopping Bot (PID: $BOT_PROC)"
    kill "$BOT_PROC"
else
    echo "Bot is not running"
fi

echo "-exiting-"
