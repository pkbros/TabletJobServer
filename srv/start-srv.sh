#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
mkdir -p ~/srv/files ~/srv/www ~/srv/api ~/srv/log
pkill -f "http.server 800" 2>/dev/null
pkill -f "srv/api/api.py" 2>/dev/null
cd ~
nohup python -m http.server 8000 --bind 127.0.0.1 --directory ~/srv/www > ~/srv/log/www.log 2>&1 &
nohup python -m http.server 8001 --bind 127.0.0.1 --directory ~/srv/files > ~/srv/log/files.log 2>&1 &
nohup python ~/srv/api/api.py > ~/srv/log/api.log 2>&1 &
sleep 2
curl -s -o /dev/null -w "www:%{http_code} " http://127.0.0.1:8000/
curl -s -o /dev/null -w "files:%{http_code} " http://127.0.0.1:8001/
curl -s http://127.0.0.1:8002/projects | head -c 120; echo
