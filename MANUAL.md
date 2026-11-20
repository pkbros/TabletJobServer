# Tablet Server — MANUAL.md
Device: Lenovo YT3-X50L (Yoga Tab 3 10 LTE) · LineageOS 17.1 mimbrelte, no GApps
Tablet IP (static): `192.168.1.50` · SSH port: `8022` · user: any (key auth, try `root` or default)
PC project folder: `D:\projects\ProjectLenovoUnlock\`

## 1. Open a terminal on the tablet FROM YOUR PC (SSH)
1. On PC open **PowerShell** (Win+X → Terminal).
2. Run: `ssh mind2`
   (Shortcut configured in `~/.ssh/config` → 192.168.1.50:8022 with key `~/.ssh/mind2`.
   Long form, if the shortcut ever breaks:
   `ssh -i ~/.ssh/tablet -p 8022 192.168.1.50`)
3. You land in Termux (`$` prompt). This is the tablet's Linux.
4. Keep this window open; open more with the same command for parallel work.
5. Exit any session with `exit`.

If it says `Network is unreachable` / timeout → tablet IP changed or sshd died (see §6).

## 2. Termux basics (inside the SSH session)
- `pwd`, `ls`, `cd ~` — you start in home (`/data/data/com.termux/files/home`).
- `pkg install <name>` — install tools (needs internet). Installed now: git, python, nodejs, openssh, tmux, sqlite, mosquitto, micro? (if not: `pkg install micro`).
- `pkg update && pkg upgrade` — update everything (slow on this chip, run rarely).
- `pip install <pkg>` — Python packages (`paho-mqtt`, `requests` already present).
- `uname -a`, `uptime`, `free`, `df -h` — system info. Expect ~280MB available; that is NORMAL here.
- In SSH you have a full shell (pipes OK).

## 3. Background task loop — REMOVED 2026-10-13 (user wants clean Termux, gradual learning)
- Tablet is clean: no extra software, only SSH autostart remains.
- Sources kept in PC folder `scripts/` for later, when you ask for them.

## 4. API keys — SKIPPED (nothing running that needs one; revisit later)

## 5. MQTT quick test (local broker)
Terminal 1: `mosquitto_sub -t home/test -v`
Terminal 2: `mosquitto_pub -t home/test -m hello-tablet`
Start broker if needed: `mosquitto -d` (configless, localhost). No auth by default — LAN-only, fine behind home router.

## 6. Troubleshooting
- SSH timeout → 1) tablet on same WiFi? 2) IP changed? check tablet Settings > About > Status, or USB fallback below. 3) sshd dead → USB: `adb shell "run-as com.termux /data/data/com.termux/files/usr/bin/sshd"`.
- WiFi doze (SSH dies when screen sleeps; no UI switch in this build) — applied:
  `adb shell "settings put global wifi_sleep_policy 2"` (2 = never sleep),
  `adb shell "dumpsys deviceidle whitelist +com.termux"` (+ `+com.termux.boot`),
  plus Termux:API app + `pkg install termux-api` + `termux-wake-lock` (kernel wake lock, survives screen-off; in `~/.termux/boot/start-sshd`). Driver proof: dmesg `wlan_suspend` at kill time.
- USB fallback (needs cable + platform-tools in `C:\Users\123pk\AppData\Local\Temp\platform-tools\`):
  `adb devices` → `adb shell` (root shell, full control).
- Services silent → check their logs in `~/srv/log/`, restart with `bash ~/srv/start-srv.sh` (see §10).
- High load after boot is normal (settling). `uptime` load >4 for hours = something stuck; check `top` (press q to quit).
- Reboot path: power menu → Restart → 2-3 min → Termux:Boot runs `~/.termux/boot/start-sshd` (SSH only). Verify with SSH.
- VERIFIED 2026-10-13: screen-off sleep keeps SSH alive (wake lock); full power-off → boot → SSH back on its own (uptime 1 min on reconnect).

## 7. Safety / restore (all in project folder)
- `partitions/` — persist, modemst1/2, boot, recovery, aboot… (irreplaceable, never delete).
- `images/downloads/` — Lineage ROM + recovery + TWRP x50 + patcher (reflash set).
- PC `~/.ssh/mind2*` — your login key. Keep a backup copy somewhere safe (project `ssh/` folder was removed by user).
- `scripts/` — spare helper scripts (tablet copies pushed from here when needed).
- Never factory-reset from Android settings (wipes Termux). Never flash wrong-variant images (mimbrelte only).

## 9. Pairing a NEW pc with the tablet from scratch (both strangers)
SSH trust has two directions, set up once:
A. Tablet trusts YOUR pc: your pc's PUBLIC key must be appended to tablet `~/.ssh/authorized_keys`.
B. Your pc trusts the TABLET: on first connect, verify the host fingerprint, type `yes`.
Recipe for a new pc:
1. On the new pc: `ssh-keygen -t ed25519` (Enter through prompts) → `~/.ssh/id_ed25519.pub`.
2. Move that `.pub` onto the tablet by ONE of:
   - USB+adb (no network needed): tablet USB debugging on, cable in, then on pc:
     `adb push ~/.ssh/id_ed25519.pub /data/local/tmp/new.pub`
     `adb shell "cat /data/local/tmp/new.pub >> /data/data/com.termux/files/home/.ssh/authorized_keys"`
     (needs root adbd: `adb root` first; fix owner: `chown 10120:10120 .../authorized_keys` — confirm uid via `dumpsys package com.termux | grep userId`)
   - Or via tablet screen: open Termux, run `passwd`, set a temporary password; from pc:
     `ssh-copy-id -p 8022 <tablet-ip>` (type password once), then remove password login by deleting it (`passwd -d`? simpler: leave key-only after first key works — set a strong password or `passwd -l`).
3. From new pc: `ssh -p 8022 <tablet-ip>` → `yes` → in.
This is exactly how the current pc was paired (method: USB+adb push).

## 10. Serving the internet via Cloudflare Tunnel (no router access needed)
Tablet: `~/cloudflared` v2026.10.0 (32-bit arm, verified working).
STATUS 2026-10-13: TUNNEL LIVE (4 conns, bom/del edges). Autostart: `~/.termux/boot/start-tunnel` (token inside, 700).
PUBLIC: https://home.mind2.xyz → :8000 (verified loads). :8001 route (^/files path) pending — files LAN-only meanwhile.
GOTCHA: tablet ships with NO /etc/resolv.conf → Go binaries fail DNS on ::1. Fix (adb root, once):
`mount -o remount,rw /` + write `nameserver 1.1.1.1 / 8.8.8.8` to /etc/resolv.conf.
NOTE: ROM reflash wipes it (lives on system) — reapply after every flash. Reapplied 2026-10-13 post-reflash.
YOUR STEPS (Cloudflare dashboard, free account):
YOUR STEPS (Cloudflare dashboard, free account):
1. Sign up at dash.cloudflare.com → Add site `mind2.xyz` → change nameservers at your registrar to the two Cloudflare gives you. Wait till status Active.
2. Zero Trust → Networks → Tunnels → Create tunnel → name it `tablet` → copy the install TOKEN (long string, `eyJh...`).
3. Give the token to your assistant (paste in chat) — tablet runs: `./cloudflared tunnel run --token TOKEN`.
4. Back in dashboard → tunnel → Public Hostnames → Add: e.g. `home.mind2.xyz` → `http://localhost:8000`.
Tablet services (assistant side): test page + file server + JSON API all on localhost ports, Cloudflare routes subdomains to each.
STATUS: local services LIVE (verified 200s) — :8000 www (test homepage), :8001 files, bound 0.0.0.0 since 2026-10-13 (were localhost-only; browsers refused). :8002 api DEFERRED per user (code kept in project `srv/api/`). Autostart: `~/.termux/boot/start-srv`. Starter: `~/srv/start-srv.sh` (source: project `srv/`).
USER PROJECTS: `~/code/jobscrapper/` (see `Job Scrapper/PRD.md`). Weather demo app removed 2026-10-13 per user.
Commands used:
- `scp cloudflared mind2:cloudflared && ssh mind2 "chmod 700 ~/cloudflared; ./cloudflared --version"`

