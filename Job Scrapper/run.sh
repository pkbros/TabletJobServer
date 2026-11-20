#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
source ~/.bashrc
cd ~/code/jobscrapper
nohup python scraper.py > scraper.log 2>&1 &
