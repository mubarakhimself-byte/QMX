"""B2: every shipped app installs, starts, answers its operations and runs each job once (MA-03),
and no shipped app or template takes a core name (CA-12, Level 0 AD-30).

The walk is every folder in `examples/apps/` and `qmx-agents/apps/`. Each app installs from its
own lock into a throwaway home behind the host's own composition: a control service, a Library
store and the core landers, so QMB lands through `qmb-run` as it does at home. Every tool its
server serves is called with the example input below, and every job it declares runs once. A job
that needs an outside service runs against a local fake on 127.0.0.1, or is skipped with its
reason. Secrets come from a fixture getter, never the machine's vault.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import secrets
import shutil
import threading
import time
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import cached_property
from pathlib import Path
from typing import cast

import pytest
import uvicorn
from fastmcp import FastMCP
from pydantic import JsonValue
from qmf.core import is_refusal
from qmf.data.series import BAR_KIND, SeriesKey, SeriesStore
from qmx_control.catalog import CORE_TOOLSETS, rows
from qmx_control.service import ControlService
from qmx_engine.ledger import redact
from qmx_engine.templates.catalog import CATALOG
from qmx_host.first_start import land_dummy  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.host import (  # pyright: ignore[reportMissingTypeStubs]
    STUDY_CHECKER,
    LanderLibrary,
    landers,
    study_check,
)
from qmx_judge.conformance import run_conformance
from qmx_library.kinds import roster
from qmx_library.principal import Principal
from qmx_library.store import Store
from starlette.requests import Request
from starlette.responses import JSONResponse

from qmx_apps.errors import Document
from qmx_apps.manifest import Definition, image_files
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Stage
from qmx_apps.supervisor import Supervisor

REPO = Path(__file__).resolve().parents[4]
ROOTS = (REPO / "examples/apps", REPO / "qmx-agents/apps")
SLICES = REPO / "qml/tests/fixtures/slices"
OPERATOR = Principal("operator")
CHAT = "agent:shipped-apps"
MARCH: Document = {"window": {"start": "2025-03-01", "end": "2025-04-01"}, "allow_gaps": True}
"""QML's synthetic March 2025 month opens each forex week an hour late, so runs allow gaps."""
VAULT_FIXTURE = "shipped-apps-fixture"
NODE_KEYS = '{"schema_version": "qmx.node.keys/1"}'
SNAPSHOT: Document = {
    "observations": [
        {"exchange": "binance", "status": "operational", "observed_at": "2026-10-31T09:00:00Z"},
        {"exchange": "kraken", "status": "degraded", "observed_at": "2026-11-01T18:30:00Z"},
    ]
}
"""A weekend's recorded observations: Saturday 31 October and Sunday 1 November 2026."""


def folders() -> list[Path]:
    return [
        folder
        for root in ROOTS
        for folder in sorted(root.iterdir())
        if folder.is_dir() and not folder.name.startswith((".", "__"))
    ]


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


class Library(LanderLibrary):
    """The host's lander port with the read a conformance run adds."""

    def read(self, object_id: str) -> tuple[Mapping[str, object], bytes | None]:
        view = self.store.get(OPERATOR, object_id)
        blob = view.blobs.get("report")
        return dict(view.fields), None if blob is None else self.store.read_blob(blob.blob_id)


class Fakes:
    """An OpenAI-compatible model on 127.0.0.1 in this test process, so a job that asks a model
    never leaves the machine."""

    def __init__(self) -> None:
        self.asked: list[Document] = []
        server = FastMCP("Fixture model")

        @server.custom_route("/v1/chat/completions", methods=["POST"])
        async def chat(request: Request) -> JSONResponse:
            self.asked.append(cast(Document, await request.json()))
            answer = {"bias": "bullish", "rationale": "Fixture model read two bars."}
            return JSONResponse({"choices": [{"message": {"content": json.dumps(answer)}}]})

        _ = chat
        config = uvicorn.Config(server.http_app(path="/mcp"), host="127.0.0.1", port=0)
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 30
        while not self.server.started:
            assert time.monotonic() < deadline, "the fixture data server did not start"
            time.sleep(0.05)
        port = self.server.servers[0].sockets[0].getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"

    def close(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)


