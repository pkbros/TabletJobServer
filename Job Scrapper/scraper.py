#!/data/data/com.termux/files/usr/bin/python
"""job scrapper v2.1: simplified paced collector + digest builder."""
import json, os, re, sqlite3, sys, time, urllib.request, urllib.error, urllib.parse, html as _html
import http.cookiejar, random

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "code", "jobscrapper")
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"}
SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/%s"
SPOOL = os.path.join(HOME, "srv", "alerts")
_JARFILE = os.path.join(BASE, "cookies.txt")
_JAR = http.cookiejar.LWPCookieJar()
try: _JAR.load(_JARFILE, ignore_discard=True)
except Exception: pass
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR))
SENIOR_RE = re.compile(r"\b(senior|sr\.?|lead|staff|principal|manager|director|\bhead\b|\bvp\b|chief|architect)\b", re.I)
SCAM_RE = re.compile(
    r"up\s+to\s+[\d\u20b9Rs]|earn\s+up\s+to|stipend.*up\s+to|"
    r"pay\s+to\s+(join|register)|registration\s+fee|training\s+fee|certification\s+fee|"
    r"data\s+entry|typing\s+job|captcha\s+solv|"
    r"telegram\s*(only|@|group|channel)|whatsapp\s*(only|@)|"
    r"work\s+from\s+home.*no\s+experience|no\s+experience.*work\s+from\s+home|"
    r"earn\s+\d+.*per\s+(day|week)|daily\s+income|weekly\s+income|"
    r"mlm|multi.?level|referral\s+scheme|"
    r"investment\s+required|deposit\s+required|security\s+deposit",
    re.I)

def local_scam_check(text):
    if not text:
        return False
    return bool(SCAM_RE.search(text))
CHALLENGE_RE = re.compile(r"_0x[a-f0-9]{6}|captcha|meta http-equiv=.refresh", re.I)


def is_challenge(html):
    return len(html) < 8000 and bool(CHALLENGE_RE.search(html))


def cfg():
    with open(os.path.join(BASE, "config.json")) as f: return json.load(f)


def db():
    os.makedirs(BASE, exist_ok=True)
    c = sqlite3.connect(os.path.join(BASE, "seen.db"))
    c.execute('CREATE TABLE IF NOT EXISTS seen(job_id TEXT PRIMARY KEY, first_seen REAL, sent_ts REAL, title TEXT, company TEXT, location TEXT, link TEXT, "desc" TEXT, preskip INTEGER DEFAULT 0)')
    c.execute("CREATE TABLE IF NOT EXISTS crawls(ts REAL, kind TEXT, q TEXT, parses INTEGER, err TEXT)")
    return c


def fetch(url, params, tries=3):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + ("?" + q if q else ""), headers=UA)
    err = None
    for attempt in range(tries):
        try:
            with _OPENER.open(req, timeout=25) as r:
                if attempt: print("fetch ok on attempt %d" % (attempt + 1), flush=True)
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError: raise
        except Exception as e:
            err = e
            if attempt == 0 and "Errno 7" in str(e):
                raw_ip_ok = (os.system("ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1") == 0)
                print("NET-DIAG on Errno 7: ping_1.1.1.1=%s" % raw_ip_ok, flush=True)
            if attempt < tries - 1:
                print("fetch retry %d/%d (%s)" % (attempt + 1, tries, str(e)[:100]), flush=True)
                time.sleep(5 if attempt == 0 else 15)
    raise err


def all_pairs(c):
    terms, locs = c.get("terms", []), c.get("locations", ["India"])
    pairs = []
    for g in [terms[i:i + 7] for i in range(0, len(terms), 7)]:
        q = "(" + " OR ".join('"%s"' % t for t in g) + ") AND (fresher OR intern OR junior) NOT senior NOT lead"
        for loc in locs: pairs.append({"keywords": q, "location": loc})
    return pairs


def parse_search(html):
    ids = re.findall(r"urn:li:jobPosting:(\d+)", html)
    seen, out = set(), []
    for jid in ids:
        if jid not in seen:
            seen.add(jid)
            out.append({"id": jid, "link": "https://www.linkedin.com/jobs/view/%s/" % jid})
    titles = re.findall(r'base-search-card__title[^>]*>\s*(?:<[^>]+>)?\s*([^<]{2,120})', html)
    companies = []
    for pat in (r'base-search-card__subtitle[^>]*>\s*(?:<[^>]+>)?\s*([^<]{2,120})',
                r'job-search-card__subtitle[^>]*>\s*(?:<[^>]+>)?\s*([^<]{2,120})'):
        companies = re.findall(pat, html)
        if companies: break
    locs = re.findall(r'job-search-card__location[^>]*>\s*([^<]{2,120})', html)
    clean = lambda s: _html.unescape(re.sub(r"\s+", " ", s)).strip()
    for i, j in enumerate(out):
        if i < len(titles): j["title"] = clean(titles[i])
        if i < len(companies): j["company"] = clean(companies[i])
        if i < len(locs): j["location"] = clean(locs[i])
    return out


