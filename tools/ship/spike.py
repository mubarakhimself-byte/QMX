"""spike: seven probes of the real `claude` CLI that the headless design rests on (unit U06).

`python tools/ship spike --program <scratch folder>` uses the cheapest model (haiku, effort low) and a
one-line prompt per run, three runs in all. It writes `workers/spike/SPIKE.md` (one PASS or FAIL line
per probe, then each command and its raw output) and `roles/RESULT-SHAPE.md` (the result fields the
parser reads). The scratch folder gets a throwaway state.json with one held slice, so the hook has a
worktree to allow.

1. a run started by a detached parent is alive after the parent exits, and finishes;
2. with `--settings roles/builder.json`, a Write outside the worktree is refused by the hook;
3. with `--permission-prompts none`, a tool outside the allow-list is refused and the run ends;
4. the result names the model that was asked for;
5. the result JSON parses and `session_id` equals the `--session-id` passed;
6. the working folder is the one given, and no trust prompt stops a run in a new folder;
7. `claude auth status` shows the plan login (claude.ai), not an API key.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from ship import launch as ln
from ship import state as st
from ship.layout import Program
from ship.plan import init_state
from ship.proc import pid_alive
from ship.settings import Settings

MODEL = "haiku"
REDACT = ("email", "orgId", "orgName", "accountUuid", "organizationUuid")


def spike_role(timeout_s: float = 300) -> ln.Role:
    return ln.Role("spike", MODEL, "low", False, timeout_s, ln.ROLES_DIR / "builder.json")


def folder(program: Program) -> Path:
    return program.workers / "spike"


def _fresh(program: Program, tag: str) -> Path:
    path = folder(program) / f"fresh-{tag}-{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True)
    return path


def _norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path.strip().strip("`'\"").replace("/", os.sep)))


def scratch_state(program: Program) -> Path:
    """A state.json with slice sp1 held, so the hook allows its worktree. Returns the worktree."""
    wt_root = program.dir / "wt"
    if not program.state.exists():
        program.slices_md.write_text("| id | name | depends on | files | size |\n|---|---|---|---|---|\n"
                                     "| sp1 | Spike | - | inside.txt | S |\n", "utf-8", newline="\n")
        init_state(program.dir, program.dir, "build/spike", wt_root, "origin")
        with st.locked(program) as state:
            sl = state.slices["sp1"]
            sl.status, sl.attempts = st.Status.HELD, 1
            sl.holder = st.Holder("sp1-a1-r0-spike", 1, 0, st.now_iso())
    wt = wt_root / "slice-sp1"
    wt.mkdir(parents=True, exist_ok=True)
    return wt


def parent(program: Program) -> int:
    """Start the child detached, write its pid, exit at once."""
    argv = [sys.executable, str(ln.KIT), "spike", "--program", str(program.dir), "--child"]
    log = open(folder(program) / "child.log", "w", encoding="utf-8")
    kwargs = ln.detached_kwargs()
    try:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **kwargs)
        how = "detached"
    except OSError as exc:  # a job that forbids breakaway refuses CREATE_BREAKAWAY_FROM_JOB
        kwargs["creationflags"] = kwargs.get("creationflags", 0) & ~getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0)
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, **kwargs)
        how = f"detached without breakaway ({exc})"
    (folder(program) / "child.pid").write_text(json.dumps({"pid": child.pid, "parent": os.getpid(), "how": how}),
                                               "utf-8")
    return 0


def child(program: Program, settings: Settings) -> int:
    """Run 1 (probes 1, 4, 5, 6): a tiny run in a folder never opened before."""
    cwd = _fresh(program, "child")
    prompt = ("Use no tools. Reply with exactly one line: the word DONE, a space, then your current "
              "working directory exactly as your environment states it.")
    handle = ln.launch(spike_role(), prompt, cwd, program, "spike-child", settings, label="child")
    while (got := handle.poll()) is None:
        time.sleep(2)
    (folder(program) / "child.json").write_text(json.dumps(
        {"cwd": str(cwd), "session_asked": handle.session_id, "pid": os.getpid(), "result": got.__dict__},
        indent=2), "utf-8")
    return 0


def _raw(program: Program, worker: str) -> str:
    base = program.workers / worker
    started = json.loads((base / "started.json").read_text("utf-8")) if (base / "started.json").exists() else {}
    argv = started.get("argv", [])
    out = (base / "stdout.log").read_text("utf-8", errors="replace") if (base / "stdout.log").exists() else ""
    err = (base / "stderr.log").read_text("utf-8", errors="replace") if (base / "stderr.log").exists() else ""
    return (f"### {worker}\n\ncwd: `{started.get('cwd')}`\n\n```\n{subprocess.list2cmdline(argv)}\n```\n\n"
            f"stdout:\n\n```json\n{out.strip()}\n```\n\nstderr:\n\n```\n{err.strip() or '(empty)'}\n```\n")


def probe_detached(program: Program) -> tuple[list[tuple[int, bool, str]], dict]:
    marker = folder(program) / "child.pid"
    marker.unlink(missing_ok=True)
    (folder(program) / "child.json").unlink(missing_ok=True)
    started = time.monotonic()
    subprocess.run([sys.executable, str(ln.KIT), "spike", "--program", str(program.dir), "--parent"],
                   stdin=subprocess.DEVNULL, check=True, timeout=60)
    info = json.loads(marker.read_text("utf-8"))
    parent_gone = not pid_alive(info["parent"])
    alive = pid_alive(info["pid"])
    while pid_alive(info["pid"]) and time.monotonic() - started < 600:
        time.sleep(2)
    summary_path = folder(program) / "child.json"
    summary = json.loads(summary_path.read_text("utf-8")) if summary_path.exists() else {}
    ok1 = parent_gone and alive and bool(summary)
    detail = (f"parent pid {info['parent']} exited={parent_gone}; child pid {info['pid']} alive after it={alive} "
              f"({info['how']}); child finished its run={bool(summary)}")
    return [(1, ok1, detail)], summary


def check_child(summary: dict) -> list[tuple[int, bool, str]]:
    res = summary.get("result") or {}
    models = res.get("models") or []
    ok4 = any(ln.same_model(MODEL, m) for m in models)
    ok5 = res.get("kind") == "ok" and res.get("session_id") == summary.get("session_asked")
    said = res.get("value", "")
    ok6 = res.get("kind") == "ok" and _norm(said) == _norm(summary.get("cwd", "?"))
    return [(4, ok4, f"asked {MODEL!r}; modelUsage names {models}"),
            (5, ok5, f"kind {res.get('kind')}; session_id {res.get('session_id')} vs passed {summary.get('session_asked')}"),
            (6, ok6, f"ran in {summary.get('cwd')}; it said {said!r}; ended on its own with kind {res.get('kind')}")]


def probe_hook(program: Program, settings: Settings) -> tuple[int, bool, str]:
    wt = scratch_state(program)
    inside, outside = wt / "inside.txt", program.dir / "outside.txt"
    inside.unlink(missing_ok=True)
    outside.unlink(missing_ok=True)
    prompt = (f"Use the Write tool twice and no other tool: write the text x to {inside.as_posix()}, then write "
              f"the text x to {outside.as_posix()}. Then reply with exactly one line: DONE written")
    got = ln.run(spike_role(), prompt, wt, program, "spike-hook", settings, label="hook")
    ok = inside.exists() and not outside.exists()
    return (2, ok, f"inside the worktree written={inside.exists()}; outside written={outside.exists()}; "
                   f"denials {got.denials}; kind {got.kind}; text {got.text[-200:]!r}")


def probe_prompts(program: Program, settings: Settings) -> tuple[int, bool, str]:
    cwd = _fresh(program, "perm")
    prompt = ("Use the WebFetch tool once to fetch https://example.com. If it is refused, do not retry and use "
              "no other tool; reply with exactly one line: DONE refused")
    began = time.monotonic()
    got = ln.run(spike_role(timeout_s=300), prompt, cwd, program, "spike-perm", settings, label="perm")
    took = time.monotonic() - began
    ok = got.kind != "timeout" and any("WebFetch" in d for d in got.denials)
    return (3, ok, f"ended on its own after {took:.0f}s (kind {got.kind}); denials {got.denials}; "
                   f"text {got.text[-200:]!r}")


def probe_auth(program: Program, settings: Settings) -> tuple[tuple[int, bool, str], str]:
    env = ln.worker_env(spike_role(), program, settings)
    done = subprocess.run([*settings.claude, "auth", "status"], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, stdin=subprocess.DEVNULL, timeout=120)
    try:
        data = json.loads(done.stdout)
    except ValueError:
        data = {}
    shown = {k: ("<redacted>" if k in REDACT else v) for k, v in data.items()}
    keys = sorted(k for k in env if k.upper().startswith(("ANTHROPIC", "CLAUDE")))
    ok = data.get("loggedIn") is True and data.get("authMethod") == "claude.ai" and keys == [ln.DEPTH_VAR]
    raw = (f"### auth\n\n```\n{subprocess.list2cmdline([*settings.claude, 'auth', 'status'])}\n```\n\n"
           f"```json\n{json.dumps(shown, indent=2)}\n```\n\nCLAUDE*/ANTHROPIC* variables in the worker env: {keys}\n")
    return (7, ok, f"loggedIn {data.get('loggedIn')}, authMethod {data.get('authMethod')}, apiProvider "
                   f"{data.get('apiProvider')}, plan {data.get('subscriptionType')}; worker env holds only {keys}"), raw


def result_shape(program: Program, settings: Settings) -> str:
    out = (program.workers / "spike-child" / "stdout.log").read_text("utf-8", errors="replace")
    data = ln._json_object(out) or {}
    perm = ln._json_object((program.workers / "spike-perm" / "stdout.log").read_text("utf-8", errors="replace")
                           if (program.workers / "spike-perm" / "stdout.log").exists() else "") or {}
    usage = next(iter((data.get("modelUsage") or {}).values()), {})
    denial = (perm.get("permission_denials") or [{}])[0]
    fields = "\n".join(f"| `{k}` | {type(v).__name__} |" for k, v in sorted(data.items()))
    return f"""# Result shape of a headless run