@dataclass
class Host:
    """One throwaway home as the host composes it, running one shipped app."""

    control: ControlService
    store: Store
    runtime: Supervisor
    library: Library
    home: Path

    @cached_property
    def dummy(self) -> str:
        landed = land_dummy(self.store)
        assert landed is not None
        return landed

    @cached_property
    def fakes(self) -> Fakes:
        return Fakes()

    def landed(self, run_id: str) -> Document:
        """The fields of what a run landed: its result or a check's report."""
        found = self.library.find(run_id)
        assert found is not None, f"run {run_id} landed nothing"
        return dict(self.store.get(OPERATOR, found).fields)

    def publish_signed(self, definition_hash: str, app_id: str, version: str) -> None:
        """A money app runs only once published with his signature: here, one made for the test."""
        with history(self.runtime.home, app_id) as state:
            for stage in ("tests", "sandbox", "shadow"):
                state.append(
                    Evidence(
                        definition_hash=definition_hash,
                        version=version,
                        stage=cast(Stage, stage),
                        passed=True,
                        inputs={"fixture": True},
                        versions={"definition": definition_hash},
                        results={"passed": True},
                        duration_seconds=0.1,
                    )
                )
        road = self.runtime.road
        road.signing_key(secrets.token_urlsafe(32))
        road.publish(app_id, definition_hash, signature=road.sign(app_id, definition_hash, None))


def vault(service: str, _username: str) -> str:
    return NODE_KEYS if service == "qmx/trading-node-keys" else VAULT_FIXTURE


@pytest.fixture
def host(tmp_path: Path) -> Generator[Host]:
    bars = tmp_path / "bars"
    bars.mkdir()
    for source in SLICES.glob("synthetic-*.csv"):
        shutil.copyfile(source, bars / source.name.removeprefix("synthetic-"))
    control = ControlService(tmp_path / "home", secret_getter=vault)
    control.settings_put("qmb", {"bars": str(bars)})
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as store:
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        store.register_checker(STUDY_CHECKER, study_check)
        found = Host(control, store, runtime, Library(store), tmp_path / "home")
        try:
            yield found
        finally:
            control.close()
            if "fakes" in vars(found):
                found.fakes.close()


type Arguments = Document | Callable[[Host], Document]
type Run = Callable[[Host], JsonValue]


@dataclass(frozen=True)
class Ask:
    """One operation call, its example input and what its answer holds."""

    operation: str
    arguments: Arguments
    answer: JsonValue


@dataclass(frozen=True)
class Job:
    """One job run once and what it answers, or why it is skipped here."""

    path: str
    run: Run | None
    answer: JsonValue = None
    skipped: str = ""


@dataclass(frozen=True)
class Shipped:
    asks: tuple[Ask, ...]
    jobs: tuple[Job, ...] = ()


def kept(found: JsonValue, expected: JsonValue) -> JsonValue:
    """`found` cut to the keys `expected` names, so a literal compares against what it names."""
    if isinstance(expected, dict) and isinstance(found, dict):
        return {key: kept(found[key], value) for key, value in expected.items() if key in found}
    if isinstance(expected, list) and isinstance(found, list) and len(found) == len(expected):
        return [kept(item, want) for item, want in zip(found, expected, strict=True)]
    return found


def qmb_job(kind: str, **request: JsonValue) -> Run:
    """One QMB job over the dummy and March, answered by what its run landed."""

    def run(host: Host) -> JsonValue:
        ran = host.control.app_job(
            "qmb",
            f"jobs/{kind}.py",
            inputs={"unit": host.dummy, **MARCH, **request},
            principal=CHAT,
        )
        return host.landed(str(ran["run_id"]))

    return run


def conformance(host: Host) -> JsonValue:
    """The core's own conformance pack, run on QMB's conformance job and judged by the core."""

    def run_job(
        app: str, job: str, inputs: Mapping[str, object], principal: str
    ) -> Mapping[str, object]:
        return host.runtime.run_job(
            app, job, inputs=cast(Document, dict(inputs)), principal=principal
        )

    ran = run_conformance("qmb", "1.0.6", run_job=run_job, library=host.library, principal=CHAT)
    return {"passed": ran.verdict.passed, "says": ran.verdict.says()}


