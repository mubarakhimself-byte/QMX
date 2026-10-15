"""Shared parts of the HP12 switch checks: a harness with two fake-model rows, the OpenRouter
Kimi row for the ship home, the OpenRouter spend guard, and quote-then-apply with its log."""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Final

from common import (
    EVIDENCE,
    SCRATCH,
    Log,
    Session,
    capture_launches,
    only_tools,
    put_providers,
    throwaway_home,
)
from fake_model import FakeModel, Turn
from money_lane import direct_row
from spend import Ledger, Prices, key_usage, openrouter_key

KIMI_MODEL: Final = "moonshotai/kimi-k2.5"
KIMI_PRICES: Final = Prices(KIMI_MODEL, 0.5e-6, 2.5e-6)
"""The cheapest Kimi on OpenRouter in HP1's model list (`evidence/hp1/openrouter-models.json`)."""
LEDGER_NAME: Final = os.environ.get("QMA_SPEND_LEDGER", "openrouter-spend.tsv")
BUDGET_USD: Final = float(os.environ.get("QMA_SPEND_BUDGET", "0.15"))
"""Read at import, before `boot` scrubs the environment."""
OPENROUTER_ROW: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), KIMI_MODEL),
}
WORKSPACE: Final = SCRATCH / "hp12-ws"


def spend_ledger(prices: Prices = KIMI_PRICES) -> Ledger:
    """The guard for every OpenRouter turn, at `<evidence>/<LEDGER_NAME>`."""
    secret = openrouter_key()
    if secret is None:
        raise SystemExit("BLOCKED: keyring qmx/openrouter is empty")
    return Ledger(Path(EVIDENCE or ".") / LEDGER_NAME, BUDGET_USD, prices, key_usage(secret))


@asynccontextmanager
async def ship_providers(session: Session, log: Log) -> AsyncIterator[None]:
    """The OpenRouter Kimi row in the ship home for the check, then its rows as found."""
    control = session.control
    found = dict(control.settings_get("providers"))
    control.settings_put("providers", found | {"openrouter": OPENROUTER_ROW})
    log(f"ship home [providers] += openrouter tiers -> {KIMI_MODEL}")
    try:
        yield
    finally:
        control.settings_put("providers", found)
        log(f"ship home [providers] restored to {sorted(control.settings_get('providers'))}")


async def start(
    root: Path,
    *,
    title: str,
    model: str = "opus",
    profile: str = "fake",
    test: Any = None,
    tools: list[str] | None = None,
    **spec: Any,
) -> Session:
    """A harness on `root` and one chat in it. `spec` goes to `NewChat` (effort, mode, kind)."""
    from qma.harness import Harness, NewChat, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    if tools is not None:
        only_tools(tools)
    home = QmxHome(root)
    control = control_service(home)
    harness = await Harness.open(home, control=control, test=test)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    chat = await harness.start_chat(
        NewChat(title=title, model=model, workspace=WORKSPACE, profile=profile, **spec)
    )
    return Session(harness, home, control, chat)


async def fake_pair(
    log: Log, slug: str, script: list[Turn], *, tools: list[str], **spec: Any
) -> tuple[FakeModel, Session, list[Any]]:
    """A throwaway home with rows `fake` and `fake2` on one fake model, and a chat on `fake`.
    Returns the fake model, the session and every CLI the harness launches from now on."""
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home(slug)
    fake = FakeModel(script).start()
    put_providers(root, {"fake": direct_row(fake.url), "fake2": direct_row(fake.url)})
    launched = capture_launches()
    session = await start(
        root, title=slug, test=TestMode(loopback_http_provider=True), tools=tools, **spec
    )
    log(f"home {root}, fake model {fake.url}, chat {session.chat}")
    return fake, session, launched


async def quote(log: Log, session: Session, **change: Any) -> Any:
    from qma.harness import ConfigChange  # noqa: PLC0415
    from qma.harness.profiles import ProfileName  # noqa: PLC0415

    if "profile" in change:
        change["profile"] = ProfileName(change["profile"])
    found = await session.harness.quote(session.chat, ConfigChange(**change))
    steps = [step.value for step in found.steps]
    log(
        f"quote {change}: steps={steps} warning={found.warning!r} "
        f"tokens={found.recomputed_tokens} tasks={found.background_tasks}"
    )
    return found


async def apply(log: Log, session: Session, quote_id: str) -> float:
    """Seconds from `apply` until it returned, which for a relaunch is the new CLI connected."""
    began = time.perf_counter()
    await session.harness.apply(session.chat, quote_id)
    took = time.perf_counter() - began
    record = session.harness._chat(session.chat).record
    log(f"applied in {took:.2f} s; config {record.config.profile}/{record.config.model}")
    return took


def assistant_entries(raw: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("type") == "assistant":
            found.append(entry)
    return found


def last_reply_text(raw: str) -> str | None:
    """The last non-blank reply text in a transcript (HP1: a provider can close a turn with
    thinking and a blank text)."""
    texts = [
        str(block.get("text", ""))
        for entry in assistant_entries(raw)
        for block in entry.get("message", {}).get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    replies = [text for text in texts if text.strip()]
    return replies[-1] if replies else None


def relayed_rows(session: Session, profile: str) -> list[dict[str, Any]]:
    """The payloads of the run journal's `model_call` rows for `profile`."""
    return [
        row["payload"]
        for row in session.journal()
        if row["event"] == "model_call" and row["payload"].get("profile") == profile
    ]
