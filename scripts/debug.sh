#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
export TERM=xterm-256color
echo "--- tmux ---"
tmux ls
echo "--- loop procs ---"
ps aux | grep -v grep | grep loop || echo NO-LOOP-PROC
echo "--- pane ---"
tmux capture-pane -p -t loop 2>&1 | tail -5
echo "--- inbox/outbox ---"
ls ~/loop/inbox/ ~/loop/outbox/