Recorded by `ship spike` on {time.strftime('%Y-%m-%d')} with `claude {_version(settings)}`, `-p ... --output-format json`.
`launch.parse_result` follows this file. Stdout is one JSON object on one line.

## A normal ending

| Field | Type |
|---|---|
{fields}

Used by the kit:

- `result`: the final text. Its last non-blank line is the reply contract (`READY`, `BLOCKED`, `DONE`, `WAITS`).
- `session_id`: equals the `--session-id` passed.
- `modelUsage`: one key per model that ran, the full id (`claude-haiku-5-5` for `--model haiku`). Fields of one
  entry: {', '.join(f'`{k}`' for k in usage)}. A run may list a second, smaller model for housekeeping, so a
  fallback is read as "the asked model is absent and the fallback model is present".
- `permission_denials`: one object per refused tool call, fields {', '.join(f'`{k}`' for k in denial) or '(none seen)'}.
- `is_error`, `subtype` (`success` on a normal end), `api_error_status` (null on a normal end).

## A usage-limit ending

None was seen during the spike. Until one is recorded here, `launch.parse_result` calls a run a limit when its
text (or stderr, or `api_error_status`) holds one of the `limit_patterns` settings and it has no contract line,
and reads the reset time from a `|<epoch seconds>` suffix (the CLI's `Claude AI usage limit reached|<epoch>`
form), else from an ISO time in the text, else now plus `limit_backoff_s`. Record the real shape here the first
time a worker ends on a limit (its `workers/<id>/stdout.log`).
"""


def _version(settings: Settings) -> str:
    try:
        return subprocess.run([*settings.claude, "--version"], capture_output=True, text=True,
                              stdin=subprocess.DEVNULL, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "?"


def spike(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    folder(program).mkdir(parents=True, exist_ok=True)
    scratch_state(program)
    results, summary = probe_detached(program)
    results += check_child(summary)
    results.append(probe_hook(program, settings))
    results.append(probe_prompts(program, settings))
    auth, auth_raw = probe_auth(program, settings)
    results.append(auth)
    results.sort()
    lines = [f"{'PASS' if ok else 'FAIL'} {n} {detail}" for n, ok, detail in results]
    raws = "\n".join(_raw(program, w) for w in ("spike-child", "spike-hook", "spike-perm")) + "\n" + auth_raw
    child_log = folder(program) / "child.log"
    body = (f"# Spike {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n" + "\n".join(lines) + "\n\n## Raw\n\n"
            "Run 1 (probes 1, 4, 5, 6) is `spike-child`, started by `ship spike --parent` as a detached child; its "
            f"log: `{child_log}`.\n\n" + raws)
    (folder(program) / "SPIKE.md").write_text(body, "utf-8", newline="\n")
    if summary:
        (ln.ROLES_DIR / "RESULT-SHAPE.md").write_text(result_shape(program, settings), "utf-8", newline="\n")
    return all(ok for _, ok, _ in results), lines + [f"SPIKE {folder(program) / 'SPIKE.md'}"]


def probe_model(program: Program, settings: Settings, model: str, effort: str,
                fallback: str | None = None) -> tuple[str, bool, str]:
    """A one-line run on a role's real model (D-L15): it answers, and the result names the model."""
    role = ln.Role(f"spike-{model}", model, effort, False, 600, ln.ROLES_DIR / "builder.json", fallback)
    cwd = _fresh(program, model.replace("/", "-"))
    got = ln.run(role, "Use no tools. Reply with exactly one line: DONE ok", cwd, program, f"spike-model-{model}",
                 settings, label=model)
    asked = any(ln.same_model(model, m) for m in got.models)
    ok = got.kind == "ok" and (asked or got.fell_back)
    how = f"fell back ({got.note})" if got.fell_back else ("ran as asked" if asked else "ran on another model")
    return (f"model {model} effort {effort}" + (f" fallback {fallback}" if fallback else ""), ok,
            f"kind {got.kind}; modelUsage {got.models}; {how}; text {got.text[-80:]!r}")


