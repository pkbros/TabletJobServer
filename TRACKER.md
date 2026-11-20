# ProjectLenovoUnlock — TRACKER.md

## Device (verified via ADB `d7abcc5a`)
- Model: Lenovo YT3-X50L (Yoga Tab 3 10 LTE) — `ro.product.model=Lenovo YT3-X50L`
- SoC: Qualcomm MSM8909 (4x Cortex-A7 1.1GHz, ARMv7 32-bit)
- RAM: MemTotal 922472 kB (~900MB usable) — MemFree ~95MB, always ~0.88GB used
- Storage: /data 11.2G (4.0G used, 7.2G free), /system 2.4G, no SD card (`/storage/sdcard1` missing)
- OS: Android 6.0.1, build YT3-X50L_S000143_220825_ROW
- Battery: 63%, health good (2), 3681mV, 26.2C, 8400mAh design = built-in UPS
- Network: wlan0, 2.4GHz only, LTE modem present (`gsm.version.baseband=.JO.1.2.c3...`)
- Top RAM hogs (measured `dumpsys meminfo`): gms.unstable 131MB + gms.persistent 72MB + gms 32MB = ~235MB Google services alone

## Key research finding (2026-10-12)
- postmarketOS `device-lenovo-lxf-p5100` (YT3-X50 10 LTE/WiFi, armv7, v25.06, maintainer exkc) EXISTS but status = **archived / likely broken** per Nura Wiki. Depends on `linux-postmarketos-qcom-msm8916` + `soc-qcom-msm8909`.
- Implication: native Linux may boot but WiFi/display/modem likely broken. WiFi is the only network on this tablet — losing it kills server use.
- TWRP + bootloader unlock path exists for sibling YT3-X50F (XDA guide), `fastboot oem unlock-go` style. YT3-X50L LTE shares board, likely compatible but unconfirmed.
- LineageOS 14.1 (Android 7.1) unofficial builds referenced for Yoga Tab 3 family — would unlock modern Termux (needs Android 7+).

