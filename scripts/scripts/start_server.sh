#!/bin/bash
cd /home/ubuntu/kaapi-junction-cafe
pkill -f app.py || true
nohup python3 app.py > app.log 2>&1 &
