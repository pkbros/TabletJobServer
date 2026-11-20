#!/data/data/com.termux/files/usr/bin/python
"""tablet gateway bot: single Telegram face for all local apps."""
import json, os, subprocess, time, urllib.request, urllib.parse

TOKEN = os.environ.get("TBOT_TOKEN", "")
OWNER = os.environ.get("TBOT_OWNER", "")
API = "https://api.telegram.org/bot" + TOKEN if TOKEN else ""
HOME = os.path.expanduser("~")
ALERTS = os.path.join(HOME, "srv", "alerts")
JOBCFG = os.path.join(HOME, "code", "jobscrapper", "config.json")
UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"}


def api(method, **params):
    if "reply_markup" in params and isinstance(params["reply_markup"], dict):
        params["reply_markup"] = json.dumps(params["reply_markup"])
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API + "/" + method, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def send_long(chat, text):
    text = text or "(empty)"
    while len(text) > 3500:
        cut = text.rfind("\n\n", 0, 3500)
        if cut < 500: cut = text.rfind("\n", 0, 3500)
        if cut < 500: cut = 3500
        api("sendMessage", chat_id=chat, text=text[:cut])
        text = text[cut:].lstrip()
    api("sendMessage", chat_id=chat, text=text)


JOB_MENU = {"inline_keyboard": [
    [{"text": "Show latest digest", "callback_data": "jobs:show"}],
    [{"text": "Force digest now", "callback_data": "jobs:run"}]]}


def trigger_digest_now():
    subprocess.Popen(["/data/data/com.termux/files/usr/bin/bash", "-c",
                      "source ~/.bashrc; cd ~/code/jobscrapper && python scraper.py --collect >> scraper.log 2>&1; python scraper.py --digest --force >> scraper.log 2>&1"])


def read_latest():
    try:
        with open(os.path.join(HOME, "code", "jobscrapper", "latest.txt")) as f:
            return f.read()[:3500] or "(empty)"
    except Exception as e:
        return "no digest yet: " + str(e)[:120]


def sh(cmd):
    try:
        p = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=15)
        return (p.stdout or p.stderr or "(no output)")[:1500]
    except Exception as e:
        return "error: " + str(e)[:200]


def jobs_cmd(arg):
    try:
        with open(JOBCFG) as f: c = json.load(f)
    except Exception as e:
        return "jobs config missing: " + str(e)[:120]
    sub = (arg or "").strip()
    if not sub:
        return ("MENU", "job searches — pick one:",
                "typed: /jobs config | /jobs terms a, b | /jobs locs x, y | /jobs add term")
    if sub == "help":
        return ("/jobs show — latest digest\n/jobs config — view terms & locations\n"
                "/jobs add <term> — add keyword\n/jobs run-now — collect & build digest immediately")
    if sub == "show":
        return read_latest()
    if sub == "config":
        t, l = c.get("terms", []), c.get("locations", [])
        return "terms (%d): %s\nlocations: %s" % (len(t), ", ".join(t), ", ".join(l))
    if sub.startswith("terms "):
        items = [t.strip() for t in sub[6:].split(",") if t.strip()][:20]
        if not items: return "usage: /jobs terms ml intern, sde intern"
        c["terms"] = items
        c.pop("searches", None)
        with open(JOBCFG, "w") as f: json.dump(c, f, indent=2)
        return "terms saved (%d)." % len(items)
    if sub.startswith("locs "):
        items = [t.strip() for t in sub[5:].split(",") if t.strip()][:8]
        if not items: return "usage: /jobs locs India, Noida"
        c["locations"] = items
        c.pop("searches", None)
        with open(JOBCFG, "w") as f: json.dump(c, f, indent=2)
        return "locations saved (%d)." % len(items)
    if sub.startswith("add "):
        term = sub[4:].strip()
        if not term: return "usage: /jobs add prompt engineer"
        terms = c.setdefault("terms", [])
        if term not in terms: terms.append(term)
        c.pop("searches", None)
        with open(JOBCFG, "w") as f: json.dump(c, f, indent=2)
        return "term added (%d total)." % len(terms)
    if sub == "run-now":
        trigger_digest_now()
        return "triggered immediate collect + digest; arriving shortly."
    return "unknown /jobs command. /jobs help"


