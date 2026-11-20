#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
nohup ~/cloudflared tunnel run --token TOKEN_PLACEHOLDER > ~/cloudflared.log 2>&1 &
