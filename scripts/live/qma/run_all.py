"""Run every `s*.py` check in DESIGN section 5 order and print one PASS or FAIL table.

Run it from the agents workspace, so each check gets that Python:

    cd qmx-agents
    uv run --no-sync python ../scripts/live/qma/run_all.py --evidence <evidence folder>

Each check runs in its own process with `QMA_EVIDENCE_DIR` set, so its log lands where it always
did. Its stdout and stderr go to `<evidence>/run_all/<check>.out`. A check passes when it exits 0;
a check that exits 3 is blocked on a missing login and counts as FAIL. OpenRouter turns share
one spend ledger, `<evidence>/openrouter-spend.tsv`, under `--spend-budget`.

Rows that are not run show SKIP with the reason:
- S27 reads a broker credential, so only the operator runs it (SIGNOFF.md says how);
- `--gpt-parked` skips S16, for a build where HP16 is parked;
- `--no-login` skips every row that needs the plan login, a provider key, the ChatGPT sign-in
  or this PC's keyring (the Linux container lane);
- `--skip S36` skips a row by id.

The exit code is 1 when any row is FAIL, and the last line names each one.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Generator, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

HERE: Final = Path(__file__).resolve().parent
SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")
HOST_PORT: Final = 8876
CHECK_TIMEOUT_S: Final = 1200.0


class Need(StrEnum):
    PLAN = "the plan login"
    OPENROUTER = "the OpenRouter key"
    GPT = "the ChatGPT sign-in"
    KEYRING = "this PC's keyring"
    HOST = "a running qma.serve host"
    OPERATOR = "the operator"


class Verdict(StrEnum):
    PASS = "PASS"  # noqa: S105
    FAIL = "FAIL"
    SKIP = "SKIP"


NO_LOGIN: Final = frozenset({Need.PLAN, Need.OPENROUTER, Need.GPT, Need.KEYRING, Need.HOST})


@dataclass(frozen=True)
class Check:
    id: str
    script: str
    args: tuple[str, ...] = ()
    needs: frozenset[Need] = frozenset()
    label: str = ""


def check(
    id: str,
    script: str,
    *args: str,
    needs: Sequence[Need] = (),
    label: str = "",
) -> Check:
    """`label` names the row; it defaults to the id and the script's first argument."""
    first = args[:1] if args and not args[0].startswith("-") else ()
    return Check(id, script, args, frozenset(needs), label or " ".join((id, *first)))


PLAN, ROUTER, GPT, KEYS, HOST = Need.PLAN, Need.OPENROUTER, Need.GPT, Need.KEYRING, Need.HOST

