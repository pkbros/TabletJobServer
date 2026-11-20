#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
pkg install -y termux-api 2>&1 | tail -2
termux-wake-lock
echo WAKE-LOCK-HELD
