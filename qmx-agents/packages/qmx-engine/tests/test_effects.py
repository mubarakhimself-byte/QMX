from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from flows import edge, events_of, folder, kinds, node, run_folder
from pydantic import JsonValue

from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.runner import Engine
from qmx_engine.settings import DEFAULTS
from qmx_engine.workers.effects import after_unknown

START = node("start", "trigger")

SEED = """
    import json, sys
    from pathlib import Path
    Path("seed.txt").write_text("v1")
    print(json.dumps(json.load(sys.stdin)["in"]))
"""
WORK = """
    import json, os, sys
    from pathlib import Path
    counter = Path(json.load(sys.stdin)["in"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    shared = Path(os.environ["QMX_WORK_SHARED"])
    if tries == 1:
        Path("half.txt").write_text("left by the failed attempt")
        Path("seed.txt").write_text("v2")
        sys.exit(1)
    print(json.dumps({
        "half": Path("half.txt").exists() or (shared / "half.txt").exists(),
        "seed": (shared / "seed.txt").read_text(),
    }))
"""
POST = """
    import time
    from pathlib import Path
    with Path(r"MARKS").open("a") as marks:
        marks.write("sent\\n")
    time.sleep(60)
"""


def resume(home: Path, run_id: str) -> str:
    async def go() -> str:
        with Ledger.open(home) as ledger:
            return (await Engine(home, ledger).resume(run_id)).status

    return asyncio.run(go())


def test_a_retry_sees_only_committed_files_and_nothing_the_failed_attempt_wrote(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    seed = node("seed", "script", script="scripts/seed.py")
    seed["outputs"] = {"files": [{"path": "seed.txt"}]}
    work = node("work", "script", script="scripts/work.py")
    work["retry"] = {"backoff_seconds": [0]}
    root = folder(
        tmp_path / "wf",
        [START, seed, work],
        {"start": {"main": [edge("seed")]}, "seed": {"main": [edge("work")]}},
        {"seed": SEED, "work": WORK},
    )
    counter = str(tmp_path / "tries.txt")

    first, events = run_folder(root, home, counter)

    finished = [e.data["outputs"] for e in events if e.kind == "node_finished"]
    steps = [e.data["step"] for e in events if e.kind == "ladder_step"]
    assert (first.status, steps) == ("passed", ["retry"])
    assert finished[-1] == {"main": {"half": False, "seed": "v1"}}
    assert kinds(events, "seed").count("node_started") == 1


def posting(tmp_path: Path, effect: str, timeout: int | None = None) -> tuple[Path, Workflow]:
    post = node("post", "script", script="scripts/post.py")
    post["effect"] = effect
    if timeout is not None:
        post["timeout"] = {"idle_seconds": timeout}
    root = folder(
        tmp_path / "wf",
        [START, post],
        {"start": {"main": [edge("post")]}},
        {"post": POST.replace("MARKS", str(tmp_path / "marks.txt"))},
    )
    found = checked(root)
    assert not isinstance(found, list)
    return root, found[1]


def assert_gated(tmp_path: Path, run_id: str) -> None:
    """Two resumes later the step still ran once and waits on one gate showing attempt 1's key."""
    home = tmp_path / "home"
    statuses = (resume(home, run_id), resume(home, run_id))
    events = events_of(home, run_id)
    gates = [
        (e.data["category"], e.data["idempotency_key"]) for e in events if e.kind == "gate_opened"
    ]
    assert statuses == ("waiting", "waiting")
    assert kinds(events, "post").count("node_started") == 1
    assert gates == [("irreversible_external", f"{run_id}:post:0:1")]
    assert (tmp_path / "marks.txt").read_text() == "sent\n"


@pytest.mark.parametrize("effect", ["irreversible_external", "irreversible", "compensable"])
def test_a_step_of_unknown_outcome_after_a_crash_waits_on_its_gate_over_two_resumes(
    tmp_path: Path, effect: str
) -> None:
    home, marks = tmp_path / "home", tmp_path / "marks.txt"
    root, workflow = posting(tmp_path, effect)

    async def die_mid_attempt() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS)
            run = asyncio.create_task(engine.start(root, workflow, mode="test", inputs=None))
            while not marks.exists():
                await asyncio.sleep(0.05)
            for task in asyncio.all_tasks() - {asyncio.current_task()}:
                task.cancel()
            await asyncio.gather(run, return_exceptions=True)
        with Reader.open(home) as reader:
            return reader.connection.execute("SELECT run_id FROM events LIMIT 1").fetchone()[0]

    assert_gated(tmp_path, asyncio.run(die_mid_attempt()))


def test_an_external_step_the_stuck_detector_stops_waits_on_its_gate(tmp_path: Path) -> None:
    root, _ = posting(tmp_path, "irreversible_external", timeout=1)
    quick = {"timeout.grace": 1, "scheduler.tick": 0.2}

    outcome, _ = run_folder(root, tmp_path / "home", None, **quick)

    assert outcome.status == "waiting"
    assert_gated(tmp_path, outcome.run_id)


def test_a_cancelled_external_step_waits_on_its_gate(tmp_path: Path) -> None:
    home, marks = tmp_path / "home", tmp_path / "marks.txt"
    root, workflow = posting(tmp_path, "irreversible_external")

    async def cancel_mid_attempt() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS)
            run = asyncio.create_task(engine.start(root, workflow, mode="test", inputs=None))
            while not marks.exists():
                await asyncio.sleep(0.05)
            engine.worker.cancel(next(iter(engine.worker.running)))
            return (await run).status

    assert asyncio.run(cancel_mid_attempt()) == "waiting"
    with Reader.open(home) as reader:
        run_id = reader.connection.execute("SELECT run_id FROM events LIMIT 1").fetchone()[0]
    assert_gated(tmp_path, run_id)


@pytest.mark.parametrize(
    ("definition", "earlier", "decision"),
    [
        ({"type": "script", "effect": "irreversible_external"}, 0, "inbox"),
        ({"type": "script", "effect": "irreversible"}, 0, "inbox"),
        ({"type": "script", "effect": "compensable"}, 0, "inbox"),
        ({"type": "llm"}, 0, "retry"),
        ({"type": "llm"}, 1, "inbox"),
        ({"type": "script"}, 0, "retry"),
    ],
)
def test_after_an_unknown_outcome(
    definition: dict[str, JsonValue], earlier: int, decision: str
) -> None:
    assert after_unknown(definition, earlier) == decision
