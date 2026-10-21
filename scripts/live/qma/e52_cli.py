"""E52 lane: the `cli` target of `delegate` v2, live.

    e52_cli.py    records which agent CLIs on this machine take an Anthropic base URL and token
                  from their environment, then proves two things on the fake provider, so no
                  credit is spent:

                  1. a `cli` helper runs the pinned Claude Code CLI as an ordinary local process;
                     its model calls reach the relay and appear in the router journal under the
                     grant whose owner is the helper's handle.
                  2. a `cli` helper whose process never answers is ended by `delegate_stop`, its
                     process is gone, and its stored answer says stopped.

Runs on a throwaway home and the fake model, so it needs no lane lock. Logs go to
`<QMA_EVIDENCE_DIR>/owner-dlg-e52.log`.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Final

import psutil
from common import (
    Log,
    boot,
    capture_grants,
    fake_row,
    put_providers,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)

TURN_S: Final = 180.0
COMPLETION_S: Final = 120.0
CANDIDATES: Final = ("claude", "opencode", "kimi", "qwen", "codex")
"""Agent CLIs this lane looks for on PATH and records, by name, whether it found one."""


def known_clis(log: Log) -> dict[str, str]:
    """Which CLIs are installed, and what this lane proves about each. The pinned Claude Code CLI
    is the one QMX ships, so it is the one this lane proves; another binary installed here is
    recorded as seen but not probed, and its answer is not claimed."""
    found: dict[str, str] = {}
    for name in CANDIDATES:
        path = shutil.which(name)
        if path is None:
            found[name] = "not installed"
        elif name == "claude":
            found[name] = f"installed at {path}; proven below through the pinned launcher"
        else:
            found[name] = f"installed at {path}; seen, not probed by this lane"
        log(f"cli {name}: {found[name]}")
    return found


async def lane(log: Log) -> None:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415

    from qma.harness import (  # noqa: PLC0415
        Background,
        Harness,
        InjectedText,
        NewChat,
        QmxHome,
        TestMode,
    )
    from qma.harness.routes import control_service  # noqa: PLC0415

    clis = known_clis(log)
    root = throwaway_home("dlg-e52")
    fake = FakeModel([Turn([text("CLI-HELPER-OK")]), Turn([text("CLI-HELPER-OK again")])]).start()
    put_providers(root, {"fake": fake_row(fake.url), "delegate_targets": ["fake"]})
    home = QmxHome(root)
    control = control_service(home)
    minted = capture_grants()
    harness = await Harness.open(home, control=control, test=TestMode(loopback_http_provider=True))
    handles: list[str] = []
    try:
        parent = await harness.start_chat(
            NewChat(
                title="e52 parent",
                model="opus",
                profile="fake",
                mode="bypassPermissions",
                workspace=_folder(home.root, "e52"),
                kind=Background(),
            )
        )
        await harness.run_turn(parent, InjectedText("start a cli helper"))
        ask = json.dumps(
            {
                "task": "Reply with the single word OK and nothing else.",
                "profile": "fake",
                "target": "cli",
            }
        )
        refused = "it did not ask"
        try:
            await harness._delegate(parent, "delegate_run", ask)  # pyright: ignore[reportPrivateUsage]
        except Exception as error:
            refused = str(error)
        log.check(
            "the first spawn of the pinned CLI's version asks before it runs",
            "allow_cli=true" in refused,
            refused[:160],
        )
        reply = json.loads(
            await harness._delegate(  # pyright: ignore[reportPrivateUsage]
                parent,
                "delegate_run",
                json.dumps({**json.loads(ask), "allow_cli": True}),
            )
        )
        handle = str(reply["handle"])
        handles.append(handle)
        log(f"cli helper {handle}: resolved to {reply['resolved']}")
        stored = await _wait(control, parent, 1)
        for row in stored:
            log(f"completion {row['handle']}: state={row['state']} {str(row['summary'])[:160]!r}")
        log.check(
            "the cli helper ran the pinned CLI and answered through the relay",
            bool(stored)
            and stored[0]["state"] == "done"
            and "CLI-HELPER-OK" in str(stored[0]["summary"]),
            str(stored[0]["summary"])[:120] if stored else None,
        )
        child = _child_of(control, parent, home)
        calls = _model_calls(home, child)
        for row in calls:
            model, path, status = row.get("model"), row.get("path"), row.get("status")
            log(f"  journal: model={model} path={path} status={status}")
        mine = [
            grant
            for grant in minted
            if getattr(grant, "agent_id", "") == handle or str(grant.session_id) == child
        ]
        log(
            "grants minted for the helper: "
            + json.dumps([(g.session_id[:8], g.agent_id) for g in mine])
        )
        log.check(
            "its model calls appear in the router journal under its grant",
            bool(calls)
            and any(str(grant.session_id) == child for grant in mine)
            and any(getattr(grant, "agent_id", "") == handle for grant in mine),
            {"journal": child[:8], "grants": [(g.session_id[:8], g.agent_id) for g in mine]},
        )
        log.check(
            "the CLI a cli helper runs takes a base URL and token from its environment",
            bool(calls) and bool(clis.get("claude")),
            {"journal rows": len(calls), "claude": clis.get("claude")},
        )
        control.settings_put(
            "agents",
            {"cli_helper": [sys.executable, "-c", "import time; time.sleep(120)"]},  # pyright: ignore[reportArgumentType]
        )
        argument = json.dumps({"task": "sleep", "profile": "fake", "target": "cli"})
        refused: dict[str, Any] = {}
        try:
            await harness._delegate(parent, "delegate_run", argument)  # pyright: ignore[reportPrivateUsage]
        except Exception as error:
            refused = {"message": str(error)}
        log(f"the first spawn of the new binary version asks: {str(refused)[:160]}")
        reply = json.loads(
            await harness._delegate(  # pyright: ignore[reportPrivateUsage]
                parent,
                "delegate_run",
                json.dumps(
                    {"task": "sleep", "profile": "fake", "target": "cli", "allow_cli": True}
                ),
            )
        )
        sleeping = str(reply["handle"])
        handles.append(sleeping)
        await _wait(control, parent, 2, seconds=30)
        process = _process_of(harness, sleeping)
        log(f"the sleeping cli helper {sleeping} runs as pid {process}")
        stopped = json.loads(
            await harness._delegate(  # pyright: ignore[reportPrivateUsage]
                parent,
                "delegate_stop",
                json.dumps({"handle": sleeping, "reason": "the lane ends it"}),
            )
        )
        log(f"delegate_stop: {stopped}")
        await asyncio.sleep(3)
        log.check(
            "a cli helper dies with its handle",
            process is not None and not psutil.pid_exists(process),
            process,
        )
        rows = _rows(control, parent)
        mine = [row for row in rows if row["handle"] == sleeping]
        log.check(
            "its stored answer says stopped",
            bool(mine) and mine[0]["state"] == "stopped",
            [(row["handle"], row["state"]) for row in rows],
        )
    finally:
        await harness.close()
        fake.stop()


def _folder(root: Path, name: str) -> Path:
    found = root / "workspaces" / name
    found.mkdir(parents=True, exist_ok=True)
    return found


def _rows(control: Any, parent: str) -> list[dict[str, Any]]:
    return list(control.delegate_completions_all(parent))


async def _wait(
    control: Any, parent: str, wanted: int, seconds: float = COMPLETION_S
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = _rows(control, parent)
        if len(found) >= wanted:
            return found
        await asyncio.sleep(0.5)
    return _rows(control, parent)


def _child_of(control: Any, parent: str, home: Any) -> str:
    """The helper chat that reached the model: the first child of the parent whose run journal
    holds a model call, else the first child. A refused first spawn leaves a child chat too."""
    children = [
        str(row["id"]) for row in control.sessions_list(0, 100) if row.get("parent_id") == parent
    ]
    for child in children:
        if _model_calls(home, child):
            return child
    return children[0]


def _model_calls(home: Any, child: str) -> list[dict[str, Any]]:
    path = home.root / "runs" / child / "journal.jsonl"
    if not path.is_file():
        return []
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    return [
        {"event": row.get("event"), **row.get("payload", {})}
        for row in rows
        if row.get("event") == "model_call"
    ]


def _process_of(harness: Any, handle: str) -> int | None:
    helper = harness._helpers._by_handle.get(handle)  # pyright: ignore[reportPrivateUsage]
    process = None if helper is None else helper.process
    return None if process is None else process.pid


def main() -> int:
    log = Log("owner-dlg-e52")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(lane(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
