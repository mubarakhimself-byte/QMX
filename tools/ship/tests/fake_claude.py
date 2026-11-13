"""A stand-in for the `claude` CLI, run as a real subprocess by launch.py in tests.

`FAKE_CLAUDE_SCRIPT` names a JSON list of rules:

    {"match": "builder: a2", "times": 1, "steps": [...], "reply": "READY {head}",
     "kind": "ok|limit|hang|garbage|crash", "sleep_s": 0, "model": "<modelUsage key>", "reset": "<ISO>"}

The first rule whose `match` words all appear among the words of the `--name` value, and whose `times`
is not used up (a missing `times` never runs out), applies; the counts live in `<script>.count.json`.
Steps run in the working folder, in order:

    {"write": {"<relative path>": "<text>"}}   {"git": ["add", "-A"]}   {"commit": "<message>"}
    {"push": true}   {"file": {"<path with {program}, {evidence}>": "<text>"}}   {"sleep": 0.5}

`{head}` is `git rev-parse HEAD` when the text is filled; `{program}`, `{evidence}`, `{slice}`,
`{dispatch}` and `{worktree}` come from the run's environment (SHIP_PROGRAM, SHIP_EVIDENCE,
SHIP_SLICE, SHIP_DISPATCH_ID) and its working folder. It prints one JSON object in the recorded
result shape (roles/RESULT-SHAPE.md): `limit` prints the limit ending, `garbage` a reply with no
contract line, `crash` exits 2, `hang` sleeps until it is killed. With no matching rule it replies
`DONE fake`. Each call appends {"argv", "cwd", "env", "rule", "at"} as one JSON line to
`<program>/fake-claude.log`.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def opt(argv: list[str], name: str) -> str | None:
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True,
                          stdin=subprocess.DEVNULL).stdout.strip()


def fill(text: str) -> str:
    values = {"program": os.environ.get("SHIP_PROGRAM", ""), "evidence": os.environ.get("SHIP_EVIDENCE", ""),
              "slice": os.environ.get("SHIP_SLICE", ""), "dispatch": os.environ.get("SHIP_DISPATCH_ID", ""),
              "worktree": os.getcwd()}
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    if "{head}" in text:
        text = text.replace("{head}", git("rev-parse", "HEAD"))
    return text


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8", newline="\n")


def pick(name: str) -> tuple[int | None, dict]:
    script = os.environ.get("FAKE_CLAUDE_SCRIPT")
    if not script or not Path(script).exists():
        return None, {}
    rules = json.loads(Path(script).read_text("utf-8"))
    counts_path = Path(script + ".count.json")
    counts = json.loads(counts_path.read_text("utf-8")) if counts_path.exists() else {}
    words = set(name.split())
    for n, rule in enumerate(rules):
        if not set(rule.get("match", "").split()) <= words:
            continue
        used = counts.get(str(n), 0)
        if "times" in rule and used >= rule["times"]:
            continue
        counts[str(n)] = used + 1
        counts_path.write_text(json.dumps(counts), "utf-8")
        return n, rule
    return None, {}


def run_steps(steps: list[dict]) -> None:
    for step in steps:
        if "write" in step:
            for rel, text in step["write"].items():
                write(Path(rel), fill(text))
        if "git" in step:
            git(*step["git"])
        if "commit" in step:
            git("add", "-A")
            git("-c", "user.name=fake builder", "-c", "user.email=fake@test.invalid", "commit", "-q",
                "-m", fill(step["commit"]))
        if step.get("push"):
            git("push", "-q", "-u", "origin", "HEAD")
        if "file" in step:
            for target, text in step["file"].items():
                write(Path(fill(target)), fill(text))
        if "sleep" in step:
            time.sleep(float(step["sleep"]))


def main(argv: list[str]) -> int:
    name = opt(argv, "--name") or ""
    n, rule = pick(name)
    program = os.environ.get("SHIP_PROGRAM")
    if program:
        env = {k: v for k, v in os.environ.items() if k.upper().startswith(("CLAUDE", "ANTHROPIC", "SHIP_"))}
        with open(Path(program) / "fake-claude.log", "a", encoding="utf-8") as log:
            log.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "env": env, "rule": n,
                                  "at": time.time()}) + "\n")
    time.sleep(float(rule.get("sleep_s", 0)))
    kind = rule.get("kind", "ok")
    if kind == "hang":
        while True:
            time.sleep(60)
    if kind == "crash":
        print("fake claude: crashed", file=sys.stderr)
        return 2
    run_steps(rule.get("steps", []))
    session = opt(argv, "--session-id")
    model = rule.get("model") or opt(argv, "--model") or "claude-opus-5-5"
    usage = {model: {"inputTokens": 1, "outputTokens": 1, "canonicalModel": model}}
    if kind == "limit":
        reset = rule.get("reset")
        epoch = int(time.time()) + 3600
        if reset:
            import datetime as dt

            epoch = int(dt.datetime.fromisoformat(reset).timestamp())
        print(json.dumps({"type": "result", "subtype": "success", "is_error": True,
                          "result": f"Claude AI usage limit reached|{epoch}", "session_id": session,
                          "modelUsage": {}, "permission_denials": [], "num_turns": 1}))
        return 1
    reply = "I looked at it and I think it is fine." if kind == "garbage" else fill(rule.get("reply", "DONE fake"))
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": reply,
                      "session_id": session, "modelUsage": usage, "permission_denials": [], "num_turns": 1,
                      "stop_reason": "end_turn", "terminal_reason": "completed"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
