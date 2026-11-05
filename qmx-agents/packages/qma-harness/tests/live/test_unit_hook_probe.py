"""A14's probe: the core plugin's PostToolUse hook under the harness's own chat launch.

The model test opts in with `QMX_TEST_LIVE=1`; without it it skips, so the package suite never
starts a model. The command test needs no model and runs in the package suite. The chat starts
through `Harness.start_chat` on a QMX home with a plan login, so the CLI loads
`qmx-agents/plugin/` with `setting_sources=[]`, exactly as every chat does. Model turns run on
`haiku`. No API key is read and nothing is spent. The run holds the engine lane lock, because
`Harness.open` kills every CLI tree it finds for its home.

- `test_the_hook_reaches_the_model`. One chat writes a broken unit, edits a passing unit into a
  broken one, edits it back, and writes a JSON file that is not a unit. PASS when the hook's
  `additionalContext` is in the transcript after the two broken saves only, and the model repeats
  each broken save's `problem_set`, which it can only know from the hook.
- `test_the_hook_command_alone`. The shipped command run by hand, in the shell the CLI runs it
  in, on a failing unit, a passing unit, a unit whose market only a Library record could settle,
  a non-unit JSON file and a TOML file, timed. PASS when only the failing unit gets an answer and
  every run ends inside `HOOK_BUDGET_S`.
- `test_the_hook_tells_the_agent_on_a_library_only_market`. The same command on a broken and a
  clean unit on GBPUSD. PASS when the broken one is told `outside_range` and nothing else, and the
  clean one prints nothing.

From `qmx-agents/` on This PC, with the agents venv:
`QMX_TEST_LIVE=1 uv run --no-sync pytest -p no:xdist -s <this file>`, where the file is
`packages/qma-harness/tests/live/test_unit_hook_probe.py`.
The model test writes `<A14_EVIDENCE>/<A14_LOG_PREFIX>a14-<windows|linux>.log`. The command test
writes `a14-time.log` there when `A14_EVIDENCE` is set, and in its own temporary folder otherwise.
On another host set `A14_HOME` (a QMX home whose `claude/` holds a plan login), `A14_LOCK`,
`A14_EVIDENCE`, `A14_WORK` and `QMA_LIVE_SCRATCH`.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, cast

import pytest
from qmx_tools.gather import template
from qmx_tools.unit_check import checked

REPO: Final = Path(__file__).resolve().parents[5]
PLUGIN: Final = REPO / "qmx-agents" / "plugin"
HOME: Final = Path(os.environ.get("A14_HOME", "D:/QMX-worktrees/qma-ship/home"))
LOCK: Final = Path(os.environ.get("A14_LOCK", "D:/QMX-worktrees/.engine-lane-lock"))
GIVEN_EVIDENCE: Final = os.environ.get("A14_EVIDENCE")
EVIDENCE: Final = Path(GIVEN_EVIDENCE or "D:/QMX-worktrees/unit-ship/evidence/a14")
WORK: Final = Path(os.environ.get("A14_WORK", "D:/QMX-worktrees/unit-ship/homes/a14-probe"))
HOST: Final = "windows" if os.name == "nt" else "linux"
TOLD: Final = "QMX unit check of "
"""The head of every message the hook hands the model."""
HOOK_BUDGET_S: Final = 8.0
"""Test bound: connections C4 and the hook's own `timeout`."""
LOCK_WAIT_S: Final = 1800.0
TURN_S: Final = 240.0
ASK: Final = (
    " Do not check, fix or retry anything. Then reply with only the problem_set value of any QMX "
    "unit check you were told about after that tool call, or the single word NONE if you were "
    "told of none."
)


class Log:
    def __init__(self, slug: str, folder: Path = EVIDENCE) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('A14_LOG_PREFIX', '')}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.failed: list[str] = []

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        if not ok:
            self.failed.append(name)

    def verdict(self) -> None:
        self("FAIL" if self.failed else "PASS")
        assert not self.failed, self.failed


def live_qma() -> Any:
    """`scripts/live/qma/common.py`: the process scrub and the throwaway HOME every lane uses."""
    path = REPO / "scripts" / "live" / "qma" / "common.py"
    spec = importlib.util.spec_from_file_location("qma_live_common", path)
    assert spec is not None and spec.loader is not None, path
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def lane_lock(say: Log) -> Generator[None]:
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                pytest.fail(f"the lane lock {LOCK} stayed held for {LOCK_WAIT_S:.0f} s")
            say("lane lock held by another lane; retry in 20 s")
            time.sleep(20)
    say(f"lane lock {LOCK} taken")
    try:
        yield
    finally:
        LOCK.rmdir()
        say("lane lock released")


def fresh(slug: str) -> Path:
    root = WORK / slug
    if os.name == "nt":
        assert root.as_posix().startswith("D:/"), root
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def problem_set(document: object) -> str:
    return str(checked(None, document)["problem_set"])