def fetch_detail(jid):
    html = fetch(DETAIL_URL % jid, {})
    if is_challenge(html): return "", "", "", True
    m = re.search(r'job-details-jobs-unified-top-card__job-title[^>]*>\s*([^<]{2,150})', html)
    title = _html.unescape(m.group(1)).strip() if m else ""
    c = re.search(r'job-details-jobs-unified-top-card__company-name[^>]*>\s*([^<]{2,120})', html)
    company = _html.unescape(c.group(1)).strip() if c else ""
    txt = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", html)))
    money = re.findall(r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\s?-\s?(?:₹|Rs\.?|INR)?\s?[\d,]+)?(?:\s?/\s?(?:month|mo|year|annum))?|\d+(?:\.\d+)?\s?LPA|stipend[^.]{0,80}", txt, re.I)
    stip = "; ".join(dict.fromkeys(money))[:200]
    desc = ("[Stipend: %s] %s" % (stip, txt[:1400])) if stip else txt[:1500]
    return title, company, desc, False


def groq_judge(api_key, model, jobs):
    lean_jobs = [{"id": j["id"], "title": j.get("title", ""), "company": j.get("company", ""),
                  "loc": j.get("location", ""), "desc": (j.get("desc") or "")[:450]} for j in jobs]
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "Triage India job postings for a FRESHER student (0 exp). Set scam=true for placement fees, pay-to-join, vague stipends, data-entry. Set fit=true ONLY if scam=false AND role is fresher/0-1yr/intern. Reply ONLY with JSON array: [{\"id\":\"...\",\"scam\":bool,\"fit\":bool,\"role\":\"...\",\"company\":\"...\",\"stipend\":\"...\",\"location\":\"...\",\"reqs\":\"max 10 words\",\"why\":\"max 8 words\"}]"},
            {"role": "user", "content": json.dumps(lean_jobs)}],
        "temperature": 0.1}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json", "User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=90) as r:
        content = json.loads(r.read().decode())["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", content, re.S)
    return json.loads(m.group(0)) if m else []


def ingest(con, jobs):
    new, kept = [], 0
    for j in jobs:
        if con.execute("SELECT 1 FROM seen WHERE job_id=?", (j["id"],)).fetchone():
            kept += 1; continue
        title = j.get("title", "")
        preskip = 1 if title and SENIOR_RE.search(title) else 0
        con.execute("INSERT INTO seen VALUES (?,?,?,?,?,?,?,?,?)",
                    (j["id"], time.time(), time.time() if preskip else None,
                     title, j.get("company", ""), j.get("location", ""), j.get("link", ""), "", preskip))
        if not preskip: new.append(j)
    con.commit()
    return new, kept


def log_crawl(con, kind, parses, err):
    con.execute("INSERT INTO crawls VALUES (?,?,?,?,?)", (time.time(), kind, "", parses, err))
    con.commit()


