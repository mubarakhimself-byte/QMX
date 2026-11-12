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
    from ship.verify_ready import verify_ready

    return _lines(*verify_ready(program, a.slice, a.sha, settings))


def cmd_slice_checks(a, program, settings):
    from ship.slice_checks import slice_checks

    return _lines(*slice_checks(program, a.slice, settings))


def cmd_timed(a, program, settings):
    from ship.wrapper import run_timed

    argv = a.argv[1:] if a.argv[:1] == ["--"] else a.argv
    result = run_timed(argv, Path.cwd(), Path(a.log), a.timeout or settings.check_timeout_s, settings,
                       program.tmp, program.heartbeat(a.slice))
    print(f"EXIT rc={result.rc} seconds={result.seconds:.0f}" + (" timeout" if result.timed_out else ""))
    return result.rc


def cmd_land(a, program, settings):
    from ship.land import land

    return _lines(*land(program, a.slices or None, settings))


def cmd_nightly(a, program, settings):
    from ship.nightly import nightly

    return _lines(*nightly(program, settings))


def cmd_bisect_step(a, program, settings):
    from ship.nightly import bisect_step

    return bisect_step(program, Path.cwd(), Path(a.ids), settings)


def cmd_power_watch(a, program, settings):
    from ship.power_watch import watch

    return watch(program, settings, once=a.once)


def cmd_recover(a, program, settings):
    from ship.recover import recover

    return _lines(True, recover(program, settings, a.usage_reset))


def cmd_run_report(a, program, settings):
    from ship.run_report import write_report

    ok, path = write_report(program)
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
    from ship.hook import main as hook_main

    return hook_main(program, sys.stdin.read())


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

    add("init", cmd_init, (["--repo"], {"required": True}), (["--build-branch"], {"required": True}),
        (["--worktree-root"], {"required": True}), (["--remote"], {"default": "origin"}))
    add("dispatch", cmd_dispatch, (["slice"], {}))
    add("verify_ready", cmd_verify_ready, (["slice"], {}), (["sha"], {}))
    add("slice_checks", cmd_slice_checks, (["slice"], {}))
    add("timed", cmd_timed, (["--slice"], {"required": True}), (["--log"], {"required": True}),
        (["--timeout"], {"type": float}), (["argv"], {"nargs": argparse.REMAINDER}))
    add("land", cmd_land, (["slices"], {"nargs": "*"}))
    add("nightly", cmd_nightly)
    add("bisect-step", cmd_bisect_step, (["--ids"], {"required": True}))
    add("power_watch", cmd_power_watch, (["--once"], {"action": "store_true"}))
    add("recover", cmd_recover, (["--usage-reset"], {}))
    add("run_report", cmd_run_report)
    add("preflight", cmd_preflight, (["--protection-push-test"], {"action": "store_true"}))
    add("teardown", cmd_teardown)
    add("main-check", cmd_main_check)
    add("status", cmd_status)
    add("park", cmd_park, (["slice"], {}), (["--cause"], {"choices": ["manual", "dispute"], "required": True}),
        (["--why"], {"required": True}))
    add("hook", cmd_hook)
    return p


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    program = Program(a.program.resolve())
    return a.fn(a, program, load_settings(program.dir))


if __name__ == "__main__":
    raise SystemExit(main())
