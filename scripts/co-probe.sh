#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
curl -s -m 25 -A 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36' 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=ml%20intern&location=India&f_TPR=r86400&start=0' -o li.html
grep -o -m3 'base-search-card__subtitle.\{0,200\}' li.html | head -c 600
echo
echo ---LOCKUP---
grep -o -m3 'lockup__subtitle.\{0,200\}' li.html | head -c 600