def handle(chat, text):
    parts = (text or "").strip().split(None, 1)
    cmd, arg = parts[0].lower() if parts else "", (parts[1] if len(parts) > 1 else "")
    if cmd == "/id": return "chat id: %s" % chat
    if OWNER and str(chat) != str(OWNER): return "not authorized."
    if cmd in ("/start", "/help"):
        return ("/status — box health\n/jobs — job searches\n/files — download shelf\n/id — show chat id")
    if cmd == "/jobs": return jobs_cmd(arg)
    if cmd == "/status":
        return ("uptime: " + sh("uptime") + "\nmem: " + sh("free").split("\n")[1] + "\ndisk: " + sh("df -h /data").split("\n")[1])
    if cmd == "/files":
        try:
            fs = sorted(os.listdir(os.path.join(HOME, "srv", "files")))
            return "files:\n" + ("\n".join(fs) if fs else "(empty)")
        except Exception as e: return "files error: " + str(e)[:150]
    return "unknown. /help"


def recipients():
    ids = [str(OWNER)] if OWNER else []
    try:
        with open(os.path.join(HOME, "code", "telebot", "recipients.txt")) as f:
            ids += [l.strip() for l in f if l.strip()]
    except Exception: pass
    return list(dict.fromkeys(ids))


def flush_alerts():
    dests = recipients()
    if not dests: return
    os.makedirs(ALERTS, exist_ok=True)
    for name in sorted(os.listdir(ALERTS)):
        if name.endswith(".fail"): continue
        p = os.path.join(ALERTS, name)
        fail_p = p + ".fail"
        try:
            with open(p) as f: text = f.read()[:4000]
            sent_any = False
            for d in dests:
                try:
                    send_long(d, text)
                    sent_any = True
                except Exception as e:
                    print("alert fail %s: %s" % (d, str(e)[:120]), flush=True)
            if sent_any:
                os.remove(p)
                if os.path.exists(fail_p): os.remove(fail_p)
            else:
                fails = int(open(fail_p).read().strip()) + 1 if os.path.exists(fail_p) else 1
                if fails >= 50:
                    print("dropping poison alert %s after %d fails" % (name, fails), flush=True)
                    os.remove(p); os.remove(fail_p)
                else:
                    with open(fail_p, "w") as ff: ff.write(str(fails))
        except Exception as e:
            print("alert fail:", str(e)[:150], flush=True)


def on_callback(chat, data, cq_id):
    try: api("answerCallbackQuery", callback_query_id=cq_id)
    except Exception: pass
    if OWNER and str(chat) != str(OWNER): return
    if data == "jobs:show": send_long(chat, jobs_cmd("show"))
    elif data == "jobs:run":
        trigger_digest_now()
        api("sendMessage", chat_id=chat, text="triggered immediate collect + digest.")


def main():
    if not TOKEN:
        print("TBOT_TOKEN not set")
        return
    os.makedirs(ALERTS, exist_ok=True)
    offset, tick, fails = 0, 0, 0
    print("gateway polling...", flush=True)
    while True:
        try:
            u = api("getUpdates", offset=offset, timeout=25)
            fails = 0
            for upd in u.get("result", []):
                offset = upd["update_id"] + 1
                if "callback_query" in upd:
                    cq = upd["callback_query"]
                    on_callback(cq.get("message", {}).get("chat", {}).get("id"),
                                cq.get("data", ""), cq.get("id", ""))
                    continue
                msg = upd.get("message", {})
                chat = msg.get("chat", {}).get("id")
                if chat and "text" in msg:
                    try:
                        res = handle(chat, msg["text"])
                        if isinstance(res, tuple):
                            api("sendMessage", chat_id=chat, text=(res[1] + "\n" + res[2])[:3500], reply_markup=JOB_MENU)
                        else: send_long(chat, res)
                    except Exception as e: print("send failed:", str(e)[:150], flush=True)
        except Exception as e:
            fails += 1
            wait = min(300, 5 * (2 ** min(fails, 6)))
            print("poll error (fail %d, retry in %ds): %s" % (fails, wait, str(e)[:150]), flush=True)
            time.sleep(wait)
        tick += 1
        if tick % 4 == 0:
            try: flush_alerts()
            except Exception as e: print("alerts error:", str(e)[:150], flush=True)


if __name__ == "__main__":
    main()
