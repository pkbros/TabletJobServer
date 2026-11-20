#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
sleep 28800
cd ~/code/jobscrapper
nohup bash loop.sh > loop.log 2>&1 &
echo "loop resumed after cooldown: $(date)" >> loop.log
