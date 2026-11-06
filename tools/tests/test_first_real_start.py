"""The first real start's script, run as he runs it, against a fake host on a loopback port.

No keyring is touched: a rehearsal's bearer is in a throwaway store file, and real mode's is
injected. The git checks run on throwaway repositories.
"""

from __future__ import annotations

import json
import subprocess
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit

import first_real_start as script
import pytest

BEARER = "fixture-bearer"
UNIT = "demo-unit"
LINES = (
    "folder found",
    "practice node Ready",
    "demo session ready",
    "test trade with its stop placed, seen and closed",
    "passport landed",
    "unit deployed on the chosen market",
    "node journal rows in This PC's store",
    "test trade rows in This PC's store",
)
DEPLOY = LINES[5]
PLAIN = "no unit has passed the judge yet, so nothing was deployed"
DEPLOYMENT = "dep-1"
TAG = "abcd1234"
SETUP_CHECKS = [
    {"name": "clock band", "ok": False, "value": "warn"},
    {"name": "disk", "ok": True, "value": 70355161088},
]


@dataclass
class FakeHost:
    """The routes the script calls, as the real host answers them. `venue_up` is the fake
    cTrader's state, and the other fields are what a test turns."""

    home: Path
    venue_up: bool = True
    connect_cards: list[str] = field(default_factory=list[str])
    session: str = "signed_out"
    bound: list[str] = field(default_factory=list[str])
    node_checks: list[dict[str, object]] = field(default_factory=list[dict[str, object]])
    passport_at: str | None = None
    order_rows: int = 0
    lifecycle_rows: int = 2
    keep_deploy: bool = True
    deploy_states: list[str] = field(default_factory=lambda: ["compiling", "trading"])
    """The states the node's `deployments` read answers, in turn; the last one repeats."""
    deploy_reads: int = 0
    refused_detail: str = ""
    word: str = "Ready"
    promote_refusal: dict[str, object] | None = None
    harvest: bool = True
    asked: list[str] = field(default_factory=list[str])
    bodies: list[Any] = field(default_factory=list[Any])

    def answer(self, method: str, path: str, query: dict[str, str], body: Any) -> tuple[int, Any]:
        self.asked.append(f"{method} {path}")
        self.bodies.append(body)
        if path == "/api/health":
            return 200, {"status": "ok", "pid": 4242, "read_only": []}
        if path == "/api/connect/jobs":
            return 202, self._job(body)
        if path == "/api/apps/trading-node":
            return 200, {"definition_hash": "h" * 64, "road": {"active": None}}
        if path == "/api/apps/trading-node/sign":
            return 200, {"signature": f"signed-{query['definition_hash'][:4]}"}
        if path.startswith("/api/keys/"):
            return 204, None
        if path.startswith("/api/apps/trading-node/tools/"):
            return 200, {"result": self._node(path.rsplit("/", 1)[1], body)}
        if path == "/api/library":
            return 200, [
                {
                    "id": "unit-old",
                    "kind": "unit",
                    "version": 1,
                    "content": {"unit_id": UNIT},
                },
                {
                    "id": "unit-new",
                    "kind": "unit",
                    "version": 2,
                    "content": {"unit_id": UNIT},
                },
                {"id": "note", "kind": "note", "version": 9, "content": {}},
            ]
        if path == "/api/units/promote":
            if self.promote_refusal is not None:
                return 409, self.promote_refusal
            return 200, {
                "ok": True,
                "value": {"deployment_id": DEPLOYMENT, "node_answer": "accepted"},
            }
        if path == "/api/settings/records":
            return 200, {"open_harvest_s": 60}
        if path == "/api/data/card":
            return self._card(query["series"])
        return 404, {"detail": f"no route {path}"}

    def _job(self, body: Any) -> dict[str, object]:
        fields = cast("dict[str, object]", body["answer"].get("fields") or {})
        if "signature" in fields:
            self.connect_cards = [card for card in self.connect_cards if card != "signature"]
        if "client_id" in fields:
            self.connect_cards = [card for card in self.connect_cards if card != "ctrader-app"]
        needs = None
        if self.connect_cards:
            needs = {"card": self.connect_cards[0], "line": f"card {self.connect_cards[0]}"}
        elif self.session in script.SIGNED_OUT:
            needs = {"card": "sign-in", "line": "sign in"}
        (self.home / "data").mkdir(exist_ok=True)
        (self.home / script.PASSPORT).write_text(
            json.dumps({"checks": [*self.node_checks, *SETUP_CHECKS]}), "utf-8"
        )
        return {
            "id": "job-1",
            "state": "finished",
            "needs": needs,
            "result": {"lines": ["records: account 4401, 4 landed on main, 0 unchanged"]},
        }

    def _node(self, operation: str, body: Any) -> dict[str, object]:
        if operation == "status":
            venue = {
                "venue": "ctrader",
                "environment": "demo",
                "session": self.session,
                "accounts": self.bound,
                "reason": None if self.venue_up else "the venue did not answer",
            }
            return {
                "ok": True,
                "value": {
                    "word": self.word,
                    "headline": f"{self.word}, no units yet",
                    "reasons": [],
                    "identity": {"tag": TAG},
                    "venues": [venue],
                },
            }
        if operation == "sign_in_begin":
            return {"ok": True, "value": {"url": "https://id.example.invalid/consent"}}
        if operation == "sign_in_code":
            if not self.venue_up:
                return {"ok": False, "code": "sign_in_refused", "message": "cTrader refused it"}
            self.session = "signed_in"
            return {
                "ok": True,
                "value": {"accounts": [{"account": "4401", "is_live": False}], "kept": True},
            }
        if operation == "bind":
            self.bound, self.session = [str(body["account"]["id"])], "ready"
            return {"ok": True, "value": {"world": "demo", "state": "bound"}}
        if operation == "self_test":
            self.passport_at = f"at-{len(self.asked)}"
            self.node_checks = [
                {
                    "name": name,
                    "ok": True,
                    "value": {"entry": "1.08012", "stop": "1.07512", "exit": "1.08"},
                }
                for name in script.SELF_TEST_CHECKS
            ]
            self.order_rows += 3 if self.harvest else 0
            return {"ok": True, "value": {"state": "accepted"}}
        if operation == "passport":
            return {"ok": True, "value": {"checks": self.node_checks, "at": self.passport_at}}
        if operation == "deployments":
            self.deploy_reads += 1
            if not self.keep_deploy:
                return {"ok": True, "value": []}
            state = self.deploy_states[min(self.deploy_reads - 1, len(self.deploy_states) - 1)]
            return {
                "ok": True,
                "value": [
                    {"deployment_id": DEPLOYMENT, "state": state, "detail": self.refused_detail}
                ],
            }
        return {"ok": False, "code": "unknown_operation", "message": operation}

    def _card(self, series: str) -> tuple[int, Any]:
        rows = {
            f"journal-node/{TAG}/order/demo.pc": self.order_rows,
            f"journal-node/{TAG}/node_lifecycle/demo.pc": self.lifecycle_rows,
        }.get(series, 0)
        if not rows:
            return 404, {"detail": "no series is stored under this name"}
        return 200, {"partitions": [{"month": "2026-11", "rows": rows, "frozen": False}]}


