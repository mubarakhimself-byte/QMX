"""The engine's role resolution sees only the providers a run can use: a key row whose keyring
entry is missing, or a row that does not parse, is left out, so a strong role runs on the next
provider first."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pydantic import JsonValue
from qma.harness import Harness
from qmx_control.models import Document
from qmx_control.service import ControlService

from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.roles import parse, resolve

TIERS: dict[str, JsonValue] = dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "kimi-k3")
KIMI: Document = {
    "base_url": "https://api.moonshot.ai/anthropic",
    "credential_ref": "qmx/kimi",
    "tiers": TIERS,
}
OPENROUTER: Document = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": TIERS,
}


class Host:
    def __init__(self, root: Path) -> None:
        self.control = ControlService(root)

    def register_sink(self, name: str, sink: object) -> None:
        pass

    def register_policy(self, name: str, policy: object) -> None:
        pass


def test_a_key_row_with_no_keyring_entry_is_skipped_by_role_resolution(tmp_path: Path) -> None:
    host = Host(tmp_path)
    host.control.settings_put(
        "providers", {"kimi": KIMI, "openrouter": OPENROUTER, "broken": {"base_url": 7}}
    )
    checked: list[str] = []

    def stored(reference: str) -> bool:
        checked.append(reference)
        return reference == "qmx/openrouter"

    adapter = HarnessAdapter(cast(Harness, host), stored=stored)
    profiles = adapter.profiles()
    strong = tuple(
        found
        for row in ("kimi/k3", "openrouter/moonshotai/kimi-k2.5", "claude/opus")
        if (found := parse(row, test_only=False, window=200_000)) is not None
    )
    chosen = resolve(strong, profiles, None)
    assert profiles == {"claude", "openrouter"}
    assert sorted(checked) == ["qmx/kimi", "qmx/openrouter"]
    assert not isinstance(chosen, str)
    assert chosen.name == "openrouter/moonshotai/kimi-k2.5"
