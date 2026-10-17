from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from flows import edge, events_of, folder, kinds, node, run_folder
from pydantic import JsonValue

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
    import json, sys
    from pathlib import Path
    counter = Path(json.load(sys.stdin)["in"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    if tries == 1:
        Path("half.txt").write_text("left by the failed attempt")
        Path("seed.txt").write_text("v2")
        sys.exit(1)
    print(json.dumps({"half": Path("half.txt").exists(), "seed": Path("seed.txt").read_text()}))
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


def test_a_retry_starts_from_the_zone_as_it_was_before_the_failed_attempt(tmp_path: Path) -> None:
    home = tmp_path / "home"
    root = folder(
        tmp_path / "wf",
        [
            START,
            node("seed", "script", script="scripts/seed.py"),
            node("work", "script", script="scripts/work.py"),
        ],
        {"start": {"main": [edge("seed")]}, "seed": {"main": [edge("work")]}},
        {"seed": SEED, "work": WORK},
    )
    counter = str(tmp_path / "tries.txt")

    first, _ = run_folder(root, home, counter)
    status = resume(home, first.run_id)

    events = events_of(home, first.run_id)
    finished = [e.data["outputs"] for e in events if e.kind == "node_finished"]
    assert (first.status, status) == ("failed", "passed")
    assert finished[-1] == {"main": {"half": False, "seed": "v1"}}
    assert kinds(events, "seed").count("node_started") == 1


def test_an_external_step_of_unknown_outcome_waits_for_an_answer_and_never_retries(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    marks = tmp_path / "marks.txt"
    post = node("post", "script", script="scripts/post.py")
    post["effect"] = "irreversible_external"
    root = folder(
        tmp_path / "wf",
        [START, post],
        {"start": {"main": [edge("post")]}},
        {"post": POST.replace("MARKS", str(marks))},
    )
    found = checked(root)
    assert not isinstance(found, list)

    async def die_mid_attempt() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS)
            run = asyncio.create_task(engine.start(root, found[1], mode="test", inputs=None))
            while not marks.exists():
                await asyncio.sleep(0.05)
            for task in asyncio.all_tasks() - {asyncio.current_task()}:
                task.cancel()
            await asyncio.gather(run, return_exceptions=True)
        with Reader.open(home) as reader:
            return reader.connection.execute("SELECT run_id FROM events LIMIT 1").fetchone()[0]

    run_id = asyncio.run(die_mid_attempt())
    status = resume(home, run_id)

    events = events_of(home, run_id)
    gates = [e.data for e in events if e.kind == "gate_opened"]
    assert status == "waiting"
    assert kinds(events, "post").count("node_started") == 1
    assert [(g["category"], g["idempotency_key"]) for g in gates] == [
        ("irreversible_external", f"{run_id}:post:0:1")
    ]
    assert marks.read_text() == "sent\n"


@pytest.mark.parametrize(
    ("definition", "earlier", "decision"),
    [
        ({"type": "script", "effect": "irreversible_external"}, 0, "inbox"),
        ({"type": "llm"}, 0, "retry"),
        ({"type": "llm"}, 1, "park"),
        ({"type": "script"}, 0, "retry"),
        ({"type": "script", "effect": "irreversible"}, 0, "park"),
    ],
)
def test_after_an_unknown_outcome(
    definition: dict[str, JsonValue], earlier: int, decision: str
) -> None:
    assert after_unknown(definition, earlier) == decision