def write_market(host: Host) -> None:
    """Two whole days and half a third of EURUSD M1 bid bars in the host's market store, written
    by the store's own writer. Every minute of day `d` closes at 1.08 + 0.001 d."""
    rows: list[tuple[object, ...]] = []
    for day, minutes in ((10, 1_440), (11, 1_440), (12, 720)):
        start = int(datetime(2025, 3, day, tzinfo=UTC).timestamp()) * 1_000
        price = 108_000 + 100 * day
        rows += [(start + m * 60_000, price, price, price, price, 1.0) for m in range(minutes)]
    key = SeriesKey.try_create("fixture", "EURUSD", BAR_KIND, 2025, 3, "bid")
    assert not is_refusal(key), key
    committed = SeriesStore(host.runtime.home / "market/series").commit(key.value, rows)
    assert not is_refusal(committed), committed


def daily_bias(host: Host) -> JsonValue:
    """The instance pointed at a fixture market and the fixture model, then its daily job once."""
    write_market(host)
    settings = host.home / "apps/macro-daily-bias/data/config.json"
    settings.write_text(
        json.dumps(
            {
                "market": "fixture/EURUSD/bar-m1/bid",
                "bars": 2,
                "model": "fixture-model",
                "model_url": f"{host.fakes.url}/v1",
            }
        ),
        encoding="utf-8",
    )
    ran = host.runtime.run_job("macro-daily-bias", "daily.py")
    [request] = host.fakes.asked
    system, user = cast(list[Document], request["messages"])
    return {
        "job": ran["job"],
        "model": request["model"],
        "response_format": request["response_format"],
        "prompt": str(system["content"]).splitlines()[0],
        "snapshot": json.loads(str(user["content"])),
        "bias": host.runtime.call("macro-daily-bias", "bias", {})["result"],
    }


ARTICLES = (623, 624, 625)
"""Three seeded ids, each archived as the one saved MQL5 page."""