@dataclass
class Rig:
    host: FakeHost
    port: int
    home: Path
    store: Path
    ticks: list[float] = field(default_factory=lambda: [0.0])

    def sleep(self, seconds: float) -> None:
        self.ticks[0] += seconds

    def monotonic(self) -> float:
        return self.ticks[0]

    def rehearse(self, *more: str) -> int:
        return script.main(
            [
                "--rehearsal",
                "--home",
                str(self.home),
                "--store",
                str(self.store),
                "--port",
                str(self.port),
                *more,
            ],
            monotonic=self.monotonic,
            sleep=self.sleep,
        )


@pytest.fixture
def rig(tmp_path: Path) -> Iterator[Rig]:
    home = tmp_path / "QMX"
    home.mkdir()
    (home / script.LABEL).write_text("format = 'qmx-home'\n", "utf-8")
    store = tmp_path / "keyring.json"
    store.write_text(
        json.dumps(
            {
                "qmx/control-token|control-token": BEARER,
                "rehearsal/app|client_id": "fixture-app",
                "rehearsal/app|client_secret": "fixture-app-value",
                "rehearsal/code|code": "fixture-code",
            }
        ),
        "utf-8",
    )
    fake = FakeHost(home)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            del format, args

        def _serve(self) -> None:
            size = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(size) if size else b""
            parts = urlsplit(self.path)
            query = {name: values[0] for name, values in parse_qs(parts.query).items()}
            if self.headers.get("Authorization") != f"Bearer {BEARER}":
                status, body = 401, {"detail": "not this host's bearer"}
            else:
                status, body = fake.answer(
                    self.command, parts.path, query, json.loads(raw) if raw else None
                )
            self.send_response(status)
            self.end_headers()
            if status != 204:
                self.wfile.write(json.dumps(body).encode("utf-8"))

        do_GET = _serve
        do_POST = _serve
        do_PUT = _serve

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield Rig(fake, server.server_address[1], home, store)
    server.shutdown()
    server.server_close()