CHECKS: Final[tuple[Check, ...]] = (
    check("S1", "s01_install.py", needs=[PLAN]),
    check("S2", "s02_login.py", needs=[PLAN]),
    check("S3", "s03_tools.py", needs=[PLAN]),
    check("S4", "s04_vanilla.py", "check2", needs=[PLAN]),
    check("S5", "s05_permissions.py"),
    check("S6", "s06_money.py", "bypass", needs=[PLAN]),
    check("S6", "s06_money.py", "agent", needs=[PLAN]),
    check("S6", "s06_money.py", "neg", needs=[PLAN]),
    check("S6a", "s06a_gate_alone.py"),
    check("S6a", "s06a_gate_alone.py", "agent"),
    check("S6b", "s06b_rules_alone.py"),
    check("S7", "s07_isolation.py", needs=[PLAN]),
    check(
        "S8",
        "s08_providers.py",
        "rows",
        "--budget",
        "{budget}",
        "--ledger",
        "{ledger}",
        needs=[ROUTER],
    ),
    check("S9", "s09_leak.py"),
    check("S10", "s10_usage.py", "meter", needs=[PLAN]),
    check("S10", "s10_usage.py", "overage", needs=[PLAN]),
    check("S10", "s10_usage.py", "credits", needs=[PLAN]),
    check("S10", "s10_usage.py", "merge", needs=[PLAN]),
    check("S10", "s10_usage.py", "expiry", needs=[PLAN]),
    check("S10", "s10_usage.py", "restart", needs=[PLAN]),
    check("S11", "s11_helpers.py", "nested"),
    check("S11", "s11_helpers.py", "background"),
    check("S11", "s11_helpers.py", "model"),
    check("S11", "s11_helpers.py", "kimi", needs=[ROUTER]),
    check("S11", "s11_helpers.py", "tools"),
    check("S11", "s11_helpers.py", "subagent"),
    check("S11", "s11_helpers.py", "full"),
    check("S11", "s11_helpers.py", "allowlist"),
    check("S11", "s11_helpers.py", "unattended"),
    check("S12", "s12_interrupt.py", needs=[PLAN]),
    check("S12", "s12_interrupt.py", "--bash", label="S12 bash"),
    check("S13", "s13_compact.py", needs=[PLAN]),
    check("S14", "s14_resume.py", "all", needs=[PLAN, KEYS]),
    check("S15", "s15_event_wire.py", "wire"),
    check("S15", "s15_event_wire.py", "restart"),
    check("S15", "s15_event_wire.py", "concurrent"),
    check("S15", "s15_event_wire.py", "question"),
    check(
        "S16", "s16_gpt.py", "--only", "lanes", "--prefix", "hp17-", needs=[GPT], label="S16 lanes"
    ),
    check("S17", "s17_secrets.py", "--slug", "hp17-s17", needs=[KEYS]),
    check("S18", "s18_ram.py", needs=[PLAN]),
    check("S19", "s19_boot.py", needs=[PLAN, KEYS]),
    check("S20", "s20_live_edit.py", needs=[PLAN], label="S20 live"),
    check("S20", "s20_settings.py", needs=[KEYS, HOST], label="S20 settings"),
    check("S21", "s21_canary.py"),
    check("S21ab", "s21ab_layers.py"),
    check("S21c", "s21c_egress.py"),
    check("S21d", "s21d_redaction.py", needs=[PLAN]),
    check("S21e", "s21e_relayed_home.py"),
    check("S22", "s22_relay.py"),
    check("S23", "s23_no_key_env.py"),
    check("S24", "s24_usage_once.py", label="S24 key"),
    check("S24", "s24_usage_plan.py", needs=[PLAN], label="S24 plan"),
    check("S25", "s25_untrusted.py", needs=[PLAN]),
    check("S26", "s26_posture.py", "unknown", needs=[KEYS]),
    check("S26", "s26_posture.py", "unreachable", needs=[KEYS]),
    check("S26", "s26_posture.py", "proven", needs=[KEYS]),
    check("S27", "s27_broker_scope.py", needs=[Need.OPERATOR]),
    check("S28", "s28_effects.py"),
    check("S29", "s29_approvals.py"),
    check("S29a", "s29a_grants_alone.py"),
    check("S30", "s30_os_cap.py", needs=[PLAN]),
    check("S30b", "s30b_orphans.py", needs=[PLAN]),
    check("S31", "s31_chat_cap.py", "idle"),
    check("S31", "s31_chat_cap.py", "busy"),
    check("S32", "s32_reaping.py"),
    check("S33", "s33_one_writer.py"),
    check("S34", "s34_quote_stale.py"),
    check("S35", "s35_external_mcp.py"),
    check("S35u", "s35u_unattended_external.py"),
    check("S36", "s36_switch_resume.py", needs=[PLAN, ROUTER]),
    check("S37", "s37_effort.py"),
    check("S38", "s38_timeout.py"),
    check("S39", "s39_unattended.py"),
    check("S40", "s40_background_relaunch.py"),
    check("S41", "s41_model_ids.py"),
)


@dataclass(frozen=True)
class Outcome:
    check: Check
    verdict: Verdict
    seconds: float = 0.0
    note: str = ""


@dataclass(frozen=True)
class Plan:
    scripts: Path
    evidence: Path
    budget: float = 0.05
    timeout: float = CHECK_TIMEOUT_S
    skip: dict[str, str] = field(default_factory=dict[str, str])
    host_home: Path = SHIP_HOME
    scratch: Path | None = None


def skip_reasons(
    checks: Sequence[Check], *, gpt_parked: bool, no_login: bool, skip: Sequence[str]
) -> dict[str, str]:
    """Why each skipped row is skipped, by label."""
    reasons: dict[str, str] = {}
    for found in checks:
        if Need.OPERATOR in found.needs:
            reasons[found.label] = "only the operator runs it"
        elif gpt_parked and found.id == "S16":
            reasons[found.label] = "HP16 is parked"
        elif no_login and found.needs & NO_LOGIN:
            needs = ", ".join(sorted(need.value for need in found.needs & NO_LOGIN))
            reasons[found.label] = f"needs {needs}"
        elif found.id in skip:
            reasons[found.label] = "skipped on the command line"
    return reasons


def kill_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(process.pid)],  # noqa: S607
            capture_output=True,
            check=False,
        )
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def spawn(
    argv: Sequence[str], *, cwd: Path, env: dict[str, str], out: Path
) -> subprocess.Popen[bytes]:
    with out.open("wb") as sink:
        return subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdout=sink,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )


@contextlib.contextmanager
def host(plan: Plan, env: dict[str, str]) -> Generator[None]:
    """`qma.serve` on `HOST_PORT`, up until `/api/health` answers."""
    argv = [sys.executable, "-m", "qma.serve", "serve", "--home", str(plan.host_home)]
    out = plan.evidence / "run_all" / "host.out"
    process = spawn([*argv, "--port", str(HOST_PORT)], cwd=plan.scripts, env=env, out=out)
    try:
        deadline = time.monotonic() + 60
        while not healthy():
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(f"the host did not come up; see {out}")
            time.sleep(0.5)
        yield
    finally:
        kill_tree(process)


