#!/usr/bin/bash
git checkout master
git pull origin master
./start.sh
git add .
git commit -m "Update proxies - $(date '+%A %d-%m-%Y %H:%M:%S %Z')"
git push https://Simatwa:$GITHUB_TOKEN@github.com/Simatwa/free-proxies.git