"""Each host holds its own pass key (C-28): a server cannot sign a pass as This PC or as him.

This PC pairs two servers, `ldn-1` and `ldn-2`, each with a key of its own, and every host serves
the host route in process. A server's `host-keys` is what the pairing script's heredoc writes
there. Every key is a fake made at runtime.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import JsonValue
from qmx_apps.errors import AppError
from qmx_apps.supervisor import Supervisor
from qmx_engine.service.forward import PASS_HEADER, Remote, forward_router, mint_host_pass

from qmx_host.host_route import (
    ANSWERS,
    HOST_KEYS,
    Answering,
    Answers,
    held_keys,
    host_router,
    pair_place,
    pass_key_script,
)
from qmx_host.node_link import NodeLink

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
SCHEMA = "qmx.host.forward/1"
NOT_VERIFIED = (401, "bad_pass", "the host pass does not verify")
OK = (200, "ok", "")


async def no_beats() -> Mapping[str, object]:
    return {"latest": {}}


def route(home: Path, here: str) -> TestClient:
    """`here`'s host route over its own vault's pass keys."""
    home.mkdir(parents=True, exist_ok=True)
    link = NodeLink(
        home,
        here=here,
        apps=cast(Supervisor, None),
        settings=dict,
        pass_keys=lambda: held_keys(home),
    )
    answering = Answering(
        link,
        pass_keys=lambda: held_keys(home),
        heartbeats=no_beats,
        store_root=lambda: None,
        answers=Answers(home / ANSWERS),
    )
    app = FastAPI()
    app.include_router(host_router(answering))
    return TestClient(app)


def ask(host: TestClient, token: str) -> tuple[int, str, str]:
    answer = host.post(
        "/api/host/forward",
        json={"schema_version": SCHEMA, "verb": "heartbeats", "args": {}},
        headers={PASS_HEADER: token},
    )
    found = cast(dict[str, Any], answer.json())
    return answer.status_code, str(found.get("code", "ok")), str(found.get("message", ""))


def paired(root: Path, place: str) -> str:
    """Pair `place` from This PC: the PC keeps the key, and the server's `host-keys` is the
    pairing script's heredoc, owner-only as the script writes it, so the key rides no command
    line."""
    key = pair_place(root / "pc", place)
    command, written = pass_key_script(key).split("<<'QMXIN'\n", 1)
    assert key not in command
    vault = root / place / "vault"
    vault.mkdir(parents=True, exist_ok=True)
    handle = os.open(vault / HOST_KEYS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        out.write(written.removesuffix("QMXIN\n"))
    return key


def signed(key: str, claims: Mapping[str, object]) -> str:
    def b64(raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    body = b64(json.dumps(claims, sort_keys=True).encode("utf-8"))
    return f"{body}.{b64(hmac.new(key.encode(), body.encode(), hashlib.sha256).digest())}"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    paired(tmp_path, "ldn-1")
    paired(tmp_path, "ldn-2")
    return tmp_path


def test_this_pc_keeps_every_servers_key_and_each_server_only_its_own(home: Path) -> None:
    pc = held_keys(home / "pc")

    assert sorted(pc) == ["ldn-1", "ldn-2"]
    assert pc["ldn-1"] != pc["ldn-2"]
    assert held_keys(home / "ldn-1") == {"pc": pc["ldn-1"]}
    assert held_keys(home / "ldn-2") == {"pc": pc["ldn-2"]}


def test_this_pcs_pass_verifies_at_its_server_and_nowhere_else(home: Path) -> None:
    keys = held_keys(home / "pc")
    to_ldn1 = mint_host_pass(keys["ldn-1"], source="pc", target="ldn-1", principal="operator")
    to_ldn2 = mint_host_pass(keys["ldn-2"], source="pc", target="ldn-2", principal="operator")

    assert ask(route(home / "ldn-1", "ldn-1"), to_ldn1) == OK
    assert ask(route(home / "ldn-2", "ldn-2"), to_ldn2) == OK
    assert ask(route(home / "ldn-2", "ldn-2"), to_ldn1) == NOT_VERIFIED


def test_a_server_cannot_sign_as_this_pc_or_as_itself_to_another_server(home: Path) -> None:
    held = held_keys(home / "ldn-1")["pc"]
    as_pc = mint_host_pass(held, source="pc", target="ldn-2", principal="operator")
    as_puller = mint_host_pass(held, source="pc", target="ldn-2", principal="host:pc")
    as_itself = mint_host_pass(held, source="ldn-1", target="ldn-2", principal="host:ldn-1")
    ldn2 = route(home / "ldn-2", "ldn-2")

    assert ask(ldn2, as_pc) == NOT_VERIFIED
    assert ask(ldn2, as_puller) == NOT_VERIFIED
    assert ask(ldn2, as_itself) == (401, "bad_pass", "this host holds no pass key for 'ldn-1'")


@pytest.mark.parametrize(
    ("principal", "answered"),
    [
        ("operator", (401, "bad_pass", "a pass from ldn-1 cannot speak as operator")),
        ("host:pc", (401, "bad_pass", "a pass from ldn-1 cannot speak as host:pc")),
        ("host:ldn-2", (401, "bad_pass", "a pass from ldn-1 cannot speak as host:ldn-2")),
        ("host:ldn-1", OK),
        ("run:r1", OK),
    ],
)
def test_a_server_speaks_to_this_pc_only_for_itself_and_its_runs(
    home: Path, principal: str, answered: tuple[int, str, str]
) -> None:
    held = held_keys(home / "ldn-1")["pc"]
    token = mint_host_pass(held, source="ldn-1", target="pc", principal=principal)

    assert ask(route(home / "pc", "pc"), token) == answered


def test_a_pass_from_nobody_or_from_an_unpaired_host_is_refused(home: Path) -> None:
    held = held_keys(home / "ldn-1")["pc"]
    nobody = signed(held, {"v": 1, "to": "ldn-1", "principal": "operator", "exp": 2**40})
    stranger = mint_host_pass("a-key-nobody-paired", source="pc", target="ldn-1", principal="x")
    ldn1 = route(home / "ldn-1", "ldn-1")

    assert ask(ldn1, nobody) == (401, "bad_pass", "this host holds no pass key for None")
    assert ask(ldn1, stranger) == NOT_VERIFIED


def test_a_replayed_pass_reaches_only_the_host_it_names_and_only_until_it_expires(
    home: Path,
) -> None:
    keys = held_keys(home / "pc")
    late = mint_host_pass(
        keys["ldn-1"], source="pc", target="ldn-1", principal="operator", now=1_000.0
    )
    seen_by_ldn1 = mint_host_pass(keys["ldn-1"], source="pc", target="ldn-1", principal="operator")

    assert ask(route(home / "ldn-1", "ldn-1"), late) == (
        401,
        "expired_pass",
        "the host pass outlived its call",
    )
    assert ask(route(home / "ldn-2", "ldn-2"), seen_by_ldn1) == NOT_VERIFIED
    assert ask(route(home / "pc", "pc"), seen_by_ldn1) == (
        401,
        "bad_pass",
        "this host holds no pass key for 'pc'",
    )


def test_an_old_shared_key_home_answers_no_pass_until_it_is_paired_again(tmp_path: Path) -> None:
    shared = "the-pairing-key-both-machines-held"
    for machine in ("pc", "old-1"):
        (tmp_path / machine / "vault").mkdir(parents=True)
        (tmp_path / machine / "vault" / "pairing-key").write_text(shared, encoding="utf-8")
    old = mint_host_pass(shared, source="pc", target="old-1", principal="operator")
    old1 = route(tmp_path / "old-1", "old-1")
    rows = {"placement.old-1.kind": "owned", "placement.old-1.engine_url": "http://127.0.0.1:9"}
    link = NodeLink(
        tmp_path / "pc",
        here="pc",
        apps=cast(Supervisor, None),
        settings=lambda: rows,
        pass_keys=lambda: held_keys(tmp_path / "pc"),
    )

    assert ask(old1, old) == (401, "bad_pass", "this host holds no pass key for 'pc'")
    with pytest.raises(AppError) as unpaired:
        link.heartbeats("old-1", principal="operator")
    assert (unpaired.value.code, str(unpaired.value)) == (
        "placement_unreachable",
        "old-1 has no owned place row with a host URL, or this home holds no pass key for old-1;"
        " set old-1 up again in Connect to pair it",
    )

    key = paired(tmp_path, "old-1")
    fresh = mint_host_pass(key, source="pc", target="old-1", principal="operator")

    assert ask(old1, fresh) == OK
    assert ask(old1, old) == NOT_VERIFIED


def test_pairing_again_after_a_key_change_retires_the_old_key_on_both_ends(home: Path) -> None:
    before = held_keys(home / "pc")
    from_ldn1 = mint_host_pass(before["ldn-1"], source="ldn-1", target="pc", principal="run:r1")
    to_ldn1 = mint_host_pass(before["ldn-1"], source="pc", target="ldn-1", principal="operator")

    again = paired(home, "ldn-1")
    after = held_keys(home / "pc")
    pc, ldn1 = route(home / "pc", "pc"), route(home / "ldn-1", "ldn-1")

    assert (after["ldn-1"] == again, after["ldn-2"] == before["ldn-2"]) == (True, True)
    assert ask(pc, from_ldn1) == NOT_VERIFIED
    assert ask(ldn1, to_ldn1) == NOT_VERIFIED
    assert ask(ldn1, mint_host_pass(again, source="pc", target="ldn-1", principal="x")) == OK


class Answered:
    name = "pc"

    def answer(self, verb: str, args: Mapping[str, JsonValue], *, principal: str) -> JsonValue:
        del args
        return {"verb": verb, "principal": principal}

    def open_items(self) -> list[Mapping[str, JsonValue]]:
        return []


@pytest.mark.parametrize(
    ("principal", "answered"),
    [
        (
            "operator",
            (401, {"code": "bad_pass", "message": "a pass from ldn-1 cannot speak as operator"}),
        ),
        ("run:r1", (200, {"ok": True, "value": {"verb": "runs.list", "principal": "run:r1"}})),
    ],
)
def test_the_engine_forward_route_takes_the_same_keys(
    home: Path, principal: str, answered: tuple[int, object]
) -> None:
    app = FastAPI()
    app.include_router(forward_router(Remote(Answered()), lambda: held_keys(home / "pc")))
    held = held_keys(home / "ldn-1")["pc"]
    token = mint_host_pass(held, source="ldn-1", target="pc", principal=principal)
    answer = TestClient(app).post(
        "/api/engine/forward", json={"verb": "runs.list", "args": {}}, headers={PASS_HEADER: token}
    )
    found = cast(dict[str, Any], answer.json())

    assert (answer.status_code, found.get("detail", found)) == answered


def test_no_app_may_declare_the_host_pass_keys(tmp_path: Path) -> None:
    source = tmp_path / "asker"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    manifest = source / "app.toml"
    text = manifest.read_text(encoding="utf-8").replace(
        "[capabilities]\n", "[capabilities]\nsecrets = { ASKED = 'qmx/Host-Keys' }\n", 1
    )
    manifest.write_text(text, encoding="utf-8")
    owner = Supervisor(tmp_path / "home")
    try:
        with pytest.raises(AppError) as refused:
            owner.install(source, trust="first_party")
    finally:
        owner.close()

    assert str(refused.value) == (
        "qmx/Host-Keys is the host's own host pass keys, which sign every call between his"
        " machines; no app may declare it."
    )
