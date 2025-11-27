#!/bin/bash

orig_dir=$(pwd)

echo "-Nekoscience stack-"

cd /var/www/myangelfujiya/nekoscience/api/target/release || { echo "Rust release folder not found"; exit 1; }
RUST_BACKTRACE=1 nohup ./neko_science_api > neko_science_api.log 2>&1 &
echo "API -> neko_science_api.log"

cd /var/www/myangelfujiya/nekoscience/web/src || { echo "Web src folder not found"; exit 1; }
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload > web_uvicorn.log 2>&1 &
echo "Web -> web_uvicorn.log"
deactivate

cd /var/www/myangelfujiya/nekoscience/bot/src || { echo "Bot src folder not found"; exit 1; }
source venv/bin/activate
nohup python main.py > bot.log 2>&1 &
echo "Bot -> bot.log"
deactivate

cd "$orig_dir"

echo "-All started-"
