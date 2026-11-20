#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
source ~/.bashrc
python -c 'import os;print("KEYLEN=",len(os.environ.get("GROQ_API_KEY","")))'
cd ~/code/jobscrapper
mv -f seen.db seen.bak 2>/dev/null
python scraper.py