## 11. Telegram bot — GATEWAY pattern (live 2026-10-13, polling — works from anywhere, no tunnel needed)
- Code: `~/code/telebot/bot.py` (stdlib+requests). ONE Telegram face for ALL local apps.
- Routes: /status /jobs (2 buttons: Show = last digest w/ links, Force search = fresh scan + timer reset) /files /id /help.
- Digest rule: FIT-only listings + skipped count (skips never sent). Empty run → "nothing new" heartbeat.
- Cooldown 2026-10-14: loop paused 8h (IP throttled by our own testing); self-resumes via sleeper, ~evening.
- Usage: /jobs show → see pairs; `/jobs add ml intern | Noida, India` → next runs include it; /jobs run-now → immediate scan.
- Outbound: any app drops text in `~/srv/alerts/` → bot forwards to OWNER every ~100s. Apps need no Telegram code.
- Lock-down: `TBOT_OWNER=<chat-id>` env rejects strangers (`/id` answers anyone). Extra delivery chats in `~/code/telebot/recipients.txt` (group -1004411353963 added 2026-10-13). OWNER=2137108927 set 2026-10-13.
- INCIDENT 2026-10-18 ~03:54→05:32 IST: bot went FULLY SILENT (no digests, /commands dead) — tablet-wide DNS flap (Errno 7) hardened; poller backoff stuck at fail 18; alert-forwarding failing same way. NOTHING on the tablet can warn you over a dead net (structural mute). Self-recovered on backoff once DNS returned (~05:32; proven by a dropped test alert delivered+deleted). Diagnosis order: 1) probe tablet DNS, 2) pgrep single bot instance, 3) check spool. DNS-bypass fix (DoH via 1.1.1.1 for bot.py+scraper.py, ~30 lines, no root) = the durable patch; parked owner decision.
- Incident 2026-10-14 ~03:50: network blip (429 then 502) wedged the poller silently — alive but mute.
  Fix: exponential backoff on poll errors (5s→300s cap) instead of fixed 5s hammer. Job loop was FINE throughout
  (ran 08:53; pgrep missed it because boot runs it as `start-jobs`, not `loop.sh` — check both names).