## Decisions log
- 2026-10-17 SCRAPPER v2 (owner-approved "2 queries/min + 30-min digest" redesign): sym — bursts (~15-28 req/2min) triggered LinkedIn 429+challenge waves on a Jio-CGNAT egress. cause — rate-shaped throttle, incompatible with burst per 30 min. fix — v2: collector ≤2 req/min tick loop (round-robin ALL pairs each window, detail trickle cap 6), digest at every 30-min boundary (1 Groq call), dedupe rows persist (TTL 1h > f_TPR window; payloads cleared at digest), throttle → exit 75 + loop backoff 240s, alarms cause-classified ≤1/2h. proof — live sweep: 8 fetches / 5.7 min in minute-buckets of ≤2; old legacy rows migrated (10 stamped, no resends); heartbeat + streak observed live; 429 pair politely skipped rest-of-window.
- 2026-10-18 SCAM FILTER ADDED: user reported "stipend: up to ..." jobs being pushed (fake jobs). Added SCAM_RE regex + local_scam_check() function to scraper.py (tablet + PC synced). Pre-filters obvious scams (up-to stipends, data-entry, pay-to-join, Telegram-only, etc.) BEFORE Groq judge. Judge prompt also strengthened to be STRICT about "up to" stipends. Local filter applied as override on judge results (defense in depth). Scam counts now show "[judge + local]" breakdown. Batch size reduced 10→6 (Groq TPM 429 fix). Verified: 12 "up to" jobs in DB (all already sent before filter); regex correctly matches them. Next digest will filter new ones. PC + tablet scraper.py synced (md5 26db64fa...)."oldString">
- 2026-10-18 OWNER DECISION: FREEZE — no new mechanism (recorder/watchdog/DoH-bypass all deferred; "each new fix adds complexity"). Handoff artifact built instead: D:\projects\ProjectLenovoUnlock\ProjectBundle.txt (1,321 lines, 64KB) — system context + live state + full problem list (P1-P10) + parked ideas + verbatim evidence + 12 source files (scraper v2, loop.sh, bot.py, config, 5 boot scripts, 3 helpers) — owner will paste it into a stronger model for a redesign review. Bundle contains NO secrets (telegram/cloudflared tokens redacted; verified by regex scan).
- 2026-10-18 NEW BUG FOUND DURING BUNDLE REVIEW (not fixed — owner freeze): bot.py flush_alerts() runs os.remove(p) UNCONDITIONALLY after attempting sends — spooled digests are DESTROYED even when every recipient failed (evidence: empty spool during the 03:54-05:30 mute while undelivered digests would have been sitting there). Correct policy: delete only when ≥1 recipient confirmed (or bounded retry with poison counter). Filed into the bundle problems list as P5 for the external reviewer.
- 2026-10-18 BOT MUTE 03:54→05:32 IST (owner reported): sym — no Telegram messages after 03:54, /commands dead. cause — SAME DNS flap (Errno 7) hardened overnight: bot poller backoff 10s→300s stuck at fail 18, alert-forwarding to owner+group failing identically, scraper crawling blind; NOTHING on the tablet could message the outside world (structural: mute-with-dead-net is unfixable locally; the 03:54 delivery itself was the last thing that made it out). proof — bot.log fail-counter 2..18 all Errno 7; spool empty (all spoolable content had gone out pre-03:54); my diag probe caught DNS clean at 05:29 ("fetch ok on attempt 3" in scraper.log); test alert dropped 05:30 → bot forwarded+deleted it by 05:33 = poller recovered on its backoff without restart. LESSON: silent-bot troubleshooting order = 1) probe tablet DNS, 2) pgrep single bot instance, 3) spool state. A tablet-side watchdog cannot warn over a dead net — an OFF-tablet monitor on the Cloudflare tunnel (uptime check vs https://home.mind2.xyz) is the only channel that survives tablet-side outages (parked option).
- 2026-10-18 GROQ JUDGE TPM FIX: the digest judge batch (≤12k chars) exceeded Groq's ~8k tokens/min bucket on the qwen tier → "judge failed (HTTP 429)" with links fallback (working as designed). fix — batch: capped to 6 jobs × 500-char desc (~4.8k chars ≈ 1.2k tokens incl. system prompt). proof — live judge round-trip through deployed code: 10.1k raw payload → 4-of-6 FIT verdicts, correct scam/senior flags, 2.0s, no 429.
- 2026-10-17→18 LIKEDIN WAVE RESOLVED ITSELF: Oct 17 daytime pool-heat wave (309/330 crawls 429) decayed — last 24h report: 0 429s in latest 6h, 22 parses leaked through the wave, digests kept firing. Consistent with per-address rolling buckets + CGNAT-address rotation, not a saved ban.
- 2026-10-18 DNS FLAP RECURRED (tablet epoch, started ~19:39): 87/105 crawls Errno 7 "No address associated with hostname" — same outage class as the Oct-16 overnight one (hotspot DNS, net.dns1 = v6 Jio resolver + v4 fallback flapping). Design survives (retry ×3, intermittent sweeps, streak 0, digests on time) but coverage dips per window while it flaps. Parked options (owner to pick): (a) hotspot toggle when flapping observed, (b) pure-py resolver bypass via `https://1.1.1.1/dns-query` DoH + socket.getaddrinfo monkeypatch (~30 lines, no root), (c) adb-root net.dns pinning to stable v4 servers.
- 2026-10-17 INCIDENT (25-run ZERO-parse ALARM): sym — bot spooled "markup may have changed" ALARM every 30 min, 25 runs. cause — NOT markup: overnight DNS outage on tablet (all fetches Errno 7 `No address associated with hostname`, ~Oct 16 18:00→06:31), then LinkedIn HTTP 429 + anti-bot `_0x` JS challenge page on the guest API (transient; next probe 200 w/ 10 ids). fix — scraper.py: fetch() network-retry ×3 (5s/15s); 429/999/challenge → stop whole run (no hammering remaining searches); ALARM text now cause-classified with the real last error + max 1 spool per 2h. proof — probe: API 200/10 ids, HTML page 200/60 ids; loop run 06:36 delivered real judged digest (streak reset); manual run 06:46 hit 429 → stopped after 1 fetch, streak 1.
- 2026-10-17: NETWORK MOVED — tablet no longer on friend's LAN: wlan0 = 10.196.67.185 (Jio hotspot; DNS = net.dns1 v6 2409:40d0:... + v4 10.196.67.161). 192.168.1.50 static is per-SSID and only reasserts on the home LAN. `ssh mind2` dead meanwhile — `ssh mind2remote` (tunnel) is the path. Traffic cost on hotspot: tiny (~few MB/day) given r3600 windows + 8s gaps.
- 2026-10-12: Do NOT jump straight to postmarketOS wipe. Archived status = high risk of no WiFi. Prefer minimal-Android + Linux userland for a real server. (rationale: drivers keep working, still get SSH/nginx/mqtt)
- 2026-10-12: ADB access confirmed working via `C:\Users\123pk\AppData\Local\Temp\platform-tools\adb.exe`. Device authorized as `device` (not unauthorized).
- 2026-10-12: User chose Path 2B-updated: LineageOS 17.1 mimbrelte (Project Sweden, mrfernan, kernel 4.9.337, WiFi working, RIL broken on LTE — fine for WiFi server). Bootloader unlocked via `fastboot oem unlock-go`, wipe completed, stock setup wizard boots. OEM toggle was enabled pre-unlock.
- 2026-10-12: Goal clarified as lightweight MQTT/HTTP background jobs (strong-mini-PC model), no local LLM (900MB RAM cannot fit one).
- 2026-10-12: All 10 partition dumps saved to `partitions/` binary-clean via cmd redirection (persist 33.5MB, modemst1/2 1.5MB, boot 66MB... wait boot 33.5MB, recovery 33.5MB, aboot 1MB). boot.img verified `ANDROID!`.
- 2026-10-12: patcher-v6 flashed in TWRP ("aboot patched and verified"). Lineage recovery-mimbrelte.img flashed to recovery partition + booted, menu 17.1 up.
- 2026-10-12: Lineage 17.1 mimbrelte sideload OK ("patching system/vendor image unconditionally... script succeeded [1.00000]", no GApps). First boot to system in progress.

## Plan phases
- [x] Phase 0 — Identify + ADB access + live measurements
- [x] Phase 1 — Backup: stock props/packages + 10 partition dumps in `partitions/` (persist 33.5MB, modemst1/2, boot verified ANDROID!)
- [ ] Phase 2A (safe, reversible) — SKIPPED, went straight to 2B per user
- [x] Phase 2B — Unlocked + LineageOS 17.1 mimbrelte (no GApps) + root adbd. Disabled updater/deskclock/audiofx/printspooler, animations off.
- [x] Phase 3 — Termux 0.118.3 + git/python3.12/node25/mosquitto/sqlite/tmux + sshd:8022 key auth + background loop proven, later removed per user + Termux:Boot autostart script
- [ ] Phase 2C (experimental only) — postmarketOS: NOT pursued (archived/broken, WiFi risk)
- [x] Phase 4 (user taps) — Termux:Boot opened, battery Unrestricted, Doze whitelist, wifi_sleep_policy=2, Termux:API wake lock. VERIFIED: sleep-survival + power-off self-heal (SSH autostart).

## Backup status (2026-10-12 — COMPLETE via TWRP root)
- Saved: build-props.txt, packages-full.txt, cpu-mem.txt, WCNSS_cfg.dat, WiFi MAC stock `a0:32:99:d1:cb:83`
- `partitions/`: persist, modemst1/2, fsg, boot, recovery, aboot/abootbak, misc, config — binary-clean, boot.img `ANDROID!` verified
- Note: Lineage shows MAC `00:0a:f5:2a:c0:d0` (Android 10 per-network randomization; set static IP 192.168.1.50 instead)

## Deferred / later
- PC Playwright scraper app (Naukri/Indeed deep scraping on Windows PC → JSON to tablet). Parked per user 2026-10-13.
- Cloudflare tunnel goes live when account verified (token pending).

## Next
- Pick next server job (proposed 2026-10-13).
