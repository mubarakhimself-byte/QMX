from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import Launch, wait_for

from qma.harness.procs import AgentProcessCap
from qma.launcher import process_started

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="the job cap is Windows only")


@pytest.fixture
def cap(procs_dir: Path) -> Iterator[AgentProcessCap]:
    holder = AgentProcessCap.for_platform(procs_dir, None)
    yield holder
    holder.close()


def write_record(procs_dir: Path, chat: str, started: str | None) -> None:
    record = {"launcher_pid": os.getpid(), "cli_pid": os.getpid(), "cli_started": started}
    (procs_dir / f"{chat}.json").write_text(json.dumps(record), encoding="utf-8")


def test_a_reused_pid_with_a_new_start_time_reads_as_dead(
    cap: AgentProcessCap, procs_dir: Path
) -> None:
    write_record(procs_dir, "mine", process_started(os.getpid()))
    write_record(procs_dir, "reused", "1")
    assert cap.alive("mine")
    assert not cap.alive("reused")
    assert not cap.alive("never-started")
    assert cap.report().chats == ("mine",)


def test_kill_orphans_kills_a_live_tree_and_names_its_chat(launch: Launch, procs_dir: Path) -> None:
    orphan = launch("orphan")
    assert wait_for((procs_dir / "orphan.json").exists)
    write_record(procs_dir, "stale", "1")
    holder = AgentProcessCap.for_platform(procs_dir, None)
    try:
        assert holder.kill_orphans() == ("orphan",)
        orphan.communicate(timeout=30)
        assert not holder.alive("orphan")
        assert list(procs_dir.glob("*.json")) == []
        assert holder.kill_orphans() == ()
    finally:
        holder.close()


@windows_only
def test_the_memory_limit_kills_only_the_chat_that_crossed_it(
    cap: AgentProcessCap, launch: Launch, procs_dir: Path
) -> None:
    chats = {name: launch(name, cap=cap.handle_name) for name in ("calm-1", "heavy", "calm-2")}
    try:
        assert wait_for(lambda: len(cap.report().chats) == 3)
        used = cap.report().used_mb
        assert used is not None
        cap.set_limit(used + 300)
        assert chats["heavy"].stdin is not None
        chats["heavy"].stdin.write("heavy\n")
        chats["heavy"].stdin.flush()
        assert wait_for(lambda: not cap.alive("heavy"))
        report = cap.report()
        assert report.last_killed == "heavy"
        assert report.chats == ("calm-1", "calm-2")
        for name in ("calm-1", "calm-2"):
            out, _ = chats[name].communicate("ping\n", timeout=30)
            assert out.strip() == "pong"
            assert chats[name].returncode == 0
    finally:
        for chat in chats.values():
            if chat.poll() is None:
                chat.kill()


@windows_only
def test_closing_the_cap_kills_every_member_tree(launch: Launch, procs_dir: Path) -> None:
    holder = AgentProcessCap.for_platform(procs_dir, None)
    member = launch("member", cap=holder.handle_name)
    assert wait_for(lambda: holder.alive("member"))
    holder.close()
    holder.close()
    member.communicate(timeout=30)
    assert member.returncode != 0
    assert not holder.alive("member")


def test_stop_chat_is_idempotent(cap: AgentProcessCap, launch: Launch, procs_dir: Path) -> None:
    chat = launch("stopped", cap=cap.handle_name)
    assert wait_for(lambda: cap.alive("stopped"))
    cap.stop_chat("stopped")
    cap.stop_chat("stopped")
    chat.communicate(timeout=30)
    assert chat.returncode != 0
    assert not cap.alive("stopped")