def healthy() -> bool:
    """True once the host answers. `/api/health` wants the control token, so a 401 counts."""
    url = f"http://127.0.0.1:{HOST_PORT}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except urllib.error.HTTPError:
        return True
    except OSError:
        return False


def last_line(path: Path) -> str:
    lines = [
        line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
    ]
    found = next((line for line in reversed(lines) if line), "")
    return found if len(found) <= 100 else found[:97] + "..."


def run_one(found: Check, plan: Plan) -> Outcome:
    ledger = plan.evidence / "openrouter-spend.tsv"
    args = [arg.format(budget=plan.budget, ledger=ledger) for arg in found.args]
    env = os.environ | {
        "QMA_EVIDENCE_DIR": str(plan.evidence),
        "QMA_SPEND_BUDGET": str(plan.budget),
        "QMA_SPEND_LEDGER": ledger.name,
        "PYTHONIOENCODING": "utf-8",
    }
    if plan.scratch is not None:
        env["QMA_LIVE_SCRATCH"] = str(plan.scratch)
    out = plan.evidence / "run_all" / f"{found.label.replace(' ', '-')}.out"
    started = time.monotonic()
    with contextlib.ExitStack() as stack:
        try:
            if Need.HOST in found.needs:
                stack.enter_context(host(plan, env))
        except RuntimeError as failed:
            return Outcome(found, Verdict.FAIL, time.monotonic() - started, str(failed))
        process = spawn(
            [sys.executable, str(plan.scripts / found.script), *args],
            cwd=plan.scripts,
            env=env,
            out=out,
        )
        try:
            code = process.wait(timeout=plan.timeout)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            seconds = time.monotonic() - started
            return Outcome(found, Verdict.FAIL, seconds, f"timed out after {plan.timeout:.0f} s")
    seconds = time.monotonic() - started
    if code == 0:
        return Outcome(found, Verdict.PASS, seconds)
    return Outcome(found, Verdict.FAIL, seconds, f"exit {code}: {last_line(out)}")


def run(checks: Sequence[Check], plan: Plan) -> list[Outcome]:
    (plan.evidence / "run_all").mkdir(parents=True, exist_ok=True)
    outcomes: list[Outcome] = []
    for found in checks:
        reason = plan.skip.get(found.label)
        outcome = Outcome(found, Verdict.SKIP, note=reason) if reason else run_one(found, plan)
        print(f"{outcome.verdict} {found.label} {outcome.seconds:.0f}s {outcome.note}", flush=True)
        outcomes.append(outcome)
    return outcomes


def row(outcome: Outcome) -> str:
    found = outcome.check
    seconds = f"{outcome.seconds:.0f}" if outcome.verdict is not Verdict.SKIP else ""
    cells = (found.label, found.script, outcome.verdict.value, seconds, outcome.note)
    return "| " + " | ".join(cell.replace("|", "/") for cell in cells) + " |"


def table(outcomes: Sequence[Outcome]) -> str:
    counts = {verdict: sum(o.verdict is verdict for o in outcomes) for verdict in Verdict}
    total = sum(outcome.seconds for outcome in outcomes)
    failed = [o.check.label for o in outcomes if o.verdict is Verdict.FAIL]
    lines = [
        "| Check | Script | Verdict | Seconds | Note |",
        "|---|---|---|---|---|",
        *(row(outcome) for outcome in outcomes),
        "",
        f"{counts[Verdict.PASS]} PASS, {counts[Verdict.FAIL]} FAIL, {counts[Verdict.SKIP]} SKIP"
        f" in {total / 60:.1f} min",
    ]
    if failed:
        lines.append(f"FAIL: {', '.join(failed)}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_all.py", description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--evidence", type=Path, default=os.environ.get("QMA_EVIDENCE_DIR"))
    parser.add_argument("--scripts", type=Path, default=HERE)
    parser.add_argument("--only", nargs="+", default=[], metavar="ID")
    parser.add_argument("--skip", nargs="+", default=[], metavar="ID")
    parser.add_argument("--gpt-parked", action="store_true")
    parser.add_argument("--no-login", action="store_true")
    parser.add_argument("--spend-budget", type=float, default=0.05)
    parser.add_argument("--timeout", type=float, default=CHECK_TIMEOUT_S)
    parser.add_argument(
        "--scratch", type=Path, help="QMA_LIVE_SCRATCH for every check, so no earlier lane's files"
    )
    args = parser.parse_args(argv)
    if args.evidence is None:
        parser.error("set --evidence or QMA_EVIDENCE_DIR")
    checks = [found for found in CHECKS if not args.only or found.id in args.only]
    reasons = skip_reasons(
        checks, gpt_parked=args.gpt_parked, no_login=args.no_login, skip=args.skip
    )
    plan = Plan(
        args.scripts, args.evidence, args.spend_budget, args.timeout, reasons, scratch=args.scratch
    )
    outcomes = run(checks, plan)
    print(table(outcomes), flush=True)
    return 1 if any(outcome.verdict is Verdict.FAIL for outcome in outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
