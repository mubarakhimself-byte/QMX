"""UI factory CLI. Machine-readable JSON on stdout unless --text."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ui_factory.ci_wait import watch_sha
from ui_factory.config import load_config
from ui_factory.doctor import run_doctor, write_restart_safe_report
from ui_factory.evidence import sha256_text
from ui_factory.install import install_user_copy
from ui_factory.merge_gate import MergeBlocked, run_merge_gate
from ui_factory.paths import state_dir
from ui_factory.ports import PortAllocator
from ui_factory.quality import applicable_profiles, run_profiles
from ui_factory.schedule import build_model_for_weight, plan_epics
from ui_factory.state import FactoryState, StateStore
from ui_factory.story_parse import discover_epic_files, parse_epic_markdown
from ui_factory.validate_inputs import validate_inputs


def _dump(payload: dict[str, Any], *, text: bool) -> int:
    if text:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0 if payload.get("ok", True) else 1


def cmd_setup(args: argparse.Namespace) -> int:
    config = load_config()
    config.state_dir.mkdir(parents=True, exist_ok=True)
    store = StateStore(config.state_dir)
    state = store.load()
    if state.destination_branch == "":
        state = FactoryState(
            destination_branch=config.destination_branch,
            base_sha=_head_sha(config.repo_root),
            waiting_for_input=True,
            waiting_reason="No UI stories supplied yet.",
        )
        store.save(state)
    installed = {}
    if not args.skip_install:
        installed = install_user_copy()
    mcp = {
        "context7": True,
        "reticle": True,
        "shadcn-svelte-cli": False,
    }
    report = run_doctor(config, mcp=mcp)
    write_restart_safe_report(config.state_dir / "doctor.json", report)
    return _dump(
        {
            "ok": report.ready,
            "command": "setup",
            "destination_branch": config.destination_branch,
            "base_sha": state.base_sha,
            "installed": installed,
            "doctor": report.to_dict(),
        },
        text=args.text,
    )


def cmd_doctor(args: argparse.Namespace) -> int:
    config = load_config()
    mcp = {
        "context7": not args.assume_mcp_down,
        "reticle": not args.assume_mcp_down,
    }
    report = run_doctor(config, mcp=mcp)
    write_restart_safe_report(config.state_dir / "doctor.json", report)
    return _dump({"ok": report.ready, "doctor": report.to_dict()}, text=args.text)


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_config()
    selected = set(args.ids.split(",")) if args.ids else None
    report = validate_inputs(config, selected=selected)
    ok = report.status in {"ready", "partial", "waiting_for_input"}
    return _dump(
        {"ok": ok, "validate": report.to_dict(), "generate_stories": False},
        text=args.text,
    )


def cmd_dry_run(args: argparse.Namespace) -> int:
    config = load_config()
    report = validate_inputs(config)
    epics = []
    for path in discover_epic_files(config.repo_root, config.epic_globs):
        epics.extend(parse_epic_markdown(path))
    selected = set(args.ids.split(",")) if args.ids else None
    planned = plan_epics(epics, selected=selected, max_parallel=config.max_parallel_epics)
    payload = {
        "ok": True,
        "destination_branch": config.destination_branch,
        "validate": report.to_dict(),
        "plan": [
            {
                "epic": p.epic_id,
                "title": p.title,
                "weight": p.weight,
                "build_model": build_model_for_weight(p.weight),
                "stories": list(p.stories),
                "disjoint": p.disjoint,
            }
            for p in planned
        ],
        "would_launch": False,
        "reason": "dry-run",
    }
    if report.status == "waiting_for_input":
        payload["would_launch"] = False
        payload["reason"] = "waiting for BMAD stories"
    return _dump(payload, text=args.text)


def cmd_status(args: argparse.Namespace) -> int:
    config = load_config()
    store = StateStore(config.state_dir)
    state = store.load()
    return _dump({"ok": True, "state": state.to_dict()}, text=args.text)


def cmd_resume(args: argparse.Namespace) -> int:
    config = load_config()
    store = StateStore(config.state_dir)
    state = store.load()
    skip_rebuild: list[str] = []
    for unit in state.units.values():
        if unit.head_sha and unit.status in {"verifying", "candidate", "merged"}:
            skip_rebuild.append(unit.unit_id)
    return _dump(
        {
            "ok": True,
            "command": "resume",
            "skip_rebuild": skip_rebuild,
            "state": state.to_dict(),
        },
        text=args.text,
    )


def cmd_quality(args: argparse.Namespace) -> int:
    config = load_config()
    worktree = Path(args.worktree)
    names = args.profiles.split(",") if args.profiles else applicable_profiles(
        worktree,
        args.files.split(",") if args.files else [],
        user_facing=args.user_facing,
        needs_backend=args.needs_backend,
    )
    record, ok, reason = run_profiles(
        config=config,
        worktree=worktree,
        unit_id=args.unit_id,
        story_hash=args.story_hash or sha256_text(args.unit_id),
        candidate_sha=args.sha or "UNKNOWN",
        profile_names=names,
        user_facing=args.user_facing,
        evidence_dir=Path(args.evidence_dir or (state_dir() / "evidence")),
    )
    return _dump(
        {
            "ok": ok,
            "reason": reason,
            "evidence": record.to_dict(),
        },
        text=args.text,
    )


def cmd_merge_gate(args: argparse.Namespace) -> int:
    config = load_config()
    blocking = [x for x in (args.blocking or "").split(",") if x]
    try:
        result = run_merge_gate(
            config=config,
            worktree=Path(args.worktree),
            branch=args.branch,
            unit_id=args.unit_id,
            story_hash=args.story_hash or "",
            changed_files=args.files.split(",") if args.files else [],
            user_facing=args.user_facing,
            needs_backend=args.needs_backend,
            evidence_dir=Path(args.evidence_dir or (state_dir() / "evidence")),
            review_blocking=blocking,
            push=args.push,
        )
    except MergeBlocked as exc:
        return _dump({"ok": False, "merged": False, "reason": exc.reason}, text=args.text)
    return _dump(
        {
            "ok": result.merged,
            "merged": result.merged,
            "destination": result.destination,
            "branch": result.branch,
            "sha": result.sha,
            "reason": result.reason,
        },
        text=args.text,
    )


def cmd_ports(args: argparse.Namespace) -> int:
    alloc = PortAllocator(state_dir())
    if args.release:
        alloc.release(args.unit_id)
        return _dump({"ok": True, "released": args.unit_id}, text=args.text)
    lease = alloc.acquire(args.unit_id)
    return _dump({"ok": True, "lease": lease.to_dict()}, text=args.text)


def cmd_ci_wait(args: argparse.Namespace) -> int:
    watch = watch_sha(
        args.sha,
        branch=args.branch,
        timeout_seconds=args.timeout,
        simulate_conclusion=args.simulate,
    )
    ok = watch.conclusion == "success"
    return _dump(
        {
            "ok": ok,
            "ci": {
                "available": watch.available,
                "sha": watch.sha,
                "conclusion": watch.conclusion,
                "detail": watch.detail,
                "simulated": watch.simulated,
            },
        },
        text=args.text,
    )


def cmd_run_selected(args: argparse.Namespace) -> int:
    config = load_config()
    report = validate_inputs(config)
    if report.status == "waiting_for_input":
        store = StateStore(config.state_dir)
        state = store.load()
        state.waiting_for_input = True
        state.waiting_reason = "; ".join(report.waiting)
        store.save(state)
        return _dump(
            {
                "ok": True,
                "launched": False,
                "waiting_for_input": True,
                "generate_stories": False,
                "validate": report.to_dict(),
            },
            text=args.text,
        )
    return _dump(
        {
            "ok": True,
            "launched": False,
            "message": (
                "Stories present. Launch is owned by /run-ui-epics in a Grok "
                "session (workflow ui-epic-build). CLI will not spawn nested "
                "factory loops."
            ),
            "validate": report.to_dict(),
        },
        text=args.text,
    )


def _head_sha(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ui_factory")
    parser.add_argument("--text", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup")
    setup.add_argument("--skip-install", action="store_true")
    setup.set_defaults(func=cmd_setup)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--assume-mcp-down", action="store_true")
    doctor.set_defaults(func=cmd_doctor)
    validate = sub.add_parser("validate-inputs")
    validate.add_argument("--ids", default="")
    validate.set_defaults(func=cmd_validate)
    dry = sub.add_parser("dry-run")
    dry.add_argument("--ids", default="")
    dry.set_defaults(func=cmd_dry_run)
    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)
    resume = sub.add_parser("resume")
    resume.set_defaults(func=cmd_resume)
    quality = sub.add_parser("quality")
    quality.add_argument("--worktree", required=True)
    quality.add_argument("--unit-id", required=True)
    quality.add_argument("--story-hash", default="")
    quality.add_argument("--sha", default="")
    quality.add_argument("--profiles", default="")
    quality.add_argument("--files", default="")
    quality.add_argument("--evidence-dir", default="")
    quality.add_argument("--user-facing", action="store_true")
    quality.add_argument("--needs-backend", action="store_true")
    quality.set_defaults(func=cmd_quality)
    merge = sub.add_parser("merge-gate")
    merge.add_argument("--worktree", required=True)
    merge.add_argument("--branch", required=True)
    merge.add_argument("--unit-id", required=True)
    merge.add_argument("--story-hash", default="")
    merge.add_argument("--files", default="")
    merge.add_argument("--evidence-dir", default="")
    merge.add_argument("--blocking", default="")
    merge.add_argument("--user-facing", action="store_true")
    merge.add_argument("--needs-backend", action="store_true")
    merge.add_argument("--push", action="store_true")
    merge.set_defaults(func=cmd_merge_gate)
    ports = sub.add_parser("ports")
    ports.add_argument("--unit-id", required=True)
    ports.add_argument("--release", action="store_true")
    ports.set_defaults(func=cmd_ports)
    ci = sub.add_parser("ci-wait")
    ci.add_argument("--sha", required=True)
    ci.add_argument("--branch", default="ui-integration")
    ci.add_argument("--timeout", type=int, default=60)
    ci.add_argument("--simulate", default=None)
    ci.set_defaults(func=cmd_ci_wait)
    runsel = sub.add_parser("run-selected")
    runsel.add_argument("--ids", default="")
    runsel.set_defaults(func=cmd_run_selected)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
