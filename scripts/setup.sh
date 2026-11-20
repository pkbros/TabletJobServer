#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
pip install -q paho-mqtt requests
echo PIP-DONE
echo '{"shell":"uptime"}' > ~/loop/inbox/t1.json
python ~/loop.py --once
echo ---RESULT---
cat ~/loop/outbox/*
