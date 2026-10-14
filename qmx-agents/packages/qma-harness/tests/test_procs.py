from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import Launch, wait_for

from qma.harness.procs import AgentProcessCap, cli_kill
from qma.launcher import CREATE_SUSPENDED, process_started

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="the job cap is Windows only")


@pytest.fixture
def cap(procs_dir: Path) -> Iterator[AgentProcessCap]:
    holder = AgentProcessCap.for_platform(procs_dir, None)
    yield holder
    holder.close()


def hold_the_gil(seconds: float) -> None:
    switch = sys.getswitchinterval()
    sys.setswitchinterval(seconds * 5)
    try:
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            pass
    finally:
        sys.setswitchinterval(switch)


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


@windows_only
def test_the_memory_limit_names_a_cli_that_crossed_it_and_exited_before_the_watcher_read(
    cap: AgentProcessCap, launch: Launch, tmp_path: Path
) -> None:
    chats = {name: launch(name, cap=cap.handle_name) for name in ("calm-3", "self-heavy")}
    try:
        assert wait_for(lambda: all((tmp_path / f"{c}.seen.json").exists() for c in chats))
        used = cap.report().used_mb
        assert used is not None
        cap.set_limit(used + 300)
        heavy = chats["self-heavy"]
        assert heavy.stdin is not None
        heavy.stdin.write("heavy-self\n")
        heavy.stdin.flush()
        hold_the_gil(seconds=2.0)
        heavy.wait(timeout=30)
        assert wait_for(lambda: cap.report().last_killed is not None)
        assert cap.report().last_killed == "self-heavy"
        out, _ = chats["calm-3"].communicate("ping\n", timeout=30)
        assert out.strip() == "pong"
    finally:
        for chat in chats.values():
            if chat.poll() is None:
                chat.kill()


@windows_only
def test_a_second_cap_holder_for_one_home_is_refused(
    cap: AgentProcessCap, launch: Launch, procs_dir: Path
) -> None:
    with pytest.raises(OSError, match="another holder"):
        AgentProcessCap.for_platform(procs_dir, None)
    member = launch("first-holder", cap=cap.handle_name)
    assert wait_for(lambda: cap.alive("first-holder"))
    out, _ = member.communicate("ping\n", timeout=30)
    assert out.strip() == "pong"


def test_stop_chat_kills_the_clis_children(cap: AgentProcessCap, launch: Launch) -> None:
    chat = launch("parent", cap=cap.handle_name)
    assert chat.stdin is not None
    assert chat.stdout is not None
    chat.stdin.write("child\n")
    chat.stdin.flush()
    child = int(chat.stdout.readline())
    assert process_started(child) is not None
    cap.stop_chat("parent")
    chat.communicate(timeout=30)
    assert wait_for(lambda: process_started(child) is None)


def test_the_kill_takes_the_process_group_the_cli_leads() -> None:
    assert cli_kill(4242, 4242) == "killpg"
    assert cli_kill(4242, 17) == "kill"
    assert cli_kill(4242, None) == "kill"


@windows_only
def test_kill_orphans_kills_a_suspended_cli_outside_every_job(
    cap: AgentProcessCap, procs_dir: Path
) -> None:
    sleeper = [sys.executable, "-c", "import time; time.sleep(600)"]
    suspended = subprocess.Popen(sleeper, creationflags=CREATE_SUSPENDED)
    try:
        started = process_started(suspended.pid)
        record = {"launcher_pid": 1, "cli_pid": suspended.pid, "cli_started": started}
        (procs_dir / "suspended.json").write_text(json.dumps(record), encoding="utf-8")
        assert cap.kill_orphans() == ("suspended",)
        assert suspended.wait(timeout=10) != 0
    finally:
        if suspended.poll() is None:
            suspended.kill()


@windows_only
def test_two_homes_with_one_chat_id_neither_refuse_nor_kill_each_other(
    cap: AgentProcessCap, launch: Launch, tmp_path: Path
) -> None:
    other = AgentProcessCap.for_platform(tmp_path / "other-procs", None)
    try:
        mine = launch("shared", cap=cap.handle_name)
        theirs = launch("shared", cap=other.handle_name, QMA_PROC_DIR=str(other.procs_dir))
        assert wait_for(lambda: cap.alive("shared") and other.alive("shared"))
        cap.stop_chat("shared")
        mine.communicate(timeout=30)
        assert mine.returncode != 0
        out, _ = theirs.communicate("ping\n", timeout=30)
        assert out.strip() == "pong"
        assert theirs.returncode == 0
    finally:
        other.close()
