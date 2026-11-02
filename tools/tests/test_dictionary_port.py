"""The port of the Stats dictionary (A12, AD-114): 239 records in, 239 drafts out, none lost, each
passing the entry checker, roles mapped by the table and never guessed, and a rerun the same."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Protocol, cast

import pytest

_ROOT = Path(__file__).resolve().parents[2]


class _Port(Protocol):
    records: tuple[object, ...]
    unmapped: dict[str, list[str]]

    def faces(self) -> list[dict[str, object]]: ...
    def lost(self) -> list[str]: ...
    def problems(self) -> list[str]: ...
    def statuses(self) -> Mapping[str, int]: ...
    def transfer(self) -> dict[str, dict[str, int]]: ...
    def document(self) -> dict[str, object]: ...


class _Script(Protocol):
    SEED: Path
    FAMILIES: Mapping[str, str]
    README: str

    def main(self, argv: Sequence[str] | None = None) -> int: ...
    def port(self, seed: Path = ..., table: Mapping[str, list[str]] | None = None) -> _Port: ...
    def roles_table(self) -> dict[str, list[str]]: ...
    def stale(self, made: _Port, seed: Path = ...) -> list[str]: ...


def _script() -> _Script:
    spec = importlib.util.spec_from_file_location(
        "dictionary_port", _ROOT / "tools" / "dictionary" / "port_stats.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return cast("_Script", module)


SCRIPT = _script()
MADE = SCRIPT.port()


def _by_id() -> dict[str, dict[str, object]]:
    return {str(face["entry_id"]): face for face in MADE.faces()}


def test_the_dry_run_ports_239_into_239_drafts_and_loses_none(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = SCRIPT.main(["--dry-run"])

    lines = capsys.readouterr().out.splitlines()
    assert (code, lines[:7], lines[-1]) == (
        0,
        [
            "parsed 239",
            "drafts 239",
            "lost 0",
            "refused 0",
            "checker problems 0",
            "status named 239",
            "unmapped role strings 27",
        ],
        "current SOURCES.json, port.json",
    )


def test_every_draft_passes_the_entry_checker_and_no_name_is_taken_twice() -> None:
    assert (dict(MADE.statuses()), MADE.problems(), MADE.lost()) == ({"named": 239}, [], [])


def test_no_field_of_any_record_is_lost() -> None:
    faces = list(MADE.faces())
    missing = [
        (face["entry_id"], name)
        for record, face in zip(MADE.records, faces, strict=True)
        for name, text in cast("Mapping[str, str]", getattr(record, "entry").fields).items()
        if text
        and text not in face.values()
        and text not in [s["quote"] for s in cast("list[dict[str, str]]", face["sources"])]
    ]
    assert (len(faces), missing) == (239, [])


def test_a_role_string_the_table_lacks_is_reported_and_never_guessed() -> None:
    table = {k: v for k, v in SCRIPT.roles_table().items() if k not in ("context", "target")}

    reduced = SCRIPT.port(table=table)

    by_id = {str(f["entry_id"]): f for f in reduced.faces()}
    assert set(reduced.unmapped) - set(MADE.unmapped) == {"context", "target"}
    assert (len(reduced.unmapped["context"]), len(reduced.unmapped["target"])) == (119, 9)
    assert (
        by_id["trend-direction"]["eligible_roles"],
        _by_id()["trend-direction"]["eligible_roles"],
    ) == (
        ["confirmation", "filter", "invalidation", "exit"],
        ["context", "confirmation", "filter", "invalidation", "exit"],
    )


def test_no_entry_claims_native_and_each_stated_claim_quotes_its_sentence() -> None:
    claims = MADE.transfer()

    def quoted(face: dict[str, object]) -> str:
        sources = cast("list[dict[str, str]]", face["sources"])
        return next(s["quote"] for s in sources if s["source_ref"].endswith(" Transfer notes"))

    stated = [
        (face["entry_id"], name)
        for face in MADE.faces()
        for name, claim in cast("dict[str, str]", face["transfer"]).items()
        if claim != "not_assessed"
        and not any(w in quoted(face).lower() for w in ("forex", "spot fx", "spot-fx"))
    ]
    assert (claims["fx"], claims["spot_crypto"], claims["future"], stated) == (
        {"direct": 46, "not_assessed": 187, "not_transferable": 6},
        {"direct": 46, "not_assessed": 193},
        {"not_assessed": 239},
        [],
    )
    assert _by_id()["exchange-volume"]["transfer"] == {
        "commodity_cfd": "not_assessed",
        "future": "not_assessed",
        "fx": "not_transferable",
        "index_cfd": "not_assessed",
        "metal": "not_assessed",
        "perp": "not_assessed",
        "spot_crypto": "not_assessed",
        "stock": "not_assessed",
        "stock_cfd": "not_assessed",
    }


def test_a_slug_two_families_share_is_scoped_by_family_and_linked() -> None:
    faces = _by_id()
    scoped = sorted(i for i in faces if "." in i)

    assert (len(faces), len(scoped)) == (239, 21)
    assert [faces[i].get("same_word_as") for i in ("locations.vwap", "exits.time-stop")] == [
        ["context.vwap@1"],
        ["time-exit-bars@1"],
    ]


def _crlf_copy(tmp_path: Path) -> Path:
    for name in [SCRIPT.README, *SCRIPT.FAMILIES]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((SCRIPT.SEED / name).read_bytes().replace(b"\n", b"\r\n"))
    return tmp_path


def test_a_rerun_changes_nothing_even_on_a_crlf_checkout(tmp_path: Path) -> None:
    again: Callable[[], _Port] = SCRIPT.port
    seed = _crlf_copy(tmp_path)
    for name in ("SOURCES.json", "port.json"):
        shutil.copyfile(SCRIPT.SEED / name, seed / name)

    assert (again().document() == MADE.document(), SCRIPT.port(seed).document()) == (
        True,
        MADE.document(),
    )
    assert (SCRIPT.stale(MADE), SCRIPT.stale(SCRIPT.port(seed), seed)) == ([], [])
