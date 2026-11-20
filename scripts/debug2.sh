#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
cat ~/loop/loop.log 2>/dev/null || echo NO-LOG
echo "--- try foreground 5s ---"
timeout 5 python ~/loop.py --once; echo RC=$?
