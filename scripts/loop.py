"""loop-loop: minimal local loop loop for 1GB ARM boxes.
Reads tasks from inbox/*.json, optionally calls an OpenAI-compatible
chat API, optionally runs an allowlisted shell command, writes result
to outbox/<name>.result.json. No daemons, no deps beyond requests.
Usage: python loop.py --once | --loop [seconds]
Task file example:
  {"model": "gpt-4o-mini", "messages": [{"role":"user","content":"hi"}],
   "shell": "uptime", "shell_timeout": 20}
Env: LOOP_API_KEY, LOOP_BASE_URL (default https://api.openai.com/v1)
"""
import json, os, subprocess, sys, time, urllib.request

HOME = os.path.expanduser("~")
INBOX = os.path.join(HOME, "loop", "inbox")
OUTBOX = os.path.join(HOME, "loop", "outbox")
BASE_URL = os.environ.get("LOOP_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("LOOP_API_KEY", "")

ALLOWLIST = ("uptime", "free", "df", "date", "uname", "ip", "ping",
             "mosquitto_pub", "mosquitto_sub", "curl", "git", "ls")


def call_api(model, messages):
    if not API_KEY:
        return {"error": "LOOP_API_KEY not set"}
    body = json.dumps({"model": model, "messages": messages}).encode()
    req = urllib.request.Request(BASE_URL + "/chat/completions", data=body,
                                 headers={"Authorization": "Bearer " + API_KEY,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def run_shell(cmd, timeout=20):
    parts = cmd.strip().split()
    if not parts or parts[0] not in ALLOWLIST:
        return {"error": "command not allowlisted: " + (parts[0] if parts else "")}
    try:
        p = subprocess.run(parts, capture_output=True, text=True, timeout=timeout)
        return {"rc": p.returncode, "out": p.stdout[-2000:], "err": p.stderr[-500:]}
    except Exception as e:
        return {"error": str(e)}


def do_task(path):
    with open(path) as f:
        task = json.load(f)
    name = os.path.basename(path)
    result = {"task": name}
    if task.get("shell"):
        result["shell"] = run_shell(task["shell"], task.get("shell_timeout", 20))
    if task.get("messages"):
        result["api"] = call_api(task.get("model", "gpt-4o-mini"), task["messages"])
    os.makedirs(OUTBOX, exist_ok=True)
    with open(os.path.join(OUTBOX, name + ".result.json"), "w") as f:
        json.dump(result, f, indent=1)
    os.remove(path)
    return result


def main():
    os.makedirs(INBOX, exist_ok=True)
    once = "--once" in sys.argv
    interval = int(sys.argv[sys.argv.index("--loop") + 1]) if "--loop" in sys.argv else 30
    while True:
        for name in sorted(os.listdir(INBOX)):
            if name.endswith(".json"):
                try:
                    print(json.dumps(do_task(os.path.join(INBOX, name)))[:300], flush=True)
                except Exception as e:
                    try:
                        os.makedirs(OUTBOX, exist_ok=True)
                        with open(os.path.join(OUTBOX, name + ".result.json"), "w") as f:
                            json.dump({"task": name, "error": "task failed: " + str(e)}, f)
                        os.remove(os.path.join(INBOX, name))
                    except Exception:
                        pass
                    print("task error: " + str(e)[:200], flush=True)
        if once:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()
