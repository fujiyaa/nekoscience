#!/bin/bash

orig_dir=$(pwd)

cd /var/www/myangelfujiya/nekoscience/api/target/release || { echo "Release folder not found"; exit 1; }

RUST_BACKTRACE=1 nohup ./neko_science_api > neko_science_api.log 2>&1 &

echo "api logs -> neko_science_api.log"

cd "$orig_dir"