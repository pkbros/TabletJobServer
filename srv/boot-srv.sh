#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
mkdir -p ~/srv/files ~/srv/log
nohup python -m http.server 8000 --bind 0.0.0.0 --directory ~/srv/www > ~/srv/log/www.log 2>&1 &
nohup python -m http.server 8001 --bind 0.0.0.0 --directory ~/srv/files > ~/srv/log/files.log 2>&1 &
