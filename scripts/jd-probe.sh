#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
curl -s -m 25 -A 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36' 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=ml%20intern&location=India&f_TPR=r86400&start=0' -o li.html -w 'size:%{size_download}\n'
grep -c 'base-search-card' li.html || echo NO-CARDS
grep -c -i 'challenge\|_0x[a-f0-9]\{6\}\|captcha' li.html || echo NO-CHALLENGE-MARKERS
grep -o -m3 'h3[^>]\{0,80\}' li.html
