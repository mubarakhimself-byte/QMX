"""C-10: the shipped trading-node app, installed and started under a real supervisor.

The app is this folder, installed with its own locked environment into a throwaway home and
published with a signature made for the test, the way a money app must be. The keys document is a
fake made here, with no venue in it, so every venue reads "not set up".
"""

from __future__ import annotations

import re
import secrets
import shutil
import time
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from qmn.app.operations import READS
from qmn.app.server import OPERATIONS
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Stage
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume

APP_FOLDER = Path(__file__).resolve().parents[1]
EXAMPLE = APP_FOLDER.parents[2] / "examples/apps/exchange-status"
APP = "trading-node"
ANSWER_BUDGET_SECONDS = 2.0
"""Test bound: `[node] op_answer_budget_ms`, the most one operation may take to answer."""
KEYS = '{"schema_version": "qmx.node.keys/1"}'

GOOD: dict[str, Document] = {
    "status": {},
    "units": {"deployment_id": "dep-none"},
    "positions": {"account": "demo-1"},
    "journal_tail": {"after_sequence": -1, "streams": ["node"]},
    "passport": {},
    "deployments": {},
    "records": {"account": "demo-1", "symbols": ["EURUSD"]},
    "withdraw": {"deployment_id": "dep-none"},
    "pause": {"scope": {"account": "demo-1"}},
    "resume": {"scope": {"account": "demo-1"}},
    "kill": {"level": "YELLOW", "scope": {"account": "demo-1"}},
    "flatten": {"scope": {"account": "demo-1"}},
    "bind": {"account": {"id": "demo-1"}, "action": "add"},
    "confirm_same_node": {},
    "take_over": {"old_tag": "abcdefgh", "confirmed_gone": True},
    "sign_in_begin": {"venue": "ctrader"},
    "sign_in_code": {"code": "fake-code"},
    "self_test": {"account": "demo-1"},
    "rotate_keys": {},
}
BAD: tuple[Document, ...] = (
    {"surprise": True},
    {"op_id": 12, "issued_at": "not a time"},
    {"scope": 5, "level": "PURPLE", "deployment": [], "after_sequence": "x"},
)


def proved(owner: Supervisor, definition_hash: str) -> None:
    with history(owner.home, APP) as state:
        for stage in ("tests", "sandbox", "shadow"):
            state.append(
                Evidence(
                    definition_hash=definition_hash,
                    version="0.1.0",
                    stage=cast(Stage, stage),
                    passed=True,
                    inputs={"fixture": True},
                    versions={"definition": definition_hash},
                    results={"passed": True},
                    duration_seconds=0.1,
                )
            )


@pytest.fixture(scope="module")
def supervisor(tmp_path_factory: pytest.TempPathFactory) -> Generator[Supervisor]:
    home = tmp_path_factory.mktemp("trading-node") / "home"
    owner = Supervisor(
        home, secret_getter=lambda service, _: KEYS if service.endswith("keys") else None
    )
    try:
        installed = owner.install(APP_FOLDER, trust="first_party")
        definition_hash = str(installed["definition_hash"])
        proved(owner, definition_hash)
        owner.road.signing_key(secrets.token_urlsafe(32))
        owner.road.publish(
            APP, definition_hash, signature=owner.road.sign(APP, definition_hash, None)
        )
        owner.start(APP)
        yield owner
    finally:
        owner.close()


def ask(owner: Supervisor, operation: str, arguments: Document) -> tuple[Document, float]:
    started = time.perf_counter()
    called = owner.call(APP, operation, arguments)
    elapsed = time.perf_counter() - started
    answer = called["result"]
    assert isinstance(answer, dict), (operation, called)
    return answer, elapsed


def errors(owner: Supervisor) -> object:
    return cast(Document, owner.status(APP)["metrics"])["errors"]


def deployment_on(supervisor: Supervisor, deployment_id: str, account: str) -> Document:
    """A deployment this node keeps, so its account is a scope the node holds."""
    state, _ = ask(supervisor, "status", {})
    tag = cast(Document, cast(Document, state["value"])["identity"])["tag"]
    return {
        "schema_version": "qmx.node.deployment/1",
        "deployment_id": deployment_id,
        "node": {"tag": tag},
        "unit": {"id": "dummy", "version": 1},
        "unit_document": {"markets": [{"market_id": "fx.eurusd"}]},
        "markets": [{"market_id": "fx.eurusd"}],
        "starting": {"source": "defaults", "values": {}},
        "compiled_fingerprint": "fp1:sha256:" + "a" * 64,
        "g_record": {"compiled_fingerprint": "fp1:sha256:" + "a" * 64},
        "files": [],
        "account": {"id": account},
        "snapshots": [],
        "lane": "paper",
    }


def test_every_operation_answers_inside_two_seconds_with_no_errors(supervisor: Supervisor) -> None:
    deployment = deployment_on(supervisor, "dep-1", "demo-1")
    good: dict[str, Document] = {**GOOD, "deploy": {"deployment": deployment}}
    answered: dict[str, list[object]] = {}
    slowest = 0.0
    for operation in OPERATIONS:
        for arguments in (good[operation], *BAD):
            answer, elapsed = ask(supervisor, operation, arguments)
            answered.setdefault(operation, []).append(answer.get("code", "ok"))
            slowest = max(slowest, elapsed)

    assert slowest < ANSWER_BUDGET_SECONDS
    assert errors(supervisor) == 0
    assert supervisor.status(APP)["status"] == "running"
    assert all(codes[1:] == ["bad_argument"] * 3 for codes in answered.values()), answered
    assert {name: codes[0] for name, codes in answered.items()} == {
        "status": "ok",
        "units": "ok",
        "positions": "ok",
        "journal_tail": "ok",
        "passport": "ok",
        "deployments": "ok",
        "records": "not_set_up",
        "deploy": "ok",
        "withdraw": "unknown_deployment",
        "pause": "ok",
        "resume": "ok",
        "kill": "ok",
        "flatten": "ok",
        "bind": "not_set_up",
        "confirm_same_node": "ok",
        "take_over": "not_available",
        "sign_in_begin": "not_set_up",
        "sign_in_code": "not_set_up",
        "self_test": "not_set_up",
        "rotate_keys": "ok",
    }


