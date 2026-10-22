"""The PC's side of the Hub: a replica refuses a write, a cache fetches a missing durable blob
from its upstream and keeps it, and the owner table reads the one setting (Library AD-10,
AD-19)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from qmx_engine.ledger import redact

from qmx_library.client import OwnerTable, library_settings, primary
from qmx_library.port import Draft, LibraryRefused
from qmx_library.principal import Principal
from qmx_library.store import Store

OPERATOR = Principal("operator")
SECRET = b"the vault code is 4411"


@pytest.fixture
def server(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "server", redactor=redact, name="server") as opened:
        yield opened


def test_a_replica_refuses_a_write_and_names_the_primary(tmp_path: Path, server: Store) -> None:
    with (
        Store.open(tmp_path / "pc", redactor=redact, name="pc", role="replica") as replica,
        pytest.raises(LibraryRefused, match=r"^read_only_replica:"),
    ):
        replica.put(OPERATOR, Draft("note", "n1", title="no"), on="main", expected_head=None)


def test_a_cache_fetches_a_missing_blob_from_its_upstream_and_keeps_it(
    tmp_path: Path, server: Store
) -> None:
    done = server.put(
        OPERATOR,
        Draft("note", "n1", title="planted", blobs={"body.md": SECRET}),
        on="main",
        expected_head=None,
    )

    wanted = server.get(OPERATOR, done.object_id).blobs["body.md"].blob_id

    class Upstream:
        def fetch(self, blob_id: str) -> bytes | None:
            return SECRET if blob_id == wanted else None

    upstream = Upstream()
    with Store.open(
        tmp_path / "pc", redactor=redact, name="pc", role="cache", upstream=upstream
    ) as cache:
        cache.ingest(server.manifest(done.object_id))
        view = cache.get(OPERATOR, done.object_id, blobs="fetch")

        assert view.data["body.md"] == SECRET
        assert cache.has_blob(wanted) is True


def test_the_owner_table_flips_with_the_one_setting(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    assert primary(home) == "pc"
    assert library_settings(home) == {}

    (home / "settings.toml").write_text('[library]\nprimary = "server"\n', encoding="utf-8")

    assert primary(home) == "server"
    assert OwnerTable(primary(home)).owner("refs/items/n1/state") == "server"
    with pytest.raises(LibraryRefused, match=r"^schema_invalid:"):
        OwnerTable("somewhere")  # pyright: ignore[reportArgumentType]
