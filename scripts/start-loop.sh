#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
pkill -f loop.py 2>/dev/null
nohup python ~/loop.py --loop 15 > ~/loop/loop.log 2>&1 &
disown
sleep 2
ps aux | grep -v grep | grep loop.py || echo NO-LOOP
