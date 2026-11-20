# Job Scrapper — PRD
Status: approved direction, v1 build next. Owner learns gradually; keep code small and readable.

## 1. Goal
Every 30 min, poll LinkedIn **guest** job search (no login, no browser), find new postings matching
saved keywords × locations, have an LLM judge fit, and deliver one Telegram digest per run
(including an explicit "nothing new" heartbeat so silence means healthy).

## 2. Non-goals (v1)
- No login-walled content (posts feed, DMs, full applicant-only fields).
- No aggressive rates (polite cadence only; 429 = back off, never retry hard).
- No self-healing parser yet (extra scope, parked). Health alarm instead.

## 3. Architecture (all pure-Python, ~50MB total)
```
per 60s tick: collector (<=2 req/min) -> store(SQLite seen.db w/ payloads) via round-robin over ALL search pairs
every 30 min: digest builder -> llm (Groq, 1 batch call) -> reporter(Telegram via gateway alerts spool)
             → window: parses collected since last digest; zero-parse x2 windows -> ALARM (max 1 per 2h)
health check: digest counts window parses; collection failure/429/challenge = skip pair + loop backs off 4 min
```
- v2 (2026-10-17, per owner approval): **paced collector** replaces the 30-min burst — peak rate ~7x lower
  (was ~15-28 req in 2-min bursts; now <=2/min incl. detail trickle), same 30-min digest freshness.
  Round-robin sweep = every composed pair visited once per window (coverage > old alternating halves).
- **config.json**: `searches: [{keywords, location}]`, `cadence_min: 30`, `pages_per_search: 1`,
  `detail_cap: 6` (new v2), `seen_ttl_hours: 1`, `llm: {provider: groq, model, key_env}`. Editable via Telegram /set commands.
- **fetcher**: GET `jobs-guest/jobs/api/seeMoreJobPostings/search` with desktop Chrome UA,
  keywords/location/f_TPR=r1800, 8s+ gaps, cookie jar persisted. 429/999/challenge → pair skipped rest of window, loop sleeps 240s.
- **store**: SQLite `seen(job_id, first_seen, sent_ts, title, company, location, link, desc, preskip)` +
  `crawls(ts, kind, q, parses, err)`. **Dedupe rows MUST outlive the 1h f_TPR window (TTL 1h) — "clean the db"
  only clears payloads at each digest, NOT job_ids** (else overlapping windows re-send the same postings).
  Legacy pre-v2 rows migrated: sent_ts=first_seen stamped.
- **collector** (`scraper.py --collect`, exits 75 on throttle for loop backoff): per tick, 1 search (first pair not
  crawled in-window) + 1 detail (newest desc-empty row, capped by detail_cap per window); details fill desc/title/company;
  detail revealing senior title flips row to preskip. Never restarts a pair's window.
- **llm**: ONE Groq call per digest window (jobs with whatever desc trickled; missing = empty string).
- **reporter**: digest message → gateway bot. FITS ONLY + skipped count (skips never sent);
  unjudged leftovers appended as links; empty window → "nothing new" heartbeat.
  Also saved to `latest.txt` for Show recall. Legacy single-burst mode (`python scraper.py`) kept for
  Telegram /jobs run-now and --test.
- **health**: zero parsed pages across a window ×2 → ALARM digest naming the real cause
  (collection error text: HTTP 429 / challenge / DNS Errno7 / parser-zero-on-200), rate-limited to 1 per 2h.
- **Telegram settings**: `/jobs keywords a, b` / `/jobs locations x, y` / `/jobs show` / `/jobs run-now`.

## 4. Config model (terms+locations composed to boolean — verified 2026-10-13/14)
- terms (14 across AI/ML, GenAI, Python/backend, SDE, full-stack); locations (7: bare + ", India" variants).
- composer: terms chunked in 7s, OR'd + fresher/intern/junior NOT senior/lead, × locations, alternating halves per run (~7/run).
- Telegram owns it: `/jobs config|terms|locs|add` rewrite terms/locations; runs compose automatically.
- cadence 30 min, f_TPR=r1800, 1 page/search, 8s gaps, shared cookie session.
- Detail pages often JS-challenge-wall → detected + skipped (never fed to LLM). Obvious-senior titles pre-skipped locally (no fetch/judge = fewer requests).
- Company fix 2026-10-14: subtitle hides behind nested tag — patterns now tolerate one inner tag.
- v2 cadence notes 2026-10-17: owner wants 30-min digests kept (freshness) but got throttled by burst crawling → redesign approved:
  collector <=2 req/min (incl. details), digest every 30-min boundary (1 Groq call), detail_cap 6/window;
  store keeps dedupe rows for seen_ttl (1h) because f_TPR window (1h) overlaps the 30-min digests — payload only cleared at digest.
  Tablet rides a Jio-hotspot CGNAT (152.58.x, rotating; pool can 429 even when we behave) — pacing keeps OUR footprint minimal; 429s are tolerated, cause-reported, and alarmed (<=1/2h) only if a whole window starves.

## 5. Risks & mitigations
- LinkedIn renames markup → defensive parsing + zero-result alarm (2 consecutive) → manual fix (5-min, one function).
- HTTP 429 → exponential backoff, shrink pages, alert owner if persistent.
- Token/secret hygiene: Groq key in env file chmod 600 on tablet only, never in repo/chat.
- Friend's LAN: total traffic tiny (~50 small pages/hr); non-issue.

## 6. Phases & acceptance
- v1 (now): poller+parser+store+raw digest to Telegram, /jobs settings, health alarm. ACCEPT: /jobs run-now returns real postings.
- v2: Groq fit-judge + bullets digest. ACCEPT: digest lists fit/no-fit with links.
- v3 (parked): self-healing parser (LLM-as-fixer). NOT now.