def write_archive(host: Host) -> None:
    """The recovered archive the README says to copy into the instance's `data/seed`."""
    seed = host.home / "apps/mql5-articles/data/seed"
    (seed / "md").mkdir(parents=True)
    (seed / "raw").mkdir()
    page = gzip.compress((Path(__file__).with_name("fixtures") / "mql5-623.html").read_bytes())
    lines: list[str] = []
    for article in ARTICLES:
        markdown = f"# Article {article}\n"
        (seed / f"md/{article}.md").write_text(markdown, encoding="utf-8")
        (seed / f"raw/{article}.html.gz").write_bytes(page)
        url = f"https://www.mql5.com/en/articles/{article}"
        digest = hashlib.sha256(markdown.encode()).hexdigest()
        row = {"id": article, "url": url, "title": f"Article {article}", "sha256": digest}
        lines.append(json.dumps({**row, "fetch_status": "ok"}))
    (seed / "catalog.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    config = host.home / "apps/mql5-articles/data/config.json"
    config.write_text(json.dumps({"crawl": False}), encoding="utf-8")


def library_articles(host: Host) -> list[str]:
    """The artifact sha256 of each Library item an article landed as, one row per item."""
    rows = host.store.catalog.db.execute(
        "SELECT DISTINCT item, json_extract(fields, '$.metadata.sha256') FROM objects "
        "WHERE kind = 'artifact' AND json_extract(fields, '$.type') = 'mql5-article'"
    ).fetchall()
    return sorted(str(sha) for _, sha in rows)


def daily_articles(host: Host) -> JsonValue:
    """The archive seeded with three articles and the crawl off, then the daily job twice: the
    first lands one Library item per article, the second lands nothing new."""
    write_archive(host)
    first = host.runtime.run_job("mql5-articles", "jobs/daily.py")
    again = host.runtime.run_job("mql5-articles", "jobs/daily.py")
    refs = [cast(Document, ref) for ref in cast(list[JsonValue], first["artifact_refs"])]
    return {
        "first": first["result"],
        "again": again["result"],
        "landed": [len(refs), len(cast(list[JsonValue], again["artifact_refs"]))],
        "one_item_per_article": library_articles(host)
        == sorted(str(ref["sha256"]) for ref in refs),
        "status": host.runtime.call("mql5-articles", "status", {})["result"],
    }


def weekend_snapshot(host: Host) -> Document:
    """The exchange-status example's `snapshot` output, landed as that app lands it."""
    producer = Definition.load(ROOTS[0] / "exchange-status")
    return {"snapshot": host.runtime.artifacts.save(producer, "snapshot", SNAPSHOT)}


def node_deployment(host: Host) -> Document:
    status = cast(Document, host.runtime.call("trading-node", "status", {})["result"])
    tag = cast(Document, cast(Document, status["value"])["identity"])["tag"]
    fingerprint = "fp1:sha256:" + "a" * 64
    return {
        "deployment": {
            "schema_version": "qmx.node.deployment/1",
            "deployment_id": "dep-1",
            "node": {"tag": tag},
            "unit": {"id": "dummy", "version": 1},
            "unit_document": {"markets": [{"market_id": "fx.eurusd"}]},
            "markets": [{"market_id": "fx.eurusd"}],
            "starting": {"source": "defaults", "values": {}},
            "compiled_fingerprint": fingerprint,
            "g_record": {"compiled_fingerprint": fingerprint},
            "files": [],
            "account": {"id": "demo-1"},
            "snapshots": [],
            "lane": "paper",
        }
    }


OK: JsonValue = {"ok": True}


def refused(code: str) -> JsonValue:
    return {"ok": False, "code": code}


FINISHED: JsonValue = {"status": "finished", "tester": {"app": "qmb", "version": "1.0.6"}}
EXAMPLES: Mapping[str, Shipped] = {
    "exchange-status": Shipped(
        asks=(
            Ask(
                "record",
                {"exchange": "binance", "status": "operational", "observed_at": "2026-10-31"},
                {"recorded": True},
            ),
            Ask(
                "snapshot",
                {},
                {
                    "output": "snapshot",
                    "data": {
                        "observations": [
                            {
                                "exchange": "binance",
                                "status": "operational",
                                "observed_at": "2026-10-31",
                            }
                        ]
                    },
                },
            ),
        )
    ),
    "macro-daily-bias": Shipped(
        asks=(Ask("bias", {}, {"status": "awaiting_data"}),),
        jobs=(
            Job(
                "daily.py",
                daily_bias,
                {
                    "job": "daily.py",
                    "model": "fixture-model",
                    "response_format": {"type": "json_object"},
                    "prompt": "Summarise the macro drivers in the supplied qmx-data snapshot.",
                    "snapshot": {
                        "as_of": "2025-03-11T00:00Z",
                        "bars": [
                            {"t": "2025-03-10T00:00Z", "close": "1.09000"},
                            {"t": "2025-03-11T00:00Z", "close": "1.09100"},
                        ],
                        "source": "fixture/EURUSD/bar-m1/bid",
                    },
                    "bias": {
                        "output": "bias",
                        "data": {
                            "bias": "bullish",
                            "rationale": "Fixture model read two bars.",
                            "as_of": "2025-03-11T00:00Z",
                            "source": "qmx-data",
                        },
                    },
                },
            ),
        ),
    ),
    "mql5-articles": Shipped(
        asks=(
            Ask("status", {}, {"known": 3057, "available": 0, "pending_publication": 0}),
            Ask("seed_library", {"limit": 5}, {"imported": 0}),
            Ask("article", {"article_id": 623}, {"available": False}),
        ),
        jobs=(
            Job(
                "jobs/daily.py",
                daily_articles,
                {
                    "first": {"seeded": 3, "landed": 0, "fetched": 0},
                    "again": {"seeded": 0, "landed": 3, "fetched": 0},
                    "landed": [3, 0],
                    "one_item_per_article": True,
                    "status": {"known": 3057, "available": 3, "pending_publication": 0},
                },
            ),
        ),
    ),
    "weekend-watcher": Shipped(
        asks=(
            Ask(
                "summarize",
                weekend_snapshot,
                {
                    "output": "summary",
                    "data": {
                        "summary": "Recorded-data fixture: binance: operational "
                        "(2026-10-31T09:00:00Z); kraken: degraded (2026-11-01T18:30:00Z)",
                        "source_sha256": "8b90c8b50c4b4f9ff54351528a9366199f71d910a349d757b2e3594"
                        "3f36d0b4c",
                        "mode": "recorded_fixture",
                    },
                },
            ),
        )
    ),
    "mis": Shipped(
        asks=(
            Ask(
                "status",
                {},
                {
                    "ok": True,
                    "value": {
                        "state": "not configured",
                        "holdout": {"on": True, "seals": "every month"},
                        "markets": [],
                        "last_round": None,
                    },
                },
            ),
            Ask(
                "configure",
                {"markets": []},
                {"ok": True, "value": {"configured": 0, "refused": []}},
            ),
            Ask("round", {}, {"ok": True, "value": {"published": [], "sealed_months": []}}),
            Ask("board", {}, {"ok": True, "value": {"boards": []}}),
        )
    ),
    "qmb": Shipped(
        asks=(
            Ask(
                "capabilities",
                {},
                {
                    "contract": "qmb/1",
                    "tester": {"app": "qmb", "version": "1.0.6"},
                    "fidelities": ["quotes"],
                    "instrument_classes": ["fx", "metal"],
                },
            ),
            Ask(
                "instruments", {}, {"instrument_classes": ["fx", "metal"], "fidelities": ["quotes"]}
            ),
        ),
        jobs=(
            Job("jobs/backtest.py", qmb_job("backtest"), {**FINISHED, "measures": {"trades": 8}}),
            Job(
                "jobs/behaviour_check.py",
                qmb_job("behaviour_check"),
                {"check": "qml-g/1", "safety": {"verdict": "pass"}},
            ),
            Job("jobs/conformance.py", conformance, {"passed": True}),
            Job(
                "jobs/sweep.py",
                qmb_job("sweep", grid={"numbers": {"ema_period": ["100"]}}),
                {**FINISHED, "measures": {"cells": 1, "trades": 8}},
            ),
            Job("jobs/walk_forward.py", qmb_job("walk_forward", split={"folds": 2}), FINISHED),
            Job("jobs/robustness.py", qmb_job("robustness", battery=["cost_stress"]), FINISHED),
            Job(
                "jobs/optimize.py",
                qmb_job("optimize", ranges={"ema_period": ["100", "101"]}, segments=2),
                FINISHED,
            ),
            Job(
                "jobs/whatif.py",
                qmb_job("whatif", scenarios=[{"name": "cost_shock", "params": {}}]),
                FINISHED,
            ),
            Job(
                "jobs/replay_check.py",
                qmb_job("replay_check", day="2025-03-12", live=[]),
                FINISHED,
            ),
        ),
    ),
    "trading-node": Shipped(
        asks=(
            Ask("status", {}, {"ok": True, "value": {"headline": "Ready, no units yet"}}),
            Ask("units", {"deployment_id": "dep-none"}, OK),
            Ask("positions", {"account": "demo-1"}, OK),
            Ask("journal_tail", {"after_sequence": -1, "streams": ["node"]}, OK),
            Ask("passport", {}, OK),
            Ask("deployments", {}, OK),
            Ask("deploy", node_deployment, OK),
            Ask("withdraw", {"deployment_id": "dep-none"}, refused("unknown_deployment")),
            Ask("pause", {"scope": {"account": "demo-1"}}, OK),
            Ask("resume", {"scope": {"account": "demo-1"}}, OK),
            Ask("kill", {"level": "YELLOW", "scope": {"account": "demo-1"}}, OK),
            Ask("flatten", {"scope": {"account": "demo-1"}}, OK),
            Ask("bind", {"account": {"id": "demo-1"}, "action": "add"}, refused("not_set_up")),
            Ask("confirm_same_node", {}, OK),
            Ask(
                "take_over",
                {"old_tag": "abcdefgh", "confirmed_gone": True},
                refused("not_available"),
            ),
            Ask("sign_in_begin", {"venue": "ctrader"}, refused("not_set_up")),
            Ask("sign_in_code", {"code": "fixture-code"}, refused("not_set_up")),
            Ask("self_test", {"account": "demo-1"}, refused("not_set_up")),
            Ask("records", {"account": "demo-1", "symbols": ["EURUSD"]}, refused("not_set_up")),
            Ask("rotate_keys", {}, OK),
        )
    ),
}


def asked(app: str) -> set[str]:
    return {ask.operation for ask in EXAMPLES[app].asks}


def install_and_start(host: Host, folder: Path) -> Definition:
    definition = Definition.load(folder)
    manifest = definition.manifest
    installed = host.runtime.install(folder, trust="first_party")
    if manifest.risk == "money":
        host.publish_signed(str(installed["definition_hash"]), manifest.id, manifest.version)
    host.runtime.start(manifest.id)
    return definition


@pytest.mark.parametrize("folder", folders(), ids=lambda folder: folder.name)
def test_each_shipped_app_installs_starts_answers_and_runs_each_job_once(
    host: Host, folder: Path
) -> None:
    definition = install_and_start(host, folder)
    app = definition.manifest.id
    shipped = EXAMPLES[app]
    [tools] = [entry["tools"] for entry in host.runtime.registry() if entry["app_id"] == app]

    assert {str(tool["name"]) for tool in cast(list[Document], tools)} == asked(app)
    for ask in shipped.asks:
        arguments = ask.arguments(host) if callable(ask.arguments) else ask.arguments
        answer = host.runtime.call(app, ask.operation, arguments)["result"]
        assert kept(answer, ask.answer) == ask.answer, (app, ask.operation, answer)
    for job in shipped.jobs:
        if job.run is not None:
            answer = job.run(host)
            assert kept(answer, job.answer) == job.answer, (app, job.path, answer)

    status = host.runtime.status(app)
    assert (status["status"], cast(Document, status["metrics"])["errors"]) == ("running", 0)


def test_the_walk_finds_seven_apps_with_an_example_for_every_operation_and_job() -> None:
    found = {folder.name: Definition.load(folder).manifest for folder in folders()}
    skipped = {
        (app, job.path): job.skipped
        for app, shipped in EXAMPLES.items()
        for job in shipped.jobs
        if job.run is None
    }

    assert sorted(found) == [
        "exchange-status",
        "macro-daily-bias",
        "mis",
        "mql5-articles",
        "qmb",
        "trading-node",
        "weekend-watcher",
    ]
    assert all(manifest.id == name for name, manifest in found.items())
    unasked = {app: sorted(set(found[app].operations) - asked(app)) for app in found}
    assert unasked == {app: [] for app in found}
    assert {app: [job.path for job in EXAMPLES[app].jobs] for app in found} == {
        app: manifest.entrypoints.jobs for app, manifest in found.items()
    }
    assert list(skipped) == []


APP_VERSIONS: Mapping[tuple[str, str], str] = {
    ("exchange-status", "1.0.0"): "65bd42b6f9d29881ca7d19393598a9fc",
    ("macro-daily-bias", "1.0.0"): "32f669c81be8b9c9a201d20dd9c272ed",
    ("mis", "1.0.0"): "da97997e2a7f1b83f9362a5039930ca9",
    ("mql5-articles", "1.0.0"): "dc86e07abe3b8b4442bdc4eeaa758110",
    ("qmb", "1.0.0"): "b03c2aca41f2e67d1689522f9ffab2a9",
    ("qmb", "1.0.1"): "abc0f0534c36dc9fc15afe8e2d95c852",
    ("qmb", "1.0.2"): "0bcae551c39204b5cad1128d9bba3163",
    ("qmb", "1.0.3"): "148ef6df97946bd6eb6d91c40a685b41",
    ("qmb", "1.0.4"): "43b0f1317da933c857813ba211e47a7c",
    ("qmb", "1.0.5"): "49ede0d9c1f5c067e660f81930f9f14d",
    ("qmb", "1.0.6"): "ecbf2b7b1ff3393169c209878a7b615b",
    ("trading-node", "0.1.0"): "474d301af9fc35f3352c3230faf4bb63",
    ("trading-node", "0.1.1"): "2feb6ee2e0d9cf2bd80666e58c175cae",
    ("trading-node", "0.1.2"): "2ecec90e00d3c17cffdc3ffffa49242c",
    ("trading-node", "0.1.3"): "71e37db09841e68f226bc896d5cb82b1",
    ("trading-node", "0.1.4"): "df7a96d184e1a90856b511fd8f12a038",
    ("trading-node", "0.1.5"): "c0d6763240096886de9225ae33f3684c",
    ("trading-node", "0.1.6"): "3a014611d3fb4c1c9557b9d03952e736",
    ("weekend-watcher", "1.0.0"): "2fd02bee829dbbb04b5f0a66dafe66cf",
}
"""One row per app and version, append-only. A change anywhere in an app's folder moves its image
hash, and the same version with new bytes answers `immutable_version` at his next start, so the
change needs a new version in its `app.toml` and a new row here."""


def folder_digest(folder: Path) -> str:
    """A folder's bytes with `\\r\\n` read as `\\n`, because `image_hash` reads raw bytes and
    `core.autocrlf` is true on this PC, so raw hashes would fail on any other checkout."""
    digest = hashlib.sha256()
    for path in image_files(folder):
        name = path.relative_to(folder).as_posix().encode()
        content = path.read_bytes().replace(b"\r\n", b"\n")
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()[:32]


def test_a_changed_app_folder_has_a_new_version_row(tmp_path: Path) -> None:
    unix, windows = tmp_path / "unix", tmp_path / "windows"
    unix.mkdir()
    windows.mkdir()
    (unix / "server.py").write_bytes(b"one\ntwo\n")
    (windows / "server.py").write_bytes(b"one\r\ntwo\r\n")
    same_on_both = folder_digest(unix) == folder_digest(windows)
    (windows / "server.py").write_bytes(b"one\r\nthree\r\n")
    an_edit_moves_it = folder_digest(unix) != folder_digest(windows)

    shipped = {
        (manifest.id, manifest.version): folder_digest(folder)
        for folder in folders()
        for manifest in [Definition.load(folder).manifest]
    }
    moved = {row: found for row, found in shipped.items() if APP_VERSIONS.get(row) != found}

    assert (same_on_both, an_edit_moves_it) == (True, True)
    assert moved == {}, "An app folder changed: bump its app.toml version and add a row."


def separators(name: str) -> str:
    return name.casefold().replace("_", "-")


def core_names() -> dict[str, str]:
    """Every name the core holds apart from its templates, by one spelling of its separators:
    the Library's kinds, the core toolsets and the catalog rows."""
    names = {separators(kind): f"the core kind {kind}" for kind in roster()}
    names |= {separators(name): f"the core toolset {name}" for name in CORE_TOOLSETS}
    return names | {separators(row.name): f"the catalog row {row.name}" for row in rows()}


def template_names() -> list[tuple[str, str]]:
    """Each workflow template's id and folder."""
    return [("template", name) for found in CATALOG for name in (found.id, found.folder)]


def collisions(shipped: list[tuple[str, str]], core: Mapping[str, str]) -> list[str]:
    """Each shipped name that a core name already holds, said in a sentence."""
    return [
        f"{what} {name} takes {core[separators(name)]}"
        for what, name in shipped
        if separators(name) in core
    ]


def shipped_names() -> list[tuple[str, str]]:
    """Each app id and each provides name of every shipped app. A provides that names a core
    lander is the core's own record, which the lander lands, so it keeps the core's name."""
    found: list[tuple[str, str]] = []
    for folder in folders():
        manifest = Definition.load(folder).manifest
        found.append(("app", manifest.id))
        found += [
            (f"{manifest.id}'s provides", name)
            for name, contract in manifest.provides.items()
            if contract.lander is None
        ]
    return found


def test_no_shipped_app_or_template_takes_a_core_name() -> None:
    core = core_names()
    templates = {separators(name): f"the template {name}" for _, name in template_names()}

    assert collisions(shipped_names(), core | templates) == []
    assert collisions(template_names(), core) == []
    assert collisions(
        [("app", "library"), ("app", "Backtest_Result"), ("template", "backtest_run")], core
    ) == [
        "app library takes the core toolset library",
        "app Backtest_Result takes the core kind backtest-result",
        "template backtest_run takes the catalog row backtest_run",
    ]
