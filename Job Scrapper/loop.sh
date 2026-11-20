#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
source ~/.bashrc
cd ~/code/jobscrapper
if [ -f loop.pid ] && kill -0 "$(cat loop.pid)" 2>/dev/null; then
  exit 0
fi
echo $$ > loop.pid
trap "rm -f loop.pid" EXIT
while true; do
  python scraper.py --collect >> scraper.log 2>&1
  rc=$?
  if [ "$rc" = "75" ]; then
    sleep 240
  fi
  python scraper.py --digest >> scraper.log 2>&1
  sleep $((45 + RANDOM % 30))
done
