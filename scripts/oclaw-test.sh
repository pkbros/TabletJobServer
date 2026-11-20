#!/data/data/com.termux/files/usr/bin/bash
export PATH=/data/data/com.termux/files/usr/bin:$PATH
npm install -g openclaw 2>&1 | tail -6
echo ---VERIFY---
command -v openclaw && openclaw --version 2>&1 | head -2 || echo INSTALL-FAILED
