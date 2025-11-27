#!/bin/bash

orig_dir=$(pwd)

cd /var/www/myangelfujiya/nekoscience/bot/src || { echo "Bot src folder not found"; exit 1; }

source venv/bin/activate

python main.py

deactivate

cd "$orig_dir"