def test_the_node_reads_ready_with_no_units_and_declares_every_operation_and_no_job(
    supervisor: Supervisor,
) -> None:
    ask(supervisor, "resume", {"scope": "all"})
    state, _ = ask(supervisor, "status", {})
    manifest = Definition.load(APP_FOLDER).manifest

    value = cast(Document, state["value"])
    assert value["headline"] == "Ready, no units yet"
    assert [venue["session"] for venue in cast(list[Document], value["venues"])] == [
        "not_set_up",
        "not_set_up",
    ]
    assert manifest.entrypoints.jobs == []
    assert sorted(manifest.operations) == sorted(OPERATIONS)
    assert {
        (name, operation.approval, operation.state)
        for name, operation in manifest.operations.items()
    } == {(name, "domain_write" if name in READS else "manage", "instance") for name in OPERATIONS}
    assert (manifest.breaker.max_errors, manifest.breaker.restart) == (1000, "backoff")
    (served,) = supervisor.registry()
    hints = {
        str(tool["name"]): cast(Document, tool["annotations"])["readOnlyHint"]
        for tool in cast(list[Document], served["tools"])
    }
    assert hints == {
        **dict.fromkeys(
            ("status", "units", "positions", "journal_tail", "passport", "deployments", "records"),
            True,
        ),
        **dict.fromkeys(
            (
                "deploy",
                "withdraw",
                "pause",
                "resume",
                "kill",
                "flatten",
                "bind",
                "confirm_same_node",
                "take_over",
                "sign_in_begin",
                "sign_in_code",
                "self_test",
                "rotate_keys",
            ),
            False,
        ),
    }


def test_an_older_pause_is_superseded_while_an_older_kill_applies(supervisor: Supervisor) -> None:
    scope: Document = {"account": "demo-order"}
    kept, _ = ask(
        supervisor, "deploy", {"deployment": deployment_on(supervisor, "dep-order", "demo-order")}
    )
    assert kept["ok"] is True, kept
    resumed, _ = ask(
        supervisor,
        "resume",
        {"op_id": "order-resume", "issued_at": "2026-10-01T10:00:02+00:00", "scope": scope},
    )
    paused, _ = ask(
        supervisor,
        "pause",
        {"op_id": "order-pause", "issued_at": "2026-10-01T10:00:01+00:00", "scope": scope},
    )
    killed, _ = ask(
        supervisor,
        "kill",
        {
            "op_id": "order-kill",
            "issued_at": "2026-10-01T10:00:00+00:00",
            "scope": scope,
            "level": "ORANGE",
        },
    )

    assert resumed["ok"] is True
    assert (paused["code"], paused["value"]) == ("superseded", {"newer_op_id": "order-resume"})
    assert killed == {"ok": True, "value": {"level_in_force": "ORANGE"}, "op_id": "order-kill"}
    assert errors(supervisor) == 0


def test_a_direct_call_without_an_op_id_gets_one_minted(supervisor: Supervisor) -> None:
    answer, _ = ask(supervisor, "flatten", {"scope": "all"})

    assert answer["value"] == {"state": "accepted", "positions": 0}
    assert re.fullmatch(r"[0-9a-f]{32}", str(answer["op_id"]))


def test_journal_tail_mid_write_returns_whole_lines_and_leaves_the_file_unchanged(
    supervisor: Supervisor,
) -> None:
    data = Volume(supervisor.home, APP).root / "data"
    (stream,) = data.glob("journal/*node_lifecycle*/000000.jsonl")
    committed = stream.read_bytes()
    with stream.open("ab") as handle:
        handle.write(b'{"series":"journal-node/x/node_lifecycle/demo.pc","t":17')
    in_flight = stream.read_bytes()
    try:
        tail, _ = ask(supervisor, "journal_tail", {})
        after = stream.read_bytes()
    finally:
        stream.write_bytes(committed)

    rows = cast(list[Document], cast(Document, tail["value"])["rows"])
    lifecycle = [row for row in rows if row["kind"] == "node_lifecycle"]
    assert [cast(Document, row["body"])["event"] for row in lifecycle] == ["start"]
    assert after == in_flight


@pytest.mark.parametrize(
    "service", ["qmx/trading-node-keys", "qmx/Trading-Node-KEYS", "qmx/node-abcd2345-ctrader"]
)
def test_install_refuses_another_app_that_names_a_trading_grant_secret(
    tmp_path: Path, service: str
) -> None:
    source = tmp_path / "keys-reader"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    manifest = source / "app.toml"
    manifest.write_text(
        manifest.read_text().replace(
            "[capabilities]\n", f'[capabilities]\nsecrets = {{ KEYS = "{service}" }}\n'
        )
    )
    owner = Supervisor(tmp_path / "home")
    try:
        with pytest.raises(AppError) as refused:
            owner.install(source, trust="first_party")
    finally:
        owner.close()

    assert refused.value.code == "invalid_definition"
    assert str(refused.value) == (
        f"Only the trading-node app may name the venue trading-grant secrets; exchange-status "
        f"names {service}."
    )
