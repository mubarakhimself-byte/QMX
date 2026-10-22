"""What EP10's model lanes share: the OpenRouter row on a throwaway home, the engine driven over the
harness adapter, workflow folders made from the `one-llm` fixture, and the spend estimate.

A test run takes the OpenRouter row only where a role names it (ruling 105), so lanes on the
OpenRouter home run with `PROVIDER_PROOF`, which names it first in every role. Run this module
itself for the provider-proof lane: one `one-llm` run on the OpenRouter home whose span must record
the row (HYG0 lane 8).

No lane reads a key or the plan login. The relay reads `qmx/openrouter` in-process, by reference,
and the plan turns run through the ship home's CLI login under the lane lock (`plan_harness`).
Spend is estimated from the relay's journal rows at the Kimi row's list prices, counting cache
reads as full input, so the figure is an upper bound.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Final

from common import ENGINE_STORE, Log, boot, opened, throwaway_home

os.environ.setdefault("QMA_LIVE_SCRATCH", str(ENGINE_STORE / "homes" / "ep10-scratch"))

from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.nodes.doctor import LlmDoctor
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.runner import Engine, Mode, Outcome
from qmx_engine.settings import DEFAULTS

PR: Final = "ep10"
KIMI: Final = "moonshotai/kimi-k2.5"
KIMI_ROW: Final = f"openrouter/{KIMI}"
OPENROUTER_ROW: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), KIMI),
}
"""`scripts/live/qma/switch_lane.py`'s row, restated: that module imports another `common`."""
ROLE_KEYS: Final = tuple(
    k
    for k in DEFAULTS
    if k.startswith("roles.")
    and k not in {"roles.test_only", "roles.test_order", "roles.live_order"}
)
PROVIDER_PROOF: Final[Mapping[str, object]] = {
    **DEFAULTS,
    **{k: (KIMI_ROW, *v) for k in ROLE_KEYS if isinstance(v := DEFAULTS[k], tuple)},
}
"""The defaults with the OpenRouter row named first in every role: the provider-proof settings."""
KIMI_USD_PER_TOKEN: Final = (0.5e-6, 2.5e-6)
"""Input and output list prices of the Kimi row (`switch_lane.KIMI_PRICES`)."""
ONE_LLM: Final = (
    Path(__file__).resolve().parents[3]
    / "qmx-agents/packages/qmx-engine/tests/fixtures/workflows/one-llm"
)


def openrouter_home(slug: str) -> Path:
    """A throwaway QMX home whose only provider row is OpenRouter's."""
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    root = throwaway_home(PR, slug)
    control_service(QmxHome(root)).settings_put("providers", {"openrouter": OPENROUTER_ROW})
    return root


@asynccontextmanager
async def harnessed(root: Path) -> AsyncIterator[Any]:
    """The harness opened in this process on `root`, scrubbed as `qmx_host` boots."""
    boot()
    async with opened(root) as found:
        yield found


def folder(
    slug: str,
    *,
    role: str = "triage",
    prompt: str | None = None,
    nodes: int = 1,
    **extra: Any,
) -> Path:
    """A workflow folder from the `one-llm` fixture: its llm node takes `role`, `prompt` and any
    `extra` node fields, and `nodes` copies of it each hang off the trigger."""
    root = throwaway_home(PR, f"{slug}-wf")
    shutil.copytree(ONE_LLM, root, dirs_exist_ok=True)
    document = json.loads((root / "definition.json").read_text(encoding="utf-8"))
    start, llm = document["nodes"]
    llm |= {"role": role, **extra}
    copies = [
        {**llm, "id": f"{llm['id']}{i}", "name": f"{llm['name']} {i}"} if nodes > 1 else llm
        for i in range(1, nodes + 1)
    ]
    document["nodes"] = [start, *copies]
    edges = [{"node": c["name"], "port": "in", "map": "one"} for c in copies]
    document["connections"] = {start["name"]: {"main": [edges]}}
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    if prompt is not None:
        (root / "prompts" / "capital.md").write_text(prompt, encoding="utf-8")
    return root


async def run(
    engine_home: Path,
    workflow: Path,
    harness: Any,
    settings: Mapping[str, object] = PROVIDER_PROOF,
    *,
    mode: Mode = "test",
    fake: bool = False,
) -> tuple[Outcome, list[Event], list[Span], Engine]:
    found = checked(workflow)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {workflow} does not validate: {found}")
    adapter = HarnessAdapter(harness) if harness is not None else None
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings=settings, harness=adapter)
        engine.doctor = LlmDoctor.of(engine)
        outcome = await engine.start(workflow, found[1], mode=mode, inputs=None, fake=fake)
        await engine.settle()
    with Reader.open(engine_home) as reader:
        return outcome, reader.events(outcome.run_id), reader.spans(outcome.run_id), engine


def model_spans(spans: list[Span]) -> list[Span]:
    return [s for s in spans if s.profile is not None]


def describe(span: Span) -> str:
    return (
        f"{span.node_id} attempt {span.attempt} {span.status}: {span.role} on "
        f"{span.profile}/{span.model} tokens {span.tokens} key {span.idempotency_key}"
    )


def journals(home: Path) -> dict[str, str]:
    """Each run journal under the harness home, by chat, as a SHA-256 of its bytes."""
    return {
        path.parent.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((home / "runs").glob("*/journal.jsonl"))
    }


def relay_usd(home: Path) -> float:
    """The upper-bound OpenRouter spend of every relayed `model_call` row under `home`."""
    total = 0.0
    for path in (home / "runs").glob("*/journal.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            payload = row.get("payload", {})
            if row.get("event") != "model_call" or payload.get("profile") != "openrouter":
                continue
            read = payload.get("input_tokens", 0) + payload.get("cache_read_tokens", 0)
            total += (
                read * KIMI_USD_PER_TOKEN[0]
                + payload.get("output_tokens", 0) * (KIMI_USD_PER_TOKEN[1])
            )
    return total


async def provider_proof() -> int:
    log = Log(PR, "ep10-provider-proof")
    home = openrouter_home("provider-proof")
    log(f"provider proof: every role names {KIMI_ROW} first; it is a test-only row")
    async with harnessed(home) as found:
        outcome, _, spans, _ = await run(
            throwaway_home(PR, "provider-proof-engine"), folder("proof"), found.harness
        )
    turns = model_spans(spans)
    for span in turns:
        log(f"span {describe(span)}")
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}")
    log.check(
        "the provider-proof run spans the named OpenRouter row and one call answers",
        outcome.status == "passed"
        and [(s.profile, s.model, s.status) for s in turns] == [("openrouter", KIMI, "ok")],
        [(s.profile, s.model, s.status, s.tokens) for s in turns],
    )
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(provider_proof()))