def recheck(program: Program, settings: Settings) -> tuple[bool, list[str]]:
    """The K2 fix-round reruns under the isolation flags (D-L10, D-L11, D-L15): probes 2, 3 and 7, and one
    model probe each for opus at effort high and for fable with its fallback. Appends to roles/SPIKE.md."""
    folder(program).mkdir(parents=True, exist_ok=True)
    rows = [probe_hook(program, settings), probe_prompts(program, settings)]
    auth, auth_raw = probe_auth(program, settings)
    hook_run = ln._json_object((program.workers / "spike-hook" / "stdout.log").read_text("utf-8", errors="replace")) or {}
    logged_in = bool(hook_run.get("modelUsage")) and not hook_run.get("is_error")
    rows.append((7, auth[1] and logged_in, auth[2] + f"; a run under --setting-sources project,local and the env "
                                                     f"allow-list answered on the plan login: {logged_in}"))
    rows.append(probe_model(program, settings, "claude-opus-5-5", "high"))
    rows.append(probe_model(program, settings, "fable", "high", "claude-opus-5-5"))
    lines = [f"{'PASS' if ok else 'FAIL'} {n} {detail}" for n, ok, detail in rows]
    raws = "\n".join(_raw(program, w) for w in ("spike-hook", "spike-perm", "spike-model-claude-opus-5-5",
                                                  "spike-model-fable")) + "\n" + auth_raw
    body = (f"\n## Recheck {time.strftime('%Y-%m-%d %H:%M:%S')}: the K2 fix round's isolation\n\n"
            "Every run below adds `--setting-sources project,local --strict-mcp-config`, gets only the allow-listed "
            "environment, and uses the narrowed `builder.json` whose hook ends `|| exit 2`.\n\n"
            + "\n".join(lines) + "\n\n### Raw\n\n" + raws)
    with open(ln.ROLES_DIR / "SPIKE.md", "a", encoding="utf-8", newline="\n") as out:
        out.write(body)
    return all(ok for _, ok, _ in rows), lines
