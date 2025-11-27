#!/bin/bash

orig_dir=$(pwd)

cd /var/www/myangelfujiya/nekoscience/web/src || { echo "./web/src <- No such file or directory"; exit 1; }

source venv/bin/activate

nohup python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload > web_uvicorn.log 2>&1 &

echo "logs -> web_uvicorn.log"

deactivate

cd "$orig_dir"