def collect(c):
    cadence = c.get("cadence_min", 30) * 60
    con = db()
    details_used = con.execute("SELECT COUNT(*) FROM crawls WHERE kind LIKE 'detail|%' AND ts > ?", (time.time() - cadence,)).fetchone()[0]
    spairs = [p for p in all_pairs(c) if not con.execute("SELECT 1 FROM crawls WHERE kind=? AND ts > ? LIMIT 1",
              ("search|%s|%s" % (p["keywords"], p["location"]), time.time() - cadence)).fetchone()]
    djobs = [r[0] for r in con.execute('SELECT job_id FROM seen WHERE sent_ts IS NULL AND preskip=0 AND "desc"=\'\' AND first_seen > ? ORDER BY first_seen DESC LIMIT 1', (time.time() - cadence,))]
    fights, throttle = 0, False

    if spairs:
        p = spairs[0]
        label = "search|%s|%s" % (p["keywords"], p["location"])
        try:
            html = fetch(SEARCH_URL, {"keywords": p["keywords"], "location": p["location"], "f_TPR": c["time_window"], "start": 0})
            if is_challenge(html):
                log_crawl(con, label, 0, "anti-bot challenge"); throttle = True
            else:
                jobs = parse_search(html)
                new, kept = ingest(con, jobs)
                log_crawl(con, label, len(jobs), "")
                print("collect search: %d parsed, %d new, %d kept" % (len(jobs), len(new), kept), flush=True)
                fights += 1
        except urllib.error.HTTPError as e:
            log_crawl(con, label, 0, "HTTP %s" % e.code)
            if e.code in (429, 999): throttle = True
        except Exception as e: log_crawl(con, label, 0, str(e)[:120])

    if not throttle and djobs and details_used < c.get("detail_cap", 10):
        if fights: time.sleep(random.uniform(c["request_gap_s"], c["request_gap_s"] + 6))
        jid = djobs[0]
        label = "detail|%s" % jid
        try:
            t, comp, d, chall = fetch_detail(jid)
            if chall:
                log_crawl(con, label, 0, "anti-bot challenge"); throttle = True
            else:
                log_crawl(con, label, 1 if d else 0, "")
                con.execute('UPDATE seen SET title=COALESCE(NULLIF(?,\'\'),title), company=COALESCE(NULLIF(?,\'\'),company), "desc"=? WHERE job_id=?',
                            (t, comp, d or "(no description)", jid))
                if t and SENIOR_RE.search(t):
                    con.execute("UPDATE seen SET preskip=1, sent_ts=? WHERE job_id=?", (time.time(), jid))
                con.commit()
                print("collect detail %s: ok" % jid, flush=True)
        except urllib.error.HTTPError as e:
            log_crawl(con, label, 0, "HTTP %s" % e.code)
            if e.code in (429, 999): throttle = True
        except Exception as e: log_crawl(con, label, 0, str(e)[:120])

    con.execute("DELETE FROM crawls WHERE ts < ?", (time.time() - 2 * 86400,))
    con.commit(); con.close()
    try: _JAR.save(_JARFILE, ignore_discard=True)
    except Exception: pass
    return 75 if throttle else 0


