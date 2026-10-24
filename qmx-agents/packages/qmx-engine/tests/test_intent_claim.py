"""A node's intent key is claimed when its attempt starts and released when it ends (AD-24, AD-30).

Two runs that declare one key both start; the claim is what says which of them holds it. The
runner reaches the store through the `claims` port, so these tests hold a recorder there and read
the order the two calls came in.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from flows import ONE_TRY, Script, edge, node, workflow
from qmx_library.port import Claim

from qmx_engine.ledger.store import Ledger
from qmx_engine.runner import Engine, Outcome


class Recording:
    """Records every claim and release the runner makes, answering as the Library's client does."""

    def __init__(self, *, granted: bool = True) -> None:
        self.granted = granted
        self.calls: list[tuple[str, str, str]] = []

    def claim(self, intent_key: str, run_id: str, ttl: int) -> Claim:
        self.calls.append(("claim", intent_key, run_id))
        return Claim(self.granted, run_id if self.granted else "run-0", None)

    def release(self, intent_key: str, run_id: str) -> None:
        self.calls.append(("release", intent_key, run_id))


def run(tmp_path: Path, claims: Recording, script: Script) -> Outcome:
    folder = tmp_path / "flow"
    folder.mkdir()
    definition = workflow(
        [node("start", "trigger"), node("land", "script", intent_key="clipping|42")],
        {"start": {"main": [edge("land")]}},
    )
    document = definition.model_dump(mode="json", by_alias=True, exclude_none=True)
    (folder / "definition.json").write_text(json.dumps(document), encoding="utf-8")

    async def go() -> Outcome:
        with Ledger.open(tmp_path / "home") as ledger:
            engine = Engine(
                tmp_path / "home",
                ledger,
                settings=ONE_TRY,
                executors={"script": script},
                claims=claims,
            )
            return await engine.start(folder, definition, mode="test", inputs=None, run_id="run-1")

    return asyncio.run(go())


def test_a_node_intent_key_is_claimed_and_released_when_the_output_lands(tmp_path: Path) -> None:
    claims = Recording()
    script = Script()
    found = run(tmp_path, claims, script)

    assert found.status == "passed"
    assert script.calls == [("land", 0, None)]
    assert claims.calls == [("claim", "clipping|42", "run-1"), ("release", "clipping|42", "run-1")]


def test_a_claim_another_run_holds_is_not_released_by_this_one(tmp_path: Path) -> None:
    claims = Recording(granted=False)
    script = Script()
    found = run(tmp_path, claims, script)

    assert found.status == "passed"
    assert script.calls == [("land", 0, None)]
    assert claims.calls == [("claim", "clipping|42", "run-1")]


def test_a_node_that_declares_no_intent_key_claims_nothing(tmp_path: Path) -> None:
    claims = Recording()
    folder = tmp_path / "flow"
    folder.mkdir()
    definition = workflow(
        [node("start", "trigger"), node("land", "script")],
        {"start": {"main": [edge("land")]}},
    )

    async def go() -> Outcome:
        with Ledger.open(tmp_path / "home") as ledger:
            engine = Engine(
                tmp_path / "home",
                ledger,
                settings=ONE_TRY,
                executors={"script": Script()},
                claims=claims,
            )
            return await engine.start(folder, definition, mode="test", inputs=None, run_id="run-1")

    assert asyncio.run(go()).status == "passed"
    assert claims.calls == []
