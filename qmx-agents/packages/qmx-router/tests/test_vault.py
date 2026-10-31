"""The vault's two rules, at the module's own surface: what may replicate, and which machine opens
what (AD-28, N5, ruling 135).

One test per rule a job depends on. No value in these tests is a real key: a source stands in for
Credential Manager, as every lane does.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from qmx_router.vault import (
    MemorySource,
    Vault,
    VaultKey,
    VaultStore,
    VaultUnavailable,
    WrongKey,
    is_replicable,
    key_file,
    read_machine_key,
    write_machine_key,
)

VALUE = "lanes-only-value"


@pytest.mark.parametrize(
    ("name", "wanted"),
    [
        ("qmx/read/x", True),
        ("qmx/data/x", True),
        ("qmx/kimi", True),
        ("qmx/openrouter", True),
        ("qmx/ctrader-demo", False),
        ("qmx/ctrader-live", False),
        ("qmx/crypto", False),
        ("qmx/backup-payload-key", False),
        ("qmx/brokers", False),
        ("qmx/chatgpt", False),
        ("qmx/read/ctrader-access-token", False),
        ("qmx/data/binance-oauth", False),
        ("qmx/kimi-2", False),
        ("plainname", False),
    ],
)
def test_the_allow_list_is_static_keys_and_provider_rows_only(name: str, wanted: bool) -> None:
    assert is_replicable(name) is wanted


def test_a_missing_key_file_names_the_machine_that_has_none(tmp_path: Path) -> None:
    home = tmp_path / "QMX" / "data"
    with pytest.raises(VaultUnavailable) as raised:
        read_machine_key(home, "contabo")
    assert str(raised.value) == "vault:unavailable:contabo"

    key = VaultKey.generate()
    written = write_machine_key(home, key)
    assert written == key_file(home) == tmp_path / "QMX" / "keys" / "vault.key"
    assert read_machine_key(home, "contabo").public_bytes() == key.public_bytes()
    if os.name == "posix":
        assert written.stat().st_mode & 0o777 == 0o600


def test_a_sealed_entry_opens_only_with_its_machines_key() -> None:
    pc, contabo = VaultKey.generate(), VaultKey.generate()
    vault = Vault(
        pc,
        MemorySource(values={"qmx/kimi": VALUE}),
        machine="pc",
        peers={"contabo": VaultKey.from_public_bytes(contabo.public_bytes())},
    )
    vault.install("qmx/kimi", VALUE)
    store = VaultStore("contabo")
    assert store.sync(vault.sync_document()) == 1

    assert store.open("qmx/kimi", contabo) == VALUE
    with pytest.raises(WrongKey):
        store.open("qmx/kimi", pc)


def test_a_trade_key_is_never_sealed_and_its_deletion_spreads_no_tombstone() -> None:
    source = MemorySource(values={"qmx/ctrader-live": VALUE, "qmx/read/ctrader-app": VALUE})
    vault = Vault(VaultKey.generate(), source, machine="pc")
    refused = vault.install("qmx/ctrader-live", VALUE, replicable=True)
    assert refused.replicable is False
    assert refused.sealed == {}
    assert vault.entries() == ()

    vault.delete("qmx/ctrader-live")
    document = vault.sync_document()
    assert document["entries"] == []
    assert source.read("qmx/ctrader-live") is None

    vault.install("qmx/read/ctrader-app", VALUE)
    vault.delete("qmx/read/ctrader-app")
    store = VaultStore("contabo")
    assert store.sync(vault.sync_document()) == 1
    assert store.names() == ()
    assert store.tombstones() == ("qmx/read/ctrader-app",)
