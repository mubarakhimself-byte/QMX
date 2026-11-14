"""Command line: `python tools/ship <command> --program <folder> ...`. See README.md for the table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ship.layout import Program  # noqa: E402
from ship.settings import load_settings  # noqa: E402


def _lines(ok: bool, lines: list[str]) -> int:
    for line in lines:
        print(line)
    return 0 if ok else 1


def cmd_init(a, program, settings):
    from ship.plan import init_state

    if settings.ci == "github" and not a.build_branch.startswith("build/"):
        print(f"REFUSED build branch {a.build_branch}: with ci = \"github\" (set in ship.toml) qmx-ci runs its "
              "land level on build/** only; name it build/<name>, or leave ci at its default, \"local\"")
        return 1
    print(init_state(program.dir, Path(a.repo), a.build_branch, Path(a.worktree_root), a.remote))
    return 0


def cmd_dispatch(a, program, settings):
    from ship.dispatch import Parked, Refused, dispatch

    try:
        got = dispatch(program, a.slice, settings)
    except Refused as exc:
        print(f"REFUSED {a.slice}: {exc}")
        return 2
    print(got.to_json())
    return 3 if isinstance(got, Parked) else 0


def cmd_verify_ready(a, program, settings):
    from ship.verify_ready import Unreachable, verify_ready

    try:
        return _lines(*verify_ready(program, a.slice, a.sha, settings))
    except Unreachable as exc:
        print(f"UNREACHABLE {a.slice}: {exc}; nothing changed, try again later")
        return 3


def cmd_slice_checks(a, program, settings):
    from ship.slice_checks import slice_checks

    return _lines(*slice_checks(program, a.slice, settings))


def cmd_timed(a, program, settings):
    from ship.wrapper import run_timed

    argv = a.argv[1:] if a.argv[:1] == ["--"] else a.argv
    if not a.slice or ".." in a.slice or not all(c.isalnum() or c in "_.-" for c in a.slice):
        raise SystemExit(f"ship timed: --slice {a.slice!r} is not a plain name")  # it names heartbeat/<slice>
    result = run_timed(argv, Path.cwd(), Path(a.log), a.timeout or settings.check_timeout_s, settings,
                       program.runs, program.heartbeat(a.slice))
    print(f"EXIT rc={result.rc} seconds={result.seconds:.0f}" + (" timeout" if result.timed_out else ""))
    return result.rc


def cmd_land(a, program, settings):
    from ship.land import land

    return _lines(*land(program, a.slices or None, settings))


def cmd_nightly(a, program, settings):
    from ship.nightly import nightly

    ok, lines = nightly(program, settings, wait=not a.no_wait)
    for line in lines:
        print(line)
    return {True: 0, False: 1, None: 2}[ok]


def cmd_ci(a, program, settings):
    from ship import ci
    from ship.nightly import ci_status

    if a.action == "start":
        try:
            lines = ci.start(program, settings, level=a.level, fresh=a.fresh)
        except ci.Unavailable as exc:
            print(f"UNAVAILABLE {exc}; ship nightly runs locally instead")
            return 1
        rc = 0
    elif a.action == "status":
        step = lambda: ci_status(program, settings)
        rc, lines = ci.wait(step, settings) if a.wait else step()
    elif a.action == "gate":
        step = lambda: ci.gate(program, settings, a.pr)
        rc, lines = ci.wait(step, settings) if a.wait else step()
    elif a.action == "summary":
        rc, lines = ci.summary(program, settings, a.sha)
    else:
        if not a.run_id:
            raise SystemExit("ship ci read needs a run id")
        rc, lines = ci.report(program, settings, a.run_id)
    for line in lines:
        print(line)
    return rc


def cmd_bisect_step(a, program, settings):
    from ship.nightly import bisect_step

    return bisect_step(program, Path.cwd(), Path(a.ids), settings)


def cmd_power_watch(a, program, settings):
    from ship.power_watch import watch

    return watch(program, settings, once=a.once)


def cmd_power(a, program, settings):
    from ship.power_watch import power_report

    rc, lines = power_report(program, settings)
    for line in lines:
        print(line)
    return rc


def cmd_merged(a, program, settings):
    from ship import state as st

    try:
        with st.locked(program) as state:
            print(state.mark_merged(a.checkpoint))
    except st.StateError as exc:
        print(f"REFUSED {exc}")
        return 1
    return 0


def cmd_quality(a, program, settings):
    from ship.quality import checkpoint_quality

    return _lines(*checkpoint_quality(program, settings, a.base, _tools(a.tools)))


def cmd_baseline(a, program, settings):
    from ship.quality import BASELINE_MOVED

    print(BASELINE_MOVED)
    return 1


def _tools(text: str) -> tuple[str, ...]:
    from ship.quality import TOOLS

    tools = tuple(t.strip() for t in text.split(",") if t.strip())
    unknown = sorted(set(tools) - set(TOOLS))
    if unknown:
        raise SystemExit(f"--tools: unknown {unknown}; known {list(TOOLS)}")
    return tools


def cmd_recover(a, program, settings):
    from ship.recover import recover

    return _lines(True, recover(program, settings, a.usage_reset))


def cmd_run_report(a, program, settings):
    from ship.run_report import write_report

    ok, path = write_report(program, settings)
    print(path)
    return 0 if ok else 1


def cmd_preflight(a, program, settings):
    from ship.preflight import preflight

    return _lines(*preflight(program, settings, protection_push_test=a.protection_push_test))


def cmd_teardown(a, program, settings):
    from ship.armed import teardown

    return _lines(*teardown(program, settings))


def cmd_main_check(a, program, settings):
    from ship.preflight import main_check

    return _lines(*main_check(program, settings))


def cmd_status(a, program, settings):
    from ship.status import status

    return _lines(*status(program, settings))


def cmd_park(a, program, settings):
    from ship import state as st
    from ship.state import ParkCause

    with st.locked(program) as state:
        blocked = state.park(a.slice, ParkCause(a.cause), a.why)
    print(json.dumps({"parked": a.slice, "blocked": blocked}))
    return 0


def cmd_hook(a, program, settings):
    try:
        from ship.hook import main as hook_main

        return hook_main(program, sys.stdin.read())
    except BaseException as exc:  # noqa: BLE001 - the guard fails closed (D-L9)
        print(f"ship hook: refusing, the guard itself failed: {exc!r}", file=sys.stderr)
        return 2


# U03: plans worktree and records
def cmd_records(a):
    from ship import records
    from ship.layout import records_of
    from ship.settings import Settings

    settings, plans = Settings(), a.plans.resolve()
    if a.action == "init":
        if not a.repo:
            raise SystemExit("ship records init needs --repo")
        try:
            lines = records.init(Path(a.repo), plans, a.remote, settings)
        except records.RecordsError as exc:
            print(f"REFUSED {exc}")
            return 1
        return _lines(True, lines)
    if a.action == "commit":
        if not a.message:
            raise SystemExit("ship records commit needs -m MESSAGE")
        lines: list[str] = []
        with records.locked(records_of(plans)):
            sha = records.commit(plans, a.message, settings, remote=a.remote, lines=lines, paths=None)
        return _lines(True, lines + [f"COMMIT {sha}" if sha else "NOTHING to commit"])
    if not (a.repo and a.prefix):
        raise SystemExit("ship records prefix needs --repo and a prefix")
    clashes = records.prefix_clashes(plans, Path(a.repo), a.remote, a.prefix, settings)
    return _lines(not clashes, [f"CLASH {c}" for c in clashes] or [f"FREE {a.prefix}"])


# U04: index v2 parser and ship phase
def cmd_phase(a):
    from ship import phase

    if a.words:
        return _lines(True, list(phase.WORDS))
    if a.all:
        if not a.plans:
            raise SystemExit("ship phase --all needs --plans")
        blocks = [phase.read(Program(f.resolve()), load_settings(f)) for f in phase.all_programs(a.plans)]
        for n, block in enumerate(blocks):
            if n:
                print()
            for key, value in block.items():
                print(f"{key}: {value}")
        return 0
    if not a.program:
        raise SystemExit("ship phase needs --program, --all --plans, or --words")
    program = Program(a.program.resolve())
    if a.set:
        if not (a.status and a.by):
            raise SystemExit("ship phase --set needs --status and --by")
        record = phase.set_phase(program, a.set, a.status, a.by)
        return _lines(True, [f"{k}: {v}" for k, v in record.items()])
    return _lines(True, [f"{k}: {v}" for k, v in phase.read(program, load_settings(program.dir)).items()])


def cmd_gate(a, program, settings):
    from ship.program import ProgramError, set_gate

    try:
        print(set_gate(program, a.name, a.by, a.source, a.advance))
    except ProgramError as exc:
        print(f"REFUSED {exc}")
        return 1
    return 0


# U06: headless launcher and spike
def cmd_spike(a, program, settings):
    from ship import spike

    program.dir.mkdir(parents=True, exist_ok=True)
    (program.workers / "spike").mkdir(parents=True, exist_ok=True)
    if a.parent:
        return spike.parent(program)
    if a.child:
        return spike.child(program, settings)
    if a.recheck:
        return _lines(*spike.recheck(program, settings))
    return _lines(*spike.spike(program, settings))


# U07: ship run, the build loop
def cmd_run(a, program, settings):
    from ship.run import run

    return run(program, settings, once=a.once)


def cmd_unpark(a, program, settings):
    from ship import state as st
    from ship.run import stop_name

    try:
        with st.locked(program) as state:
            if a.slice not in state.slices:
                raise st.StateError(f"no slice {a.slice}")
            checkpoint = state.slices[a.slice].checkpoint
            review = program.stop_review(stop_name(program, checkpoint))
            if review.is_dir() and any(review.iterdir()):
                raise st.StateError(f"{a.slice}: the review of stop {review.name} has started; "
                                    "his answer goes to the review or the backlog now")
            freed = state.unpark(a.slice, a.why)
    except st.StateError as exc:
        print(f"REFUSED {exc}")
        return 1
    note = program.stop_note(stop_name(program, checkpoint))
    removed = note.exists()
    note.unlink(missing_ok=True)  # the stop is no longer built
    print(json.dumps({"unparked": a.slice, "freed": freed, "stop_note_removed": removed}))
    return 0


# U08: arm checks
def cmd_facts(a, program, settings):
    from ship.facts import facts_at

    only = [s.strip() for s in a.slices.split(",") if s.strip()] if a.slices else None
    return _lines(*facts_at(program, a.tip, settings, only))


# U09: trace and the checkpoint review
def cmd_trace(a, program, settings):
    from ship.stop_trace import TraceError, trace

    try:
        return _lines(*trace(program, a.stop, settings))
    except TraceError as exc:
        print(f"REFUSED {exc}")
        return 1


def cmd_review(a, program, settings):
    from ship.review import review

    return review(program, a.stop, settings, a.round)


# U10: merge as a script
def cmd_merge(a, program, settings):
    from ship.merge import merge

    rc, lines = merge(program, a.stop, settings)
    for line in lines:
        print(line)
    return rc


# U38: claims, the merge queue and the worker pool
def cmd_claims(a, program, settings):
    from ship import claims as cl
    from ship import program as prog

    claims = cl.for_program(program, settings)
    if not claims.active:
        print(f"NOCLAIMS no {claims.records.claims}: the program folder is not in a plans worktree")
        return 0
    name = program.dir.name
    if a.action == "claim":
        found = claims.claim(name, cl.slice_files(program))
        lines = [f"CLAIM {r.program} {r.pattern}" for r in claims.live() if r.program == name and r.kind == "claim"]
        lines += [f"blocked-by claim {other}: {mine} ~ {theirs}" for mine, other, theirs in found]
    elif a.action == "notice":
        area = [str(x) for x in prog.load(program).area] if program.project_file.exists() else []
        claims.notice(name, area)
        lines = [f"NOTICE {name} {x}" for x in area]
    elif a.action == "release":
        lines = [f"RELEASED {claims.release(name)} patterns of {name}"]
    elif a.action == "sweep":
        lines = claims.sweep() or ["SWEPT nothing"]
    else:
        lines = [f"{r.program}\t{r.kind}\t{r.pattern}\t{r.since}" for r in claims.live()] or ["NONE live"]
    lines += claims.lines
    return _lines(True, lines)


# U11: chain, the conveyor
def cmd_chain(a):
    from ship import chain, scheduled_task

    if a.install_task or a.remove_task:
        if a.install_task:
            if not a.plans:
                raise SystemExit("ship chain --install-task needs --plans")
            rc, lines = scheduled_task.install(a.plans.resolve(), _settings_for(a), apply=a.install)
        else:
            rc, lines = scheduled_task.remove(_settings_for(a), apply=a.install)
        _lines(True, lines)
        return rc
    if a.resume_all:
        if not a.plans:
            raise SystemExit("ship chain --resume-all needs --plans")
        return _lines(True, chain.resume_all(a.plans.resolve()) or ["NOTHING to resume"])
    where = a.follow if isinstance(a.follow, Path) else a.program
    if not where:
        raise SystemExit("ship chain needs --program (or --follow P, --resume-all --plans P)")
    program = Program(where.resolve())
    settings = load_settings(program.dir)
    if a.follow is not None:
        return chain.follow(program, settings, settings.chain_poll_s)
    if a.stop_after:
        (program.dir / "STOP-AFTER").write_text(a.stop_after + "\n", "utf-8", newline="\n")
        print(f"STOP-AFTER {a.stop_after}: the conveyor stops once that stop is merged")
        return 0
    if a.detach:
        return chain.detach(["chain", "--program", str(program.dir)], program.dir)
    return chain.conveyor(program, settings)


def _settings_for(a):
    from ship.settings import Settings

    return load_settings(a.program.resolve()) if a.program else Settings()


def cmd_abandon(a, program, settings):
    from ship.chain import abandon

    return _lines(True, abandon(program, settings, a.why))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ship")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, fn, *args):
        s = sub.add_parser(name)
        s.add_argument("--program", required=True, type=Path)
        for arg in args:
            s.add_argument(*arg[0], **arg[1])
        s.set_defaults(fn=fn)
        return s

    def add_plain(name, fn, *args):
        """A command that takes no --program; `fn(a)` gets the parsed arguments only."""
        s = sub.add_parser(name)
        for arg in args:
            s.add_argument(*arg[0], **arg[1])
        s.set_defaults(fn=fn, plain=True)
        return s

    add("init", cmd_init, (["--repo"], {"required": True}), (["--build-branch"], {"required": True}),
        (["--worktree-root"], {"required": True}), (["--remote"], {"default": "origin"}))
    add("dispatch", cmd_dispatch, (["slice"], {}))
    add("verify_ready", cmd_verify_ready, (["slice"], {}), (["sha"], {}))
    add("slice_checks", cmd_slice_checks, (["slice"], {}))
    add("timed", cmd_timed, (["--slice"], {"required": True}), (["--log"], {"required": True}),
        (["--timeout"], {"type": float}), (["argv"], {"nargs": argparse.REMAINDER}))
    add("land", cmd_land, (["slices"], {"nargs": "*"}))
    add("nightly", cmd_nightly, (["--no-wait"], {"action": "store_true"}))
    add("ci", cmd_ci, (["action"], {"choices": ["start", "status", "gate", "read", "summary"]}),
        (["run_id"], {"nargs": "?"}), (["--level"], {"default": "deep"}),
        (["--fresh"], {"action": "store_true"}), (["--wait"], {"action": "store_true"}), (["--pr"], {}),
        (["--sha"], {}))
    add("bisect-step", cmd_bisect_step, (["--ids"], {"required": True}))
    add("power_watch", cmd_power_watch, (["--once"], {"action": "store_true"}))
    add("power", cmd_power)
    add("merged", cmd_merged, (["checkpoint"], {}))
    add("quality", cmd_quality, (["--from"], {"required": True, "dest": "base"}),
        (["--tools"], {"default": "vulture,skylos,mutmut"}))
    add("baseline", cmd_baseline, (["--at"], {}), (["--tools"], {}), (["--part"], {}))
    add("recover", cmd_recover, (["--usage-reset"], {}))
    add("run_report", cmd_run_report)
    add("preflight", cmd_preflight, (["--protection-push-test"], {"action": "store_true"}))
    add("teardown", cmd_teardown)
    add("main-check", cmd_main_check)
    add("status", cmd_status)
    add("park", cmd_park, (["slice"], {}), (["--cause"], {"choices": ["manual", "dispute"], "required": True}),
        (["--why"], {"required": True}))
    add("hook", cmd_hook)
    # U03: plans worktree and records
    add_plain("records", cmd_records, (["action"], {"choices": ["init", "commit", "prefix"]}),
              (["prefix"], {"nargs": "?"}), (["--plans"], {"required": True, "type": Path}), (["--repo"], {}),
              (["--remote"], {"default": "origin"}), (["-m", "--message"], {}))
    # U04: index v2 parser and ship phase
    add_plain("phase", cmd_phase, (["--program"], {"type": Path}), (["--all"], {"action": "store_true"}),
              (["--plans"], {"type": Path}), (["--set"], {}), (["--status"], {"choices": ["running", "done", "waits"]}),
              (["--by"], {}), (["--words"], {"action": "store_true"}))
    add("gate", cmd_gate, (["name"], {}), (["--by"], {"required": True}), (["--source"], {"required": True}),
        (["--advance"], {"action": "store_true"}))
    # U06: headless launcher and spike
    add("spike", cmd_spike, (["--parent"], {"action": "store_true"}), (["--child"], {"action": "store_true"}),
        (["--recheck"], {"action": "store_true"}))
    # U07: ship run, the build loop
    add("run", cmd_run, (["--once"], {"action": "store_true"}))
    add("unpark", cmd_unpark, (["slice"], {}), (["--why"], {"required": True}))
    # U08: arm checks
    add("facts", cmd_facts, (["--tip"], {"required": True}), (["--slices"], {}))
    # U09: trace and the checkpoint review
    add("trace", cmd_trace, (["--stop"], {"required": True}))
    add("review", cmd_review, (["stop"], {}), (["--round"], {"type": int, "choices": [1, 2]}))
    # U10: merge as a script
    add("merge", cmd_merge, (["stop"], {}))
    # U38: claims, the merge queue and the worker pool
    add("claims", cmd_claims, (["action"], {"choices": ["claim", "notice", "release", "sweep", "list"]}))
    # U11: chain, the conveyor
    add_plain("chain", cmd_chain, (["--program"], {"type": Path}), (["--detach"], {"action": "store_true"}),
              (["--follow"], {"nargs": "?", "const": True, "type": Path}), (["--resume-all"], {"action": "store_true"}),
              (["--plans"], {"type": Path}), (["--stop-after"], {}), (["--install-task"], {"action": "store_true"}),
              (["--remove-task"], {"action": "store_true"}), (["--install"], {"action": "store_true"}))
    add("abandon", cmd_abandon, (["--why"], {"required": True}))
    return p


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    if getattr(a, "plain", False):
        return a.fn(a)
    if a.fn is cmd_hook:  # a bad ship.toml or program path must refuse, never fall through to allow
        try:
            program = Program(a.program.resolve())
            return cmd_hook(a, program, load_settings(program.dir))
        except BaseException as exc:  # noqa: BLE001
            print(f"ship hook: refusing, the guard itself failed: {exc!r}", file=sys.stderr)
            return 2
    program = Program(a.program.resolve())
    return a.fn(a, program, load_settings(program.dir))


if __name__ == "__main__":
    raise SystemExit(main())