def verdicts(out: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith(("PASS ", "FAIL ")):
            name = line[5:].split(":", 1)[0]
            found[name] = line[:4]
    return found


def said(out: str, name: str) -> str:
    return next(line for line in out.splitlines() if line[5:].startswith(f"{name}:"))


def step_lines(out: str) -> list[str]:
    """Every step's line in order, with the plain note where the deploy step sits."""
    found: list[str] = []
    for line in out.splitlines():
        if line.startswith(("PASS ", "FAIL ")):
            found.append(line[5:].split(":", 1)[0])
        elif line == PLAIN:
            found.append(PLAIN)
    return found


def test_a_healthy_rehearsal_prints_one_pass_per_fact_in_order_and_exits_0(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    code = rig.rehearse()
    out = capsys.readouterr().out
    assert code == 0
    assert step_lines(out) == [*LINES[:5], PLAIN, *LINES[6:]]
    assert set(verdicts(out).values()) == {"PASS"}
    assert said(out, LINES[3]) == (
        "PASS test trade with its stop placed, seen and closed: "
        "entry 1.08012, stop 1.07512, exit 1.08"
    )
    assert said(out, LINES[4]) == (
        "PASS passport landed: 5 self-test checks ok, clock band warn; "
        "records: account 4401, 4 landed on main, 0 unchanged"
    )
    assert "METRIC seconds end to end: " in out


def test_with_no_unit_named_it_prints_the_plain_line_and_exits_zero(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    code = rig.rehearse()
    out = capsys.readouterr().out
    assert code == 0
    assert PLAIN == "no unit has passed the judge yet, so nothing was deployed"
    assert PLAIN in out.splitlines()
    assert [line for line in out.splitlines() if line.startswith("FAIL ")] == []
    assert "POST /api/units/promote" not in rig.host.asked


def test_his_click_names_the_market_the_newest_version_of_the_unit_he_names_and_the_bound_account(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    assert rig.rehearse("--market", "metal.xauusd", "--unit", UNIT) == 0
    capsys.readouterr()
    click = rig.host.bodies[rig.host.asked.index("POST /api/units/promote")]
    assert click == {
        "schema_version": "qmx.units.promote/1",
        "op_id": "first-start-metal.xauusd",
        "unit": {"id": UNIT, "version": "unit-new"},
        "market_id": "metal.xauusd",
        "to": "paper",
        "node": {"tag": TAG},
        "account": {"id": "4401"},
    }


def test_with_the_venue_down_only_the_venue_lines_fail_and_it_exits_1(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.venue_up = False
    code = rig.rehearse()
    out = capsys.readouterr().out
    assert code == 1
    assert verdicts(out) == {
        "folder found": "PASS",
        "practice node Ready": "PASS",
        "demo session ready": "FAIL",
        "test trade with its stop placed, seen and closed": "FAIL",
        "passport landed": "FAIL",
        "node journal rows in This PC's store": "PASS",
        "test trade rows in This PC's store": "FAIL",
    }
    assert said(out, "demo session ready") == (
        "FAIL demo session ready: the sign-in did not finish (sign_in_refused: cTrader refused it)"
    )
    assert PLAIN in out.splitlines()


def test_a_node_that_refuses_is_a_fail_in_its_own_words(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.deploy_states = ["refused"]
    rig.host.refused_detail = (
        "the unit would not start: invalid input: a starting value lies inside its range"
    )
    assert rig.rehearse("--unit", UNIT) == 1
    assert said(capsys.readouterr().out, DEPLOY) == (
        "FAIL unit deployed on the chosen market: the node reads refused: "
        "the unit would not start: invalid input: a starting value lies inside its range"
    )


def test_compiling_is_not_a_pass(rig: Rig, capsys: pytest.CaptureFixture[str]) -> None:
    rig.host.deploy_states = ["compiling"]
    assert rig.rehearse("--unit", UNIT) == 1
    out = capsys.readouterr().out
    assert said(out, DEPLOY) == (
        "FAIL unit deployed on the chosen market: the node left dep-1 at compiling for 120 s"
    )
    assert rig.host.deploy_reads > 1


def test_a_promote_answer_the_node_does_not_hold_fails_the_deploy_line(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.keep_deploy = False
    code = rig.rehearse("--unit", UNIT)
    out = capsys.readouterr().out
    assert code == 1
    assert said(out, DEPLOY) == (
        "FAIL unit deployed on the chosen market: "
        "the node holds no deployment dep-1, whatever the promote answered"
    )


def test_a_refused_promote_says_why_and_what_to_do(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.promote_refusal = {
        "ok": False,
        "code": "no_g_record",
        "message": "no G test-report for compiled fingerprint fp1",
        "next_step": "Run the behaviour check on this version.",
    }
    assert rig.rehearse("--unit", UNIT) == 1
    assert said(capsys.readouterr().out, DEPLOY) == (
        "FAIL unit deployed on the chosen market: the promote was refused: "
        "no G test-report for compiled fingerprint fp1 Run the behaviour check on this version."
    )


def test_the_reader_follows_keyrings_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    """The four rows of `ground-start.md` block J, on an in-memory store that moves an entry to
    `user@service` exactly as keyring's Windows backend does, each giving keyring's literal value."""
    service, user = script.BEARER_SERVICE, script.BEARER_USER
    compound = f"{user}@{service}"
    store: dict[str, tuple[str, str]] = {}

    def write(target: str, owner: str, value: str) -> None:
        if target == service and service in store:
            previous = store[service]
            store[f"{previous[0]}@{service}"] = previous
        store[target] = (owner, value)

    def read(target: str) -> tuple[str | None, str | None]:
        return store.get(target, (None, None))

    monkeypatch.setattr(script, "_credential", read)
    assert script.real_bearer() is None
    write(service, user, "first")
    assert script.real_bearer() == "first"
    write(service, user, "second")
    assert script.real_bearer() == "second"
    write(service, "someone-else", "other")
    assert store[compound] == (user, "second")
    assert script.real_bearer() == "second"
    del store[service]
    assert script.real_bearer() == "second"


def test_a_passport_with_a_bad_check_names_it(rig: Rig, capsys: pytest.CaptureFixture[str]) -> None:
    original = rig.host._job  # pyright: ignore[reportPrivateUsage]

    def feed_stale(body: Any) -> dict[str, object]:
        job = original(body)
        path = rig.home / script.PASSPORT
        held = json.loads(path.read_text("utf-8"))
        held["checks"] = [
            {**row, "ok": False} if row["name"] == "feed freshness" else row
            for row in held["checks"]
        ]
        path.write_text(json.dumps(held), "utf-8")
        return job

    rig.host._job = feed_stale  # type: ignore[method-assign]
    assert rig.rehearse() == 1
    assert said(capsys.readouterr().out, LINES[4]) == (
        "FAIL passport landed: the passport landed and these checks are not ok: feed freshness"
    )


def test_rows_that_never_reach_the_store_fail_at_the_harvest_limit_plus_a_minute(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.harvest = False
    assert rig.rehearse() == 1
    assert said(capsys.readouterr().out, LINES[7]) == (
        "FAIL test trade rows in This PC's store: "
        "the test trade's rows did not reach the store in 120 s"
    )


def test_the_cards_are_answered_through_the_key_route_and_the_sign_route_and_stay_out_of_the_output(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.connect_cards = ["signature", "ctrader-app"]
    assert rig.rehearse() == 0
    out = capsys.readouterr().out
    key = rig.host.asked.index(f"PUT /api/keys/{script.APP_SECRET_KEY}")
    assert rig.host.bodies[key] == {"value": "fixture-app-value"}
    answers = [
        body["answer"]
        for ask, body in zip(rig.host.asked, rig.host.bodies, strict=True)
        if ask == "POST /api/connect/jobs"
    ]
    assert answers[:3] == [
        {},
        {"fields": {"signature": "signed-hhhh"}},
        {"fields": {"client_id": "fixture-app"}},
    ]
    assert "fixture-app-value" not in out and "fixture-code" not in out and BEARER not in out


def test_a_second_run_converges_without_a_second_sign_in_or_bind(
    rig: Rig, capsys: pytest.CaptureFixture[str]
) -> None:
    assert rig.rehearse() == 0
    rig.host.asked.clear()
    assert rig.rehearse() == 0
    assert set(verdicts(capsys.readouterr().out).values()) == {"PASS"}
    tools = [ask.rsplit("/", 1)[1] for ask in rig.host.asked if "/tools/" in ask]
    assert "sign_in_code" not in tools and "bind" not in tools
    assert tools.count("self_test") == 1


def test_a_wrong_bearer_fails_the_folder_line(rig: Rig, capsys: pytest.CaptureFixture[str]) -> None:
    held = json.loads(rig.store.read_text("utf-8"))
    held["qmx/control-token|control-token"] = "another-folders-bearer"
    rig.store.write_text(json.dumps(held), "utf-8")
    assert rig.rehearse() == 1
    out = capsys.readouterr().out
    assert said(out, "folder found").endswith("did not answer: not this host's bearer")
    assert verdicts(out)["practice node Ready"] == "FAIL"


def test_a_rehearsal_refuses_a_folder_away_from_its_throwaway_store(
    rig: Rig, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    store = elsewhere / "keyring.json"
    store.write_text(rig.store.read_text("utf-8"), "utf-8")
    code = script.main(["--rehearsal", "--home", str(rig.home), "--store", str(store)])
    assert code == 1
    assert capsys.readouterr().out.startswith("FAIL rehearsal refused: ")
    assert rig.host.asked == []


def _git(where: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(where), *args], check=True, capture_output=True)  # noqa: S607


def _commit(where: Path, message: str) -> None:
    _git(where, "add", "-A")
    _git(where, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", message)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """A checkout one commit behind its origin's `engine/base`, whose tip added the script."""
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q", "-b", script.LANDED_ON)
    (source / "README").write_text("one\n", "utf-8")
    _commit(source, "before")
    (source / "tools").mkdir()
    (source / script.SCRIPT).write_text("# landed\n", "utf-8")
    _commit(source, "landed")
    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(source), str(origin)],  # noqa: S607
        check=True,
        capture_output=True,
    )
    _git(source, "remote", "add", "origin", str(origin))
    _git(source, "fetch", "-q", "origin")
    return source


def test_real_mode_refuses_a_checkout_lacking_the_landed_branchs_commit_before_it_reads_any_bearer(
    rig: Rig, checkout: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _git(checkout, "reset", "-q", "--hard", "HEAD~1")
    read: list[str] = []

    def bearer() -> str:
        read.append("read")
        return BEARER

    code = script.main(
        ["--home", str(rig.home), "--source", str(checkout), "--port", str(rig.port)],
        bearer=bearer,
    )
    out = capsys.readouterr().out
    assert code == 1
    assert out.startswith("FAIL code landed: ") and "Pull it here" in out
    assert "origin/engine/base" in out
    assert len(out.splitlines()) == 1
    assert read == []
    assert rig.host.asked == []


def test_real_mode_refuses_when_the_named_branch_holds_no_script_at_all(
    rig: Rig, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "bare-source"
    source.mkdir()
    _git(source, "init", "-q", "-b", script.LANDED_ON)
    (source / "README").write_text("one\n", "utf-8")
    _commit(source, "before")
    origin = tmp_path / "bare-origin.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(source), str(origin)],  # noqa: S607
        check=True,
        capture_output=True,
    )
    _git(source, "remote", "add", "origin", str(origin))
    _git(source, "fetch", "-q", "origin")
    assert script.main(["--home", str(rig.home), "--source", str(source)]) == 1
    assert "origin/engine/base holds no tools/first_real_start.py" in capsys.readouterr().out


def test_landed_on_reads_the_named_branch(
    rig: Rig, checkout: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.session = "ready"
    rig.host.bound = ["4401"]
    assert script.landed_refusal(checkout, "engine/base") is None
    absent = script.landed_refusal(checkout, "release/next")
    assert absent is not None and "origin/release/next holds no tools/first_real_start.py" in absent

    code = script.main(
        [
            "--home",
            str(rig.home),
            "--source",
            str(checkout),
            "--port",
            str(rig.port),
            "--landed-on",
            "engine/base",
        ],
        bearer=lambda: BEARER,
        monotonic=rig.monotonic,
        sleep=rig.sleep,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert out.splitlines()[0].startswith("PASS code landed: ") and "origin/engine/base" in (
        out.splitlines()[0]
    )

    _git(checkout, "reset", "-q", "--hard", "HEAD~1")
    behind = script.landed_refusal(checkout, "engine/base")
    assert behind is not None and "which lacks" in behind and "origin/engine/base" in behind


def test_real_mode_on_a_landed_checkout_goes_on_with_the_injected_bearer(
    rig: Rig, checkout: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rig.host.session = "ready"
    rig.host.bound = ["4401"]
    code = script.main(
        ["--home", str(rig.home), "--source", str(checkout), "--port", str(rig.port)],
        bearer=lambda: BEARER,
        monotonic=rig.monotonic,
        sleep=rig.sleep,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("PASS code landed: ")
    assert step_lines(out) == ["code landed", *LINES[:5], PLAIN, *LINES[6:]]
