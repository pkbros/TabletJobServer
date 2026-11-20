#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
bash ~/.termux/boot/start-tunnel
sleep 14
grep -m2 Registered ~/cloudflared.log | tail -2
