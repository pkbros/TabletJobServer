# TABLET.md — build handbook for coding agents targeting this machine
Audience: any coding agent asked to build/run a project ON the tablet below.
Source of truth for procedures; MANUAL.md is the human operator's guide.

## 1. Machine identity
- Lenovo YT3-X50L (Yoga Tab 3 10 LTE), Qualcomm MSM8909 (Snapdragon 210), 4x Cortex-A7 1.1GHz, **ARMv7-A 32-bit**
- CPU features (live `/proc/cpuinfo`): half thumb fastmult vfp edsp neon vfpv3 tls vfpv4 idiva idivt vfpd32 evtstrm
  (has NEON + VFPv4; NO crypto extensions, NO 64-bit — do not build for arm64/aarch64, do not assume AES-NI/NEON-crypto)
- ABI (live): `armeabi-v7a` (+ legacy `armeabi`); `platform.machine()=armv7l`, `architecture=32bit`
- GPU: Adreno 304, OpenGL ES 3.0 (`ro.opengles.version=196608`) — no CUDA/OpenCL compute target; treat as display-only
- RAM 906MB total (~280MB real headroom + 531MB zram), storage /data 11GB eMMC (10GB free at build time)
- Display 10.1" 1280x800 IPS (spec sheet); battery 8400mAh design (spec sheet, health good per dumpsys)
- OS: LineageOS 17.1 UNOFFICIAL-mimbrelte (Android 10, **API 29**, kernel 4.9.337 Project Sweden), **no GApps**
- Bootloader UNLOCKED, root adbd available, TWRP x50 + Lineage recovery tested
- Network: 2.4GHz WiFi only (prima WCNSS), static IP `192.168.1.50`, LTE radio broken (known RIL issue, WiFi fine)
- Identity: hostname `localhost`, Termux single user (uid 10120, `u0_a120`)

## 2. How THIS agent reaches the tablet (two channels)
- SSH (primary): `ssh mind2` == `ssh -i ~/.ssh/mind2 -p 8022 192.168.1.50` (key in PC `~/.ssh/`).
  Non-interactive shells get a BARE PATH — always `export PATH=/data/data/com.termux/files/usr/bin:$PATH` first,
  or prefix absolute binary paths. (`which` does not exist; use `command -v`.)
- ADB over USB (fallback/root): `C:\Users\123pk\AppData\Local\Temp\platform-tools\adb.exe`.
  `adb root` gives uid=0. App uid 10120 — chown pushed files to it. `adb push SRC /data/local/tmp/` then `cp`+`chown`.
- run-as (no network needed): `adb shell "run-as com.termux /data/data/com.termux/files/usr/bin/bash ..."`
  works because the Termux APK is a debug build.

## 3. Installed stack (verified versions, 2026-10-13)
git 2.52 · python 3.12.12 (+pip: requests, paho-mqtt, flask, fastapi==0.95.2, uvicorn) · node v25.3.0 ·
openssh (sshd:8022) · tmux · sqlite · mosquitto 2.0.22 · termux-api 0.59.1 (+app) · cloudflared 2026.10.0 (~/cloudflared, idle)
No micro guaranteed — check before assuming. No docker, no Java, no Rust toolchain.

## 4. Port map (all bound 0.0.0.0 for LAN; localhost-only ports are UNREACHABLE off-device)
- :8022 SSH · :8000 static homepage (`~/srv/www/`) · :8001 file shelves (`~/srv/files/`, read-only listing)
- :8003 FREE (weather demo removed 2026-10-13). New projects: use 8003+ and record here.

## 5. Boot & persistence
- `~/.termux/boot/` scripts run at boot via Termux:Boot app (must have been opened once; battery Unrestricted; Doze-whitelisted).
  Current: `start-sshd` (sshd + `termux-wake-lock`), `start-srv` (:8000+:8001).
- Sleep/power verified: SSH survives screen-off; full power-off self-heals in ~3 min.
- Long-running procs: `nohup <cmd> > log 2>&1 &` (tmux server proved UNRELIABLE here — do not depend on it).

## 6. Hard constraints (do not attempt)
- No local LLM inference (RAM). No Bun/OpenCode (no armv7 builds). No Docker. No GApps (RAM).
- No Rust-compiled pip packages: anything needing maturin/Rust WILL FAIL (observed: pydantic-core).
  Prefer pure-Python: Flask over FastAPI, stdlib over deps. If pip tries to BUILD (not download a wheel), abort and pick another lib.
- pydantic v1 crashes on Python 3.12 (`ForwardRef._evaluate`); FastAPI 0.95 works but is unpatched — LAN only.
- RAM budget per service: ~30-60MB. `free` before big installs. `/data` has room; RAM does not.