- Duplicate schedulers (2026-10-15): boot `start-jobs` + manual `loop.sh` stacked → double digests.
  Fix: pidfile guard in loop.sh (second instance exits) + killers match BOTH names + boot file synced from loop.sh.
- Older gotcha: stale bot duplicates never ack updates (fix: separate safe-kill, fresh single start; boot scripts must not pkill — TABLET.md §7).
- Incident 2026-10-14 eve: scraper crash-looped SILENTLY on corrupt config.json (my trailing comma) — no digest at all.
  Fix: config parse wrapped → writes ALARM digest instead of dying mute. Lesson: every crash path must shout.
- Token: env `TBOT_TOKEN` at start (kept OUT of files). PERMANENT: `~/.termux/boot/start-tbot` (token inside, 700).
- GOTCHA: HTTP 409 = another session holds the bot (was: stale Botpress webhook). Diagnose `getWebhookInfo`, fix `deleteWebhook`. One poller only.
- Token hygiene: chat-exposed tokens → BotFather /revoke if misbehavior.
- Note 2026-10-13: heavyweight harnesses (OpenClaw) fail here — native `tree-sitter` build, no armv7. Python bot + direct API calls is the viable pattern.
- GOTCHA: HTTP 409 Conflict = another session holds the bot (here: stale Botpress webhook). Diagnose: `getWebhookInfo`; fix: `deleteWebhook`. Never run two pollers.
- Token hygiene: past tokens in chat logs should be revoked via BotFather /revoke if bot misbehaves.

## 12. Job Scrapper (v2 paced-collector LIVE 2026-10-17)
- `~/code/jobscrapper/`: scraper.py (v2: `--collect` / `--digest` modes + legacy burst) + loop.sh (60s ticks) + config.json + seen.db. PRD: project `Job Scrapper/PRD.md`.
- v2 design (owner-approved): collector ≤2 req/min round-robin over ALL 10 pairs + detail trickle (cap 6/window); digest every 30-min boundary = 1 Groq call → alerts spool → payloads cleared. DEDUPE rows kept `seen_ttl` (1h) — they must outlive the 1h f_TPR window or overlapping windows re-send the same postings ("clean db" = payloads only, never job_ids).
- Loop: `python scraper.py --collect` per tick (exit 75 on throttle → loop sleeps 240s) + `--digest` (no-op until boundary; first loop start sets it). Pidfile guard; boot script name `start-jobs` unchanged.
- ALARMS: name the ACTUAL cause (HTTP 429 / anti-bot challenge / DNS Errno7 / parser-zero-on-200), max 1 per 2h. Silence with streak ≥2 = normal suppressed resend; diagnose via `scraper.log` + `crawls` rows (`sqlite3 seen.db; SELECT ts,kind,parses,err FROM crawls ORDER BY ts DESC;`).
- Legacy burst mode (`python scraper.py`) kept for `/jobs run-now` + `--test`.
- VERIFIED 2026-10-17: sweep ≤2/min (8 fetches/5.7min), throttled pair skipped politely, legacy rows migrated (10), heartbeat + streak logic observed live.
- INCIDENT 2026-10-17 (the 25-run ALARM): NOT markup — overnight tablet DNS flap (Errno 7) + transient LinkedIn 429+challenge on the guest API; API later returned 200 with real IDs. Both self-recovered.
- NETWORK: tablet on Jio hotspot (wlan0 10.196.67.185; egress rotates 152.58.x CGNAT) — `ssh mind2` dead meanwhile, use `ssh mind2remote`; pool can throw 429 even when we behave (pacing minimizes OUR share).
- Historical: guest fetch 200, ~25 jobs/page; dedupe proven (28 scanned, 0 new). Backfill 135 → 7 FITs (2026-10-13).
- Groq key: user `~/.bashrc` (ssh non-interactive skips bashrc).
- Judge live (qwen, fresher-only + SCAM filter with counts).
- GOTCHA: Groq edge 403s Python's default `User-Agent` — send a browser UA on all API calls (TABLET.md §7).
- GOTCHA: SQLite `desc` is a reserved word — always quote `"desc"` in SQL (v2 store schema).

## 13. Remote SSH from anywhere (LIVE 2026-10-13)
- Tunnel route: `ssh.mind2.xyz` → SSH://localhost:8022 (dashboard Public Hostnames).
- PC: cloudflared installed (`C:\Program Files (x86)\cloudflared\`), alias `mind2remote` (ProxyCommand).
- Use: `ssh mind2remote` — identical session, any network. Verified working via Cloudflare edge.
- Security: key-only auth + no open ports; add Cloudflare Access later for a second gate.

## 8. Limits of this box (read before installing things)
900MB RAM, 32-bit ARMv7. No: local LLMs, Bun/OpenCode (no armv7 builds), Docker, heavy npm trees. Yes: Python/Node scripts, git, cron-style loops, MQTT, static sites (`python -m http.server`), WireGuard, sqlite. When in doubt: install, run, watch `free`.
