#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
cd ~
export TBOT_TOKEN="TOKEN_PLACEHOLDER"
export TBOT_OWNER="OWNER_PLACEHOLDER"
nohup python ~/code/telebot/bot.py > ~/code/telebot/bot.log 2>&1 &
