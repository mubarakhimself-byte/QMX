"""The harness hands its broker the `[ctrader]` section, so a cTrader refresh uses the token URL
the sign-in uses. Credential Manager is an in-memory keyring; nothing reaches cTrader."""

from __future__ import annotations

from collections.abc import Iterator
from typing import override

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from test_chat import home, run

from qma.harness import Harness
from qma.harness.home import QmxHome

__all__ = ["home"]

TOKEN_URL = "https://token.fake.test/apps/token"


class Memory(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    def __init__(self) -> None:
        super().__init__()
        self.held: dict[tuple[str, str], str] = {}

    @override
    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    @override
    def set_password(self, service: str, username: str, password: str) -> None:
        self.held[service, username] = password

    @override
    def delete_password(self, service: str, username: str) -> None:
        if self.held.pop((service, username), None) is None:
            raise PasswordDeleteError(service)


@pytest.fixture
def vault() -> Iterator[Memory]:
    before = keyring.get_keyring()
    memory = Memory()
    keyring.set_keyring(memory)
    try:
        yield memory
    finally:
        keyring.set_keyring(before)


def test_the_harness_broker_reads_the_ctrader_section_settings_names(
    home: QmxHome, vault: Memory
) -> None:
    home.root.mkdir(parents=True, exist_ok=True)
    (home.root / "settings.toml").write_text(
        f'[ctrader]\ntoken_url = "{TOKEN_URL}"\n', encoding="utf-8"
    )
    seen: list[object] = []

    async def body(harness: Harness) -> None:
        broker = harness._deps.broker  # pyright: ignore[reportPrivateUsage]
        seen.append(None if broker.ctrader is None else dict(broker.ctrader()))

    run(body, home)

    assert seen == [{"token_url": TOKEN_URL}]
    assert vault.held == {}