def hook_command() -> str:
    found = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    return str(found["hooks"]["PostToolUse"][0]["hooks"][0]["command"])


def entries(lines: list[str]) -> list[dict[str, Any]]:
    return [cast("dict[str, Any]", json.loads(line)) for line in lines]


def attached(entry: dict[str, Any]) -> object:
    return cast("dict[str, Any]", entry.get("attachment") or {}).get("type")


def hook_lines(lines: list[str]) -> list[dict[str, Any]]:
    """The transcript entries that carry the hook's message, by their type and attachment type."""
    return [
        {"type": entry.get("type"), "attachment": attached(entry)}
        for entry in entries(lines)
        if TOLD in json.dumps(entry)
    ]


def reply(lines: list[str]) -> str:
    texts: list[str] = []
    for entry in entries(lines):
        if entry.get("type") == "assistant":
            content = cast("list[dict[str, Any]]", entry.get("message", {}).get("content") or [])
            texts += [str(part["text"]) for part in content if part.get("type") == "text"]
    return "\n".join(texts)


async def chat_probe(say: Log, work: Path) -> None:
    from qma.harness import Harness, NewChat, OperatorText, QmxHome, control_service
    from qma.harness.chat import transcript

    live = live_qma()
    home = QmxHome(HOME)
    hooks = (PLUGIN / "hooks" / "hooks.json").is_file()
    say(f"plugin {home.plugin_dir}; hooks.json present {hooks}")
    bash = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    say(f"python on the CLI's PATH {shutil.which('python')}; git bash {bash}")
    broken_write: dict[str, object] = {"schema": "qmx.unit/1"}
    passing = template()
    broken_edit = json.loads(json.dumps(passing))
    broken_edit["numbers"]["ema_period"]["default"] = "999"
    (work / "unit.json").write_text(json.dumps(passing, indent=2), encoding="utf-8")
    expected = {"write": problem_set(broken_write), "edit": problem_set(broken_edit)}
    verdict = checked(None, passing)["verdict"]
    say(f"passing unit verdict {verdict}; expected problem sets {expected}")
    control = control_service(home)
    harness = await Harness.open(home, control=control)
    try:
        say(f"five-hour reading from Harness.meter(): {await harness.meter()}")
        chat = await harness.start_chat(
            NewChat(
                title="a14 hook probe",
                model="haiku",
                mode="acceptEdits",
                workspace=work,
                tools=("Read", "Write", "Edit"),
                toolsets=(),
            )
        )
        say(f"chat {chat}")
        unit = (work / "unit.json").as_posix()
        turns = {
            "write": f"Use the Write tool once to create {(work / 'draft.json').as_posix()} "
            'containing exactly {"schema": "qmx.unit/1"}.',
            "edit": f"Use the Read tool on {unit}, then use the Edit tool once on it to replace "
            '"default": "100" with "default": "999".',
            "edit-back": f"Use the Edit tool once on {unit} to replace "
            '"default": "999" with "default": "100".',
            "non-unit": f"Use the Write tool once to create {(work / 'notes.json').as_posix()} "
            'containing exactly {"schema": "qmx.workflow/1", "note": "not a unit"}.',
        }
        seen: dict[str, tuple[list[dict[str, Any]], str]] = {}
        done = 0
        for name, text in turns.items():
            say(f"turn {name}: {text}")
            started = time.perf_counter()
            await harness.send(chat, OperatorText(text + ASK))
            record = await live.wait_turn(home, chat, TURN_S)
            path = transcript(home, chat)
            lines = path.read_text(encoding="utf-8").splitlines() if path else []
            fresh_lines, done = lines[done:], len(lines)
            seen[name] = (hook_lines(fresh_lines), reply(fresh_lines))
            say(
                f"  turn {record.turn if record else None} in {time.perf_counter() - started:.1f} s"
            )
            say(f"  hook entries {seen[name][0]}")
            say(f"  reply {seen[name][1]!r}")
    finally:
        await harness.close()
    for name in ("write", "edit"):
        entries, said = seen[name]
        say.check(f"{name}: the hook's message is in the transcript", bool(entries), entries)
        say.check(
            f"{name}: the model repeats the problem_set only the hook told it",
            expected[name] in said,
            said,
        )
    for name in ("edit-back", "non-unit"):
        entries, said = seen[name]
        say.check(f"{name}: the hook adds no message", not entries, entries)
        say.check(
            f"{name}: the model was told of no check", "NONE" in said and "fp1:" not in said, said
        )
    say.check(
        "the passing unit is back on disk",
        checked(None, json.loads((work / "unit.json").read_text("utf-8")))["verdict"] == "pass",
        unit,
    )


