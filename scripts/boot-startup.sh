#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
/data/data/com.termux/files/usr/bin/sshd
pkill -f loop.py 2>/dev/null
nohup python ~/loop.py --loop 15 > ~/loop/loop.log 2>&1 &
