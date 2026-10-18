from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import cast

import pytest
import qma.boot
from flows import edge, folder, node, run_folder

from qmx_engine.nodes.script import BANNED_FRAGMENTS, script_env

START = node("start", "trigger")

PRINT_ENV = """
    import json, os
    print(json.dumps(dict(os.environ)))
"""


def test_the_banned_fragments_are_qma_boots() -> None:
    assert BANNED_FRAGMENTS == qma.boot.BANNED_FRAGMENTS


@pytest.mark.skipif(sys.platform != "win32", reason="Windows path spellings")
def test_the_plan_path_is_dropped_in_every_spelling() -> None:
    plan = "D:\\QMX\\home\\claude"
    environ = {
        "HOME": "D:/QMX/home/claude",
        "TEMP": "D:\\\\QMX\\\\home\\\\claude\\\\tmp",
        "TMP": "d:\\qmx\\HOME\\claude\\",
        "PATH": "C:\\Windows;D:/QMX/home/claude/bin",
        "USERPROFILE": "D:\\QMX\\home",
        "LANG": "en_GB",
    }

    assert script_env(environ, [plan]) == {"USERPROFILE": "D:\\QMX\\home", "LANG": "en_GB"}
    assert script_env({"HOME": plan}, ["D:/QMX/home/claude"]) == {}


def test_a_script_sees_no_key_no_claude_name_and_no_plan_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    plan = str(home.resolve() / "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-canary")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", plan)
    monkeypatch.setenv("OPENROUTER_REF", "qmx/openrouter")
    monkeypatch.setenv("HOME", plan)
    root = folder(
        tmp_path / "wf",
        [START, node("env", "script", script="scripts/env.py")],
        {"start": {"main": [edge("env")]}},
        {"env": PRINT_ENV},
    )

    outcome, _ = run_folder(root, home)

    env = cast(dict[str, dict[str, str]], outcome.outputs["env"])["main"]
    assert outcome.status == "passed"
    assert "PATH" in env
    names = " ".join(env).upper()
    values = " ".join(env.values())
    assert ("ANTHROPIC" in names, "CLAUDE" in names, "OPENROUTER" in names, "HOME" in env) == (
        False,
        False,
        False,
        False,
    )
    assert ("qmx/" in values, plan.lower() in values.lower()) == (False, False)


def test_a_script_past_its_timeout_is_killed_and_fails_retryable(tmp_path: Path) -> None:
    sleeper = node("sleep", "script", script="scripts/sleep.py")
    sleeper["timeout"] = {"run_seconds": 1}
    sleeper["retry"] = {"max_tries": 1}
    root = folder(
        tmp_path / "wf",
        [START, sleeper],
        {"start": {"main": [edge("sleep")]}},
        {"sleep": "import time\ntime.sleep(60)\n"},
    )
    began = time.monotonic()

    outcome, events = run_folder(root, tmp_path / "home")

    failed = next(e.data for e in events if e.kind == "node_failed")
    assert outcome.status == "failed"
    assert (failed["code"], failed["retryable"], failed["effect_state"]) == (
        "timeout",
        True,
        "unknown",
    )
    assert time.monotonic() - began < 15


def test_only_an_irreversible_script_receives_its_idempotency_key(tmp_path: Path) -> None:
    key = "import json, os\nprint(json.dumps(os.environ.get('QMX_IDEMPOTENCY_KEY')))\n"
    post = node("post", "script", script="scripts/key.py")
    post["effect"] = "irreversible_external"
    local = node("local", "script", script="scripts/key.py")
    root = folder(
        tmp_path / "wf",
        [START, post, local],
        {"start": {"main": [edge("post"), edge("local")]}},
        {"key": key},
    )

    outcome, _ = run_folder(root, tmp_path / "home")

    assert outcome.outputs == {
        "post": {"main": f"{outcome.run_id}:post:0:1"},
        "local": {"main": None},
    }