## 7. Gotchas learned the expensive way (READ BEFORE SCRIPTING)
1. **Windows PowerShell mangles nested quotes.** NEVER inline complex remote commands through
   `ssh "..."`/`adb shell "..."` layers. Instead: write a `.sh` file locally → `scp`/`adb push` → execute it.
2. **PowerShell `>` writes UTF-16.** JSON/configs created with `echo ... >` on the PC arrive with BOM and break
   parsers. Write files with the `write` tool or `[IO.File]::WriteAllText` (UTF-8).
3. **`pkill -f <pattern>` kills your own remote shell** if the pattern appears in your ssh command string.
   Use bracket form: `pkill -f 'api[.]py'`.
   COROLLARY (learned hard): boot/startup scripts must NEVER contain pkill — running them over ssh
   makes pkill murder the very session executing it. Kill stale processes in a separate,
   pattern-only ssh call first.
4. **`adb exec-out ... > file` in PowerShell corrupts binaries** (UTF-16 re-encode). Use `cmd /c "adb exec-out ... > file"`.
5. **127.0.0.1 vs 0.0.0.0**: servers bound to localhost are invisible off-device. LAN/internet services MUST bind 0.0.0.0.
6. **Mini-shell limits** (if you build task runners): `subprocess` arg-splitting supports single commands only — no pipes.
7. **WiFi suspends at driver level on screen-off** (dmesg `wlan_suspend`); fixed via `wifi_sleep_policy=2` +
   Doze whitelist + `termux-wake-lock`. If SSH starts dying on sleep again, re-check these three.
8. **Tablet clock/timezone** may drift; check `date` if TLS/API calls fail mysteriously.
9. **Friend's LAN**: static .50 can collide; if all networking dies suddenly, suspect DHCP conflict first.
   2026-10-17 variant: tablet moved to a MOBILE HOTSPOT (wlan0 10.196.67.185) — `ssh mind2` times out while tunnel
   works. Network can change silently; check `ifconfig wlan0` before assuming sshd is dead. `ssh mind2remote`
   (Cloudflare tunnel, §13 MANUAL) always works from any network — reach tunnel-side FIRST when LAN dies.
10. **APIs may 403 Python's default User-Agent** (observed: Groq edge). Always send a browser UA
    on outbound API calls from tablet Python (`urllib` default gets refused).

## 8. Deploy recipe (project → tablet)
1. Write files in PC project dir. 2. Push: `scp` (SSH up) or `adb push`→`/data/local/tmp`+`cp`+`chown 10120:10120`.
3. Start via nohup (log to file). 4. Verify from OUTSIDE: `curl http://192.168.1.50:PORT/` from PC.
5. Autostart: add `~/.termux/boot/start-<name>` (chmod 700), prove with kill-all + run script.
6. Record in MANUAL.md (§10-style entry) and this file's port map.

## 9. Gateway bot contract (MANDATORY for anything user-facing)
One Telegram bot serves the whole box (`~/code/telebot/bot.py`, stdlib+requests, polling).
New apps MUST NOT create their own bots/tokens. Instead:
- INBOUND (user → app): expose your app as HTTP on `127.0.0.1:<port>` (take next free port ≥8004,
  record it in §4). Then add ONE route in `handle()` in bot.py, e.g.:
  `if cmd == "/myapp": return http_get("http://127.0.0.1:8004/...")`.
  Restart the bot afterwards (kill single instance, run `~/.termux/boot/start-tbot`; verify ONE poller via log).
- OUTBOUND (app → user): write a plain text file into `~/srv/alerts/<name>.txt`; the bot forwards it
  to the owner within ~100s and deletes it. No Telegram code in your app. Keep messages <1500 chars.
- AUTH: bot checks `TBOT_OWNER` env (owner chat id; `/id` reveals while open). Never hardcode tokens;
  token lives only in `~/.termux/boot/start-tbot` env (chmod 700). Never commit tokens to repos/docs.
- 409 Conflict = duplicate poller or stale webhook → `getWebhookInfo`/`deleteWebhook`, keep exactly one instance.
- Test path: `curl` the local endpoint from tablet FIRST, then test via Telegram `/<cmd>` second.

## 10. Safety rails
- NEVER factory-reset from Android settings (wipes Termux). NEVER flash non-mimbrelte images.
- Restore set in PC `partitions/` (persist/modemst/boot/aboot…) + `images/downloads/` (ROM/recovery/TWRP/patcher).
- Keep services' RAM small; check `uptime` load (sustained >4 = investigate with `top`).
