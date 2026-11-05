"""The repair program's deterministic checks. Standard library only.

Run with the audit copy's interpreter, never a bare python, which is a Windows stub on this PC:
  D:/QMX-worktrees/audit-head/.venv/Scripts/python.exe -I <this file> <command>

Commands:
  check <id> <builder|fix|reviewer> [--transcript=<path>] [--store=<path>]   did the agent do the work, in order?
  gate <id> <head> [--store=<path>]    may this PR join the stack? Nothing stacks without a PASS here.
  alive                                minutes since each repair agent's transcript last changed.
  hook <builder|reviewer>              PreToolUse hook for the two agent types. Exit 2 blocks and tells the agent why.

Each line reads PASS, FAIL or INFO. The exit code is 1 on any FAIL. Any error inside the hook lets the call through.
"""

import glob
import json
import pathlib
import re
import sys
import time

PROJECT = pathlib.Path.home() / ".claude/projects/C--Users-Mubarak-Desktop-QMX"
STORE = pathlib.Path("D:/QMX-worktrees/repair-ship")
ENV = "source D:/QMX-worktrees/repair-ship/tools/env.sh"
MAX_SECONDS = 290

SKILLS = r"skills[\\/]+{0}[\\/]+SKILL\.md|^Skill:{0}\b"
BUILDER = {
    "poteto-mode": SKILLS.format("poteto-mode"),
    "Feature playbook": r"playbooks[\\/]+feature\.md",
    "how": SKILLS.format("how"),
    "architect": SKILLS.format("architect"),
    "tdd": SKILLS.format("tdd"),
    "blast-radius": SKILLS.format("blast-radius"),
    "test behavior principle": r"principle-test-behavior-not-implementation",
    "the builder brief": r"BRIEF-REPAIR-BUILDER\.md",
    "the promises list": r"ground-core\.md",
}
REVIEWER = {
    "code-review": SKILLS.format("code-review"),
    "verification-gap lens": r"lens-verification-gap\.md",
    "blast-radius": SKILLS.format("blast-radius"),
    "prove it works principle": r"principle-prove-it-works",
    "the promises list": r"ground-core\.md",
}
FIX = {key: BUILDER[key] for key in ("poteto-mode", "the builder brief", "blast-radius")}
EDGE_LENS = r"lens-edge-case-hunter\.md"
MONEY_ADJACENT = {"r03", "r04", "r05", "r07", "r08", "r10", "r11", "r15", "r17", "r20", "r21", "r22", "r23", "r24"}
NO_RED_TEST = {"r01"}

RUNS = r"^(uv run\b.*|\S*python\S*|\"?\$\w+\"?)"
# What a builder or reviewer never does. The coordinator alone owns these.
FORBIDDEN = {
    "ran a whole-repo check": r"^just\s+ci\b|(^|\s)\S*tools[\\/](ci|test_all)\.py\b",
    "booted a host or ran a lane helper": RUNS + r".*(\s-m\s+qmx_host\b|\S*owner_lane\S*\.py|\S*owner-lane\S*\.py)",
    "ran the first start for real": RUNS + r".*(\s|[\\/])first_real_start\.py(?!.*--rehears)",
    "moved the stack": r"^git(\s+-[cC]\s+\S+)*\s+((rebase|merge|stash)(\s|$)|branch\s+-[dDmM]\b|worktree\s+(add|remove)(?!.*D:[\\/]Temp[\\/])|worktree\s+prune)",
    "force-pushed or wrote to a protected branch": r"^git\b.*\bpush\b.*(--force\b|\s-f\b|\b(main|engine/base|integration)\b)",
    "merged or closed a PR": r"^gh\s+pr\s+(merge|close)\b",
    "changed an environment by hand": r"^(\S*python\S* -m )?pip install\b|^uv (add|remove|pip|lock)\b",
    "touched a credential": r"^(cmdkey|vaultcmd)\b|" + RUNS + r".*keyring\.(get|set|delete)_password",
    "changed a virtual environment": r"(>|\btee\s|\bsed\s+-i\b|^rm\s|^mv\s|^cp\s).*(\.venv|site-packages)",
    "dropped the credential guard": r"(python\S*|_ENV\"?)\s+-I\b",
}
OUT_OF_BOUNDS = r"apps[\\/]qmx-ui|[\\/]\.qmx[\\/]|Desktop[\\/]DATA_NARL|Mubarak[\\/]Documents|\.venv[\\/]|site-packages|[\\/]\.claude[\\/]"
READ_COMMANDS = ("cat ", "sed ", "head ", "tail ", "type ", "less ", "more ")
WRITES_OK = {
    "builder": ("/bld-repair-", "/repair-ship/evidence/", "/repair-ship/homes/", "d:/temp/"),
    "reviewer": ("/repair-ship/review/", "/repair-ship/evidence/r02/review-findings.md", "d:/temp/"),
}


