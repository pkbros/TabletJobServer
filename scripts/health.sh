#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
echo "--- procs ---"
pgrep -f 'telebo[t]' >/dev/null && echo bot:UP || echo bot:DOWN
pgrep -f 'start-jobs' >/dev/null && echo loop:UP || echo loop:DOWN
pgrep -f 'cloudflare[d]' >/dev/null && echo tunnel:UP || echo tunnel:DOWN
echo "--- config ---"
python -c 'import json;c=json.load(open("code/jobscrapper/config.json"));print("terms",len(c["terms"]),"locs",len(c["locations"]),"window",c["time_window"],"pages",c["pages_per_search"],"gap",c["request_gap_s"])'
echo "--- ports ---"
for p in 8000 8001 8022; do (curl -s -m 3 -o /dev/null -w "$p:%{http_code} " http://127.0.0.1:$p/) 2>/dev/null; done; echo
echo "--- mem ---"
free | head -2 | tail -1
echo "--- boot files ---"
ls ~/.termux/boot/