def digest(c, force=False):
    cadence = c.get("cadence_min", 30) * 60
    last_f = os.path.join(BASE, "last_digest")
    try: last_digest = float(open(last_f).read().strip() or 0)
    except Exception: last_digest = 0.0
    now = time.time()
    if not force and last_digest and (now - last_digest < cadence - 90): return

    con = db()
    window = last_digest or (now - cadence)
    rows = [dict(zip(("id", "first_seen", "link", "title", "company", "location", "desc"),
                     (r[0], r[1], r[6], r[3], r[4], r[5], r[7]))) for r in con.execute(
        'SELECT job_id, first_seen, sent_ts, title, company, location, link, "desc", preskip FROM seen '
        'WHERE sent_ts IS NULL AND preskip=0 ORDER BY first_seen DESC')]
    preskipped_n = con.execute("SELECT COUNT(*) FROM seen WHERE preskip=1 AND first_seen > ?", (window,)).fetchone()[0]
    wc = con.execute("SELECT COALESCE(SUM(parses),0), MAX(COALESCE(err,'')) FROM crawls WHERE kind LIKE 'search|%' AND ts > ?", (window,)).fetchone()
    parsed_total, last_crawl_err = wc[0], (wc[1] or "")

    streak_f = os.path.join(BASE, "zero_streak")
    try: streak = int(open(streak_f).read().strip() or 0)
    except Exception: streak = 0
    if parsed_total == 0 and not rows:
        cause = ("collection paused: %s" % last_crawl_err) if last_crawl_err else "pages fetched OK but parser found NOTHING"
        streak += 1
    else: streak = 0
    with open(streak_f, "w") as f: f.write(str(streak))

    if not rows:
        digest_msg = None
        if streak >= 2:
            alarm_f = os.path.join(BASE, "last_alarm_ts")
            try: last_alarm = float(open(alarm_f).read().strip() or 0)
            except Exception: last_alarm = 0.0
            if now - last_alarm >= 7200:
                digest_msg = "ALARM: ZERO jobs parsed %d windows in a row. Cause: %s." % (streak, cause)
                with open(alarm_f, "w") as f: f.write(str(now))
        elif force:
            digest_msg = "jobs: nothing new pending (%d scanned this window)." % parsed_total
    else:
        local_scams = []
        judge_candidates = []
        for j in rows:
            text = (j.get("desc") or "") + " " + (j.get("title") or "")
            if local_scam_check(text):
                local_scams.append(j)
            else:
                judge_candidates.append(j)
        batch = judge_candidates[:6]
        local_scam_ids = [j["id"] for j in local_scams]
        try:
            items = groq_judge(os.environ["GROQ_API_KEY"], c["llm"]["model"], batch) if batch else []
            for v in (items if isinstance(items, list) else []):
                jid = str(v.get("id", ""))
                orig = next((j for j in batch if j["id"] == jid), None)
                if orig and local_scam_check((orig.get("desc") or "") + " " + (orig.get("title") or "")):
                    v["scam"] = True
                    v["fit"] = False
            fits = [v for v in items if v.get("fit") and not v.get("scam")] if isinstance(items, list) else []
            genuine_other = [v for v in items if not v.get("fit") and not v.get("scam")] if isinstance(items, list) else []
            judge_scams = [v for v in items if v.get("scam")] if isinstance(items, list) else []
            all_scams = judge_scams + [{"id": sid} for sid in local_scam_ids]
            judged = set(str(v.get("id")) for v in (items if isinstance(items, list) else []))
            orphans = [x for x in rows if x["id"] not in judged and x["id"] not in local_scam_ids]

            def card(idx, v):
                link = next((x["link"] for x in batch if x["id"] == str(v.get("id"))), "")
                if not link:
                    link = next((x["link"] for x in rows if x["id"] == str(v.get("id"))), "")
                return ("\n%d. %s\n   Company: %s | Location: %s\n   Stipend: %s\n   Needs: %s\n   Why: %s\n   %s" % (
                    idx, v.get("role", "?"), v.get("company", "not listed"), v.get("location", "?"),
                    v.get("stipend", "not listed"), v.get("reqs", "-"), v.get("why", ""), link))

            flines = ["freshers FIT (%d of %d judged, %d local-scam filtered):" % (len(fits), len(batch) + len(local_scams), len(local_scams))] if fits else ["jobs: %d judged, none fresher-fit (%d local scams filtered)." % (len(batch), len(local_scams))]
            for i, v in enumerate(fits, 1): flines.append(card(i, v))
            if genuine_other:
                flines.append("\nalso genuine (%d):" % len(genuine_other))
                for i, v in enumerate(genuine_other[:5], 1): flines.append(card(i, v))
            flines.append("(%d scams total [%d judge + %d local], %d non-fit, %d pre-skipped senior, %d overflow queued)"
                          % (len(all_scams), len(judge_scams), len(local_scams), len(genuine_other), preskipped_n, max(0, len(rows) - len(batch) - len(local_scams))))
            if orphans:
                flines.append("(unjudged %d: %s)" % (len(orphans), ", ".join(x["link"] for x in orphans[:5])))
            digest_msg = "\n".join(flines)[:3500]
            all_ids = [x["id"] for x in batch] + local_scam_ids
            con.executemany("UPDATE seen SET sent_ts=? WHERE job_id=?", [(now, jid) for jid in all_ids])
            con.commit()
        except Exception as e:
            digest_msg = "jobs: %d new, judge failed (%s). Links: %s" % (len(batch) + len(local_scams), str(e)[:100], ", ".join(x["link"] for x in rows[:10]))
            all_ids = [x["id"] for x in rows]
            con.executemany("UPDATE seen SET sent_ts=? WHERE job_id=?", [(now, jid) for jid in all_ids])
            con.commit()

    if digest_msg:
        os.makedirs(SPOOL, exist_ok=True)
        with open(os.path.join(SPOOL, "jobs-%d.txt" % int(now)), "w") as f: f.write(digest_msg)
        with open(os.path.join(BASE, "latest.txt"), "w") as f: f.write(digest_msg)
        print(digest_msg[:500], flush=True)
    with open(last_f, "w") as f: f.write(str(now))
    con.execute("DELETE FROM seen WHERE first_seen < ?", (now - c.get("seen_ttl_hours", 4) * 3600,))
    con.commit(); con.close()


def test_mode(c):
    p = all_pairs(c)[0]
    html = fetch(SEARCH_URL, {"keywords": p["keywords"], "location": p["location"], "f_TPR": c["time_window"], "start": 0})
    jobs = parse_search(html)
    print("test parsed %d jobs." % len(jobs))
    print(json.dumps(jobs[:3], indent=2))


if __name__ == "__main__":
    c = cfg()
    if "--collect" in sys.argv: sys.exit(collect(c))
    elif "--digest" in sys.argv: digest(c, force=("--force" in sys.argv))
    elif "--test" in sys.argv: test_mode(c)
    else: collect(c); digest(c, force=True)