def strip_prefix(part):
    return re.sub(r"^(timeout\s+\S+\s+|time\s+|env\s+|\w+=\S+\s+)+", "", part.strip().lstrip("(").strip())


def segments(command):
    """Each command in a shell line, without heredoc bodies. Text in quotes stays whole."""
    command = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n.*?\n\1\b", "", command, flags=re.S)
    parts, current, quote = [], [], None
    for index, ch in enumerate(command):
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            current.append(ch)
        elif ch in ";|&\n" and not (ch == "|" and index and command[index - 1] == "\\"):
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    parts.append("".join(current).strip())
    return [p for p in parts if p]


def forbidden_in(command):
    for raw in segments(command):
        part = strip_prefix(raw)
        for label, pattern in FORBIDDEN.items():
            if re.search(pattern, part):
                return label, part
    return None


def read(path):
    """Tool uses in order, as (name, input), plus the models seen and the idle minutes."""
    uses, models, stamps = [], set(), []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("timestamp"):
                stamps.append(row["timestamp"])
            message = row.get("message") or {}
            if message.get("model"):
                models.add(message["model"])
            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        uses.append((block.get("name", ""), block.get("input") or {}))
    return uses, models


def first_user_line(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        for _, line in zip(range(6), handle):
            if '"type":"user"' in line.replace(" ", ""):
                return line
    return ""


def transcripts(marker):
    found = [p for p in glob.glob(str(PROJECT / "*" / "subagents" / "**" / "*.jsonl"), recursive=True) if marker in first_user_line(p)]
    return sorted(set(found), key=lambda p: pathlib.Path(p).stat().st_mtime)


def opened_texts(uses):
    """What the agent really opened: the Read tool, the Skill tool, or a shell command that prints a file. Never text it wrote."""
    texts = []
    for name, given in uses:
        if name == "Read":
            texts.append(str(given.get("file_path", "")))
        elif name == "Skill":
            texts.append("Skill:" + str(given.get("skill", "")).split(":")[-1])
        elif name in ("Bash", "PowerShell"):
            texts += [p for p in map(strip_prefix, segments(str(given.get("command", "")))) if p.startswith(READ_COMMANDS)]
    return texts


def is_test(path):
    lowered = path.replace("\\", "/").lower()
    return "/tests/" in lowered or "/test_" in lowered or lowered.endswith("_test.py")


def order_check(pr, uses, store, say):
    """owner-how.md, then owner-sketch.md, then owner-red.log, all real, all before the first edit of product code."""
    evidence = store / "evidence" / pr
    for name, least in (("owner-how.md", 400), ("owner-sketch.md", 200), ("owner-red.log", 20)):
        target = evidence / name
        say(target.is_file() and target.stat().st_size >= least, f"{name} exists with real content in {evidence}")
    red_file = evidence / "owner-red.log"
    if red_file.is_file():
        red = red_file.read_text("utf-8", errors="replace")
        if pr in NO_RED_TEST:
            say("NO-RED:" in red or re.search(r"\bfailed\b|FAILED|Error", red) is not None, "owner-red.log says why there is no failing test")
        else:
            say(re.search(r"\b\d+ failed\b|FAILED|\bfailed\b|\berror\b|Error|FAIL\b", red) is not None, "owner-red.log shows a real failure")
    seen, first_product = {}, None
    for index, (name, given) in enumerate(uses):
        path = str(given.get("file_path", ""))
        for owner in ("owner-how.md", "owner-sketch.md", "owner-red.log"):
            by_tool = name in ("Write", "Edit") and owner in path
            by_shell = name in ("Bash", "PowerShell") and owner == "owner-red.log" and re.search(r"(>|\btee\s+)\s*\S*owner-red\.log", str(given.get("command", "")))
            if (by_tool or by_shell) and owner not in seen:
                seen[owner] = index
        if name in ("Write", "Edit", "NotebookEdit") and first_product is None and "bld-repair" in path.replace("\\", "/") and not is_test(path):
            first_product = index
    how, sketch, red_at = (seen.get(n) for n in ("owner-how.md", "owner-sketch.md", "owner-red.log"))
    say(how is not None and sketch is not None and how < sketch, "owner-how.md came before owner-sketch.md")
    say(sketch is not None and red_at is not None and sketch < red_at, "owner-sketch.md came before owner-red.log")
    if first_product is None:
        say(True, "no product file was edited by this agent")
    else:
        say(red_at is not None and red_at < first_product, "owner-red.log came before the first edit of product code")


def check(pr, role, store, override, say):
    marker = {"builder": f"dispatch/{pr}.md", "fix": f"dispatch/{pr}-fix.md", "reviewer": f"dispatch/{pr}-review.md"}[role]
    paths = [override] if override else transcripts(marker)
    if not paths:
        say(False, f"no agent transcript names {marker}")
        return
    print(f"INFO transcripts {len(paths)}; newest {paths[-1]}")
    uses, models = [], set()
    for path in paths:
        more, seen = read(path)
        uses += more
        models |= seen
    required = dict(BUILDER if role == "builder" else REVIEWER if role == "reviewer" else FIX)
    if role == "reviewer" and pr in MONEY_ADJACENT:
        required["edge-case lens"] = EDGE_LENS
    opened = opened_texts(uses)
    for label, pattern in required.items():
        say(any(re.search(pattern, text) for text in opened), f"opened {label}")
    say(any("opus" in m for m in models), f"ran on Opus: {sorted(models)}")
    hits = {}
    for name, given in uses:
        if name in ("Bash", "PowerShell"):
            hit = forbidden_in(str(given.get("command", "")))
            if hit:
                hits.setdefault(hit[0], hit[1][:140])
    for label in FORBIDDEN:
        say(label not in hits, f"never {label}" + (f": {hits[label]}" if label in hits else ""))
    writes = [str(g.get("file_path", "")) for n, g in uses if n in ("Write", "Edit", "NotebookEdit")]
    outside = [w for w in writes if re.search(OUT_OF_BOUNDS, w)]
    say(not outside, "wrote nothing out of bounds" + (f": {outside[0]}" if outside else ""))
    if role == "builder":
        order_check(pr, uses, store, say)
    if role == "reviewer":
        reviews = list((store / "review").glob(f"{pr}-check-*.md"))
        say(bool(reviews), f"review file exists for {pr}")
        if reviews:
            first = max(reviews, key=lambda p: p.stat().st_mtime).read_text("utf-8", errors="replace").splitlines()[:1]
            say(bool(first) and first[0].strip() in ("CLEAN", "NOT CLEAN"), "its first line is CLEAN or NOT CLEAN")
    print(f"INFO tool calls {len(uses)}")


def gate(pr, head, store, say):
    """The last lead stacked PRs on its own review and with no lanes run. This refuses both."""
    check(pr, "builder", store, None, say)
    check(pr, "reviewer", store, None, say)
    review = store / "review" / f"{pr}-check-{head[:8]}.md"
    say(review.is_file(), f"a review exists for this exact head: {review.name}")
    if review.is_file():
        first = review.read_text("utf-8", errors="replace").splitlines()[:1]
        say(bool(first) and first[0].strip() == "CLEAN", "that review says CLEAN")
    logs = sorted(p for p in (store / "evidence" / pr).glob("*.log") if not p.name.startswith("owner-"))
    say(len(logs) >= 3, f"lane logs saved by the coordinator: {len(logs)}, at least 3 needed")
    lines = [line for p in logs for line in p.read_text("utf-8", errors="replace").splitlines()]
    print(f"INFO lane lines: PASS {sum(line.startswith('PASS') for line in lines)}, FAIL {sum(line.startswith('FAIL') for line in lines)}. Read them yourself.")


def alive():
    now = time.time()
    for path in glob.glob(str(PROJECT / "*" / "subagents" / "**" / "*.jsonl"), recursive=True):
        changed = pathlib.Path(path).stat().st_mtime
        if now - changed > 86400:
            continue
        found = re.search(r"dispatch/(r\d+[a-z]?(?:-\w+)?)\.md", first_user_line(path))
        if found:
            print(f"INFO {found.group(1)}: transcript changed {(now - changed) / 60:.0f} minutes ago")


def hook(role):
    try:
        event = json.loads(sys.stdin.read() or "{}")
        tool = event.get("tool_name", "")
        given = event.get("tool_input") or {}
        reason = None
        if tool in ("Write", "Edit", "NotebookEdit"):
            target = str(given.get("file_path", "")).replace("\\\\", "/").replace("\\", "/").lower()
            if re.search(OUT_OF_BOUNDS, target):
                reason = f"That path is out of bounds, and an edit inside a virtual environment reaches every environment on this PC: {target}"
            elif not any(ok in target for ok in WRITES_OK.get(role, ())):
                reason = f"A {role} may write only under {', '.join(WRITES_OK.get(role, ()))}. Refused: {target}"
        elif tool == "Bash":
            command = str(given.get("command", ""))
            found = forbidden_in(command)
            parts = [(raw, strip_prefix(raw)) for raw in segments(command)]
            if found:
                reason = f"Refused, because an agent here never {found[0]}. The coordinator owns that: {found[1][:120]}"
            elif given.get("run_in_background"):
                reason = "Do not run in the background. Your cache expires while you wait. Name the command under 'Needs a long run' and the coordinator runs it."
            elif "env.sh" not in command and any(re.match(r"(uv\s|\S*python\S*(\s|$)|pytest\b|\"?\$\w+\"?\s)", part) for _, part in parts):
                reason = f"Start this command with: {ENV} && . That sets the temp and cache folders and holds the credential guard."
            else:
                for raw, part in parts:
                    if re.search(r"\bpytest\b|\bpoethepoet\b", part):
                        limit = re.search(r"\btimeout\s+(\d+)", raw)
                        if not limit or int(limit.group(1)) > MAX_SECONDS:
                            reason = f"Put 'timeout {MAX_SECONDS}' or less in front of it. A longer run goes under 'Needs a long run' for the coordinator, because your cache expires while you wait: {part[:100]}"
                            break
        if reason:
            print(reason, file=sys.stderr)
            return 2
    except Exception:
        return 0
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "alive":
        alive()
        return 0
    if len(argv) >= 3 and argv[1] == "hook":
        return hook(argv[2])
    if len(argv) < 4 or argv[1] not in ("check", "gate"):
        print(__doc__)
        return 2
    override = next((a.split("=", 1)[1] for a in argv[4:] if a.startswith("--transcript=")), None)
    store = pathlib.Path(next((a.split("=", 1)[1] for a in argv[4:] if a.startswith("--store=")), str(STORE)))
    failures = []

    def say(ok, text):
        print(("PASS " if ok else "FAIL ") + text)
        if not ok:
            failures.append(text)

    pr = argv[2].lower()
    if argv[1] == "gate":
        gate(pr, argv[3], store, say)
    else:
        if argv[3] not in ("builder", "fix", "reviewer"):
            print(__doc__)
            return 2
        check(pr, argv[3], store, override, say)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