@pytest.mark.skipif(
    os.environ.get("QMX_TEST_LIVE") != "1", reason="opt-in live probe on the plan login"
)
def test_the_hook_reaches_the_model() -> None:
    say = Log(f"a14-{HOST}")
    live = live_qma()
    live.boot()
    live.use_fake_home()
    login = (HOME / "claude" / ".credentials.json").exists()
    say(f"plan login present in {HOME}: {login}")
    assert login, f"{HOME} has no plan login"
    work = fresh("chat")
    with lane_lock(say):
        asyncio.run(chat_probe(say, work))
    shutil.rmtree(WORK, ignore_errors=True)
    say.verdict()


def hook_shell() -> str | None:
    """The shell the CLI runs a hook command in. On Windows that is Git Bash, found beside git as
    the CLI finds it, since the `bash` on PATH there can be WSL's."""
    given = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if given:
        return given
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    shells = [folder / "bin" / "bash.exe" for folder in Path(git).resolve().parents] if git else []
    found = [shell for shell in shells if shell.is_file()]
    return str(found[0]) if found else None


def test_the_hook_command_alone(tmp_path: Path) -> None:
    shell = hook_shell()
    if shell is None:
        pytest.skip("the hook command runs under bash (Git Bash on Windows), and none was found")
    say = Log("a14-time", Path(GIVEN_EVIDENCE) if GIVEN_EVIDENCE else tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    passing = template()
    broken = json.loads(json.dumps(passing))
    broken["numbers"]["ema_period"]["default"] = "999"
    library_only = json.loads(json.dumps(passing))
    library_only["markets"][0]["instrument_ref"]["symbol"] = "GBPUSD"
    blind = cast("list[dict[str, Any]]", checked(None, library_only)["errors"])
    assert [problem["kind"] for problem in blind] == ["no_record"]
    files = {
        "broken.json": json.dumps(broken, indent=2),
        "unit.json": json.dumps(passing, indent=2),
        "gbpusd.json": json.dumps(library_only, indent=2),
        "notes.json": '{"schema": "qmx.workflow/1"}',
        "pyproject.toml": '[project]\nname = "x"\n',
    }
    say(f"shell {shell}; python {shutil.which('python')}")
    answers: dict[str, str] = {}
    for name, body in files.items():
        (work / name).write_text(body, encoding="utf-8")
        event = {
            "hook_event_name": "PostToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": (work / name).as_posix()},
        }
        started = time.perf_counter()
        ran = subprocess.run(
            [shell, "-c", hook_command()],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        took = time.perf_counter() - started
        answers[name] = ran.stdout.strip()
        say(f"{name}: exit {ran.returncode} in {took:.2f} s")
        say(f"  stdout {ran.stdout[:200]!r}, stderr {ran.stderr[:200]!r}")
        say.check(f"{name}: the command exits 0", ran.returncode == 0, ran.returncode)
        say.check(
            f"{name}: the command ends inside {HOOK_BUDGET_S:.0f} s",
            took < HOOK_BUDGET_S,
            f"{took:.2f} s",
        )
    told = json.loads(answers["broken.json"])["hookSpecificOutput"]
    say.check(
        "broken.json: the answer is PostToolUse additionalContext with the problem set",
        told["hookEventName"] == "PostToolUse"
        and told["additionalContext"].startswith(f"{TOLD}broken.json failed.")
        and problem_set(broken) in told["additionalContext"],
        told["additionalContext"][:200],
    )
    quiet = ("unit.json", "gbpusd.json", "notes.json", "pyproject.toml")
    say.check(
        f"{', '.join(quiet)} get no answer",
        [answers[name] for name in quiet] == ["", "", "", ""],
        answers,
    )
    say.verdict()


def hook_answer(shell: str, path: Path, document: object) -> str:
    """What the shipped command prints after a Write of `document`."""
    path.write_text(json.dumps(document), encoding="utf-8")
    event = {"tool_input": {"file_path": path.as_posix()}}
    ran = subprocess.run(
        [shell, "-c", hook_command()],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return ran.stdout.strip()


def test_the_hook_tells_the_agent_on_a_library_only_market(tmp_path: Path) -> None:
    shell = hook_shell()
    if shell is None:
        pytest.skip("the hook command runs under bash (Git Bash on Windows), and none was found")
    clean = json.loads(json.dumps(template()))
    clean["markets"] = [
        {
            "market_id": "fx.gbpusd",
            "instrument_ref": {"venue": "icmarkets-ctrader", "symbol": "GBPUSD"},
        }
    ]
    broken = json.loads(json.dumps(clean))
    broken["numbers"]["ema_period"]["default"] = "1"

    told = hook_answer(shell, tmp_path / "broken.json", broken)
    quiet = hook_answer(shell, tmp_path / "clean.json", clean)

    answer = json.loads(told)["hookSpecificOutput"]
    context = answer["additionalContext"]
    assert answer["hookEventName"] == "PostToolUse"
    assert context.startswith(f"{TOLD}broken.json failed.")
    found = json.loads(context[context.index("{") :])
    assert [problem["kind"] for problem in found["errors"]] == ["outside_range"]
    assert quiet == ""
