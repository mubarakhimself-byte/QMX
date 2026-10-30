"""Run the study's subjects: headless `claude -p --model haiku` calls on the plan login.
Never sets or reads an API key; ANTHROPIC_API_KEY is removed from the child's env.

usage: python -I run_study.py [RUNS_PER_ARM=3] [PARALLEL=3]
Writes runs/<case>/<arm>-<n>/out.json (+ receipts.jsonl for the receipts arm).
"""
import concurrent.futures as cf, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = {  # case folder -> (symbol, date, unit word, unit singular)
    "eurusd-2025-12-08": ("EURUSD", "2025-12-08", "pips", "pip"),
    "btcusd-2025-07-10": ("BTCUSD", "2025-07-10", "USD", "USD"),
}
ARMS = {  # arm -> (files copied into the workdir, --tools value, allowed tools)
    "free": (["vendor_note.txt"], "", None),
    "chart": (["chart.png", "vendor_note.txt"], "Read", "Read"),
    "both": (["chart.png", "vendor_note.txt"], "Read", "Read"),
    "receipts": (["data.csv", "tool.py", "vendor_note.txt"], "Bash", "Bash(python -I tool.py *)"),
}
ARMS_PER_CASE = {"eurusd-2025-12-08": ["free", "chart", "both", "receipts"],
                 "btcusd-2025-07-10": ["free", "receipts"]}
MEMORY = [("EURUSD", "2025-12-08"), ("EURUSD", "2024-12-18")]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def render(arm, case):
    sym, date, unit, unit1 = CASES[case]
    cdir = os.path.join(HERE, "cases", case)
    truth = json.loads(read(os.path.join(cdir, "truth.json")))
    answers = read(os.path.join(HERE, "prompts", "answers_block.txt")).replace("{unit}", unit.lower())
    return read(os.path.join(HERE, "prompts", f"{arm}.txt")).format(
        symbol=sym, date=date, unit=unit, unit_singular=unit1, pip=truth["pip"], answers=answers,
        note=read(os.path.join(cdir, "vendor_note.txt")).strip(), csv=read(os.path.join(cdir, "data.csv")))


def call(prompt, workdir, tools, allowed):
    exe = shutil.which("claude")
    cmd = [exe, "-p", "--model", "haiku", "--output-format", "json", "--no-session-persistence",
           "--strict-mcp-config", "--restricted", "--tools", tools]
    if allowed:
        cmd += ["--allowedTools", allowed]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       cwd=workdir, env=env, timeout=900)
    return p.stdout or json.dumps({"is_error": True, "result": p.stderr[-2000:]})


def done(wd):
    p = os.path.join(wd, "out.json")
    return os.path.exists(p) and not json.loads(read(p)).get("is_error")


def job(case, arm, n):
    files, tools, allowed = ARMS[arm]
    wd = os.path.join(HERE, "runs", case, f"{arm}-{n}")
    if done(wd):
        return wd, "skipped (done)"
    shutil.rmtree(wd, ignore_errors=True)
    os.makedirs(wd)
    for f in files:
        shutil.copy(os.path.join(HERE, "cases", case, f), wd)
    out = call(render(arm, case), wd, tools, allowed)
    with open(os.path.join(wd, "out.json"), "w", encoding="utf-8") as f:
        f.write(out)
    return wd, "error" if json.loads(out).get("is_error") else "ok"


def memory_job(sym, date, n):
    wd = os.path.join(HERE, "runs", "memory", f"{sym}-{date}-{n}")
    if done(wd):
        return wd, "skipped (done)"
    os.makedirs(wd, exist_ok=True)
    out = call(read(os.path.join(HERE, "prompts", "memory.txt")).format(symbol=sym, date=date), wd, "", None)
    with open(os.path.join(wd, "out.json"), "w", encoding="utf-8") as f:
        f.write(out)
    return wd, "error" if json.loads(out).get("is_error") else "ok"


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    par = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    jobs = [(job, (c, a, n)) for c, arms in ARMS_PER_CASE.items() for a in arms for n in range(1, runs + 1)]
    jobs += [(memory_job, (s, d, n)) for s, d in MEMORY for n in range(1, 3)]
    with cf.ThreadPoolExecutor(par) as ex:
        for wd, status in ex.map(lambda j: j[0](*j[1]), jobs):
            print(status, os.path.relpath(wd, HERE), flush=True)
