"""The first real start on his own QMX folder, as one command he runs (Part C slice C-14, OP-02).

    uv run python tools/first_real_start.py

It sets the practice node up through the running host, signs in on cTrader's own demo page, makes
one test trade, lands the passport and the records, deploys the dummy unit on the market he names,
and finds the node's journal rows in This PC's store. It prints one PASS or FAIL line per fact and
exits non-zero on any FAIL. Running it again converges: every step checks what is in place first.

It talks only to the host's REST, with the bearer from Credential Manager, and imports nothing from
`qmx-agents`, because the root env holds none of it. Only the trading node sends an order, and the
one this script asks for is the self-test's.

Real mode refuses a checkout that lacks the commit on `origin/main` that added this file, before it
reads any credential. He squash-merges, so stack SHAs never reach main and there is no build stamp.

`--rehearsal` runs the same steps on a throwaway folder. Its bearer and his answers come only from
the throwaway store file named by `--store`, a JSON object of `<service>|<user>` entries, so it
never reads Credential Manager. Whoever runs it holds a fake cTrader on the node's loopback.
"""

from __future__ import annotations

import argparse
import ctypes
import getpass
import http.server
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final, Protocol, TypeAlias, cast

import tomllib

NODE: Final = "trading-node"
KIND: Final = "trading-node-pc"
PLACE: Final = "first-start"
"""The connect dialog's name for this run; the kind homes the node in This PC's own row."""
BEARER_SERVICE: Final = "qmx/control-token"
BEARER_USER: Final = "control-token"
APP_SECRET_KEY: Final = "qmx/node-ctrader-app-secret"  # noqa: S105 - an entry name, not a secret
LABEL: Final = "qmx-home.toml"
PASSPORT: Final = "data/trading-node-passport.json"
RECEIVER: Final = ("127.0.0.1", 47613)
"""The node's sign-in redirect (`qmn.app.grants.REDIRECT`), where cTrader sends the one code."""
DUMMY: Final = "dummy-trend-pullback"
TEST_TRADE: Final = "demo test trade with its stop placed, observed and closed"
PASSPORT_CHECKS: Final = (
    "broker session",
    "feed freshness",
    TEST_TRADE,
    "kill-switch latency",
    "image digest",
    "clock band",
    "disk",
)
READY_WORDS: Final = frozenset({"Ready", "Trading"})
SIGNED_OUT: Final = frozenset({"signed_out", "expired"})
HARVEST_GRACE_S: Final = 60.0
"""The plan's "plus a minute" past `[records] open_harvest_s`."""
SCRIPT: Final = "tools/first_real_start.py"
CONNECT_ROUNDS: Final = 5
"""A run answers at most his app card, his signature, and ends on the sign-in card."""
POLL_S: Final = 1.0

Json: TypeAlias = dict[str, Any]


@dataclass(frozen=True, slots=True)
class Line:
    check: str
    ok: bool
    said: str

    def __str__(self) -> str:
        return f"{'PASS' if self.ok else 'FAIL'} {self.check}: {self.said}"


class Him(Protocol):
    """What only he can answer."""

    def trading_app(self, line: str) -> tuple[str, str] | None: ...

    def sign_in_code(self, link: str, wait_s: float) -> str | None: ...


@dataclass(frozen=True)
class Options:
    home: Path
    port: int = 8766
    account: str | None = None
    venue: str = "icmarkets-ctrader"
    market: str = "fx.eurusd"
    setup_s: float = 1800.0
    session_s: float = 120.0
    trade_s: float = 120.0
    sign_in_s: float = 300.0


@dataclass(frozen=True, slots=True)
class Answer:
    status: int
    body: Any

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    @property
    def said(self) -> str:
        """Why the host refused, in its own words."""
        body = self.body
        if not isinstance(body, dict):
            return f"HTTP {self.status}" if self.status else str(body)
        found = cast(Json, body)
        error = found.get("error")
        words = cast(Json, error).get("message") if isinstance(error, dict) else None
        return str(words or found.get("message") or found.get("detail") or f"HTTP {self.status}")


@dataclass(frozen=True, slots=True)
class Host:
    """The running host's REST behind one bearer. Nothing here raises for a refusal."""

    port: int
    bearer: str

    def rest(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, str] | None = None,
        body: object = None,
        timeout: float = 120.0,
    ) -> Answer:
        url = f"http://127.0.0.1:{self.port}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)  # noqa: S310 - loopback
        request.add_header("Authorization", f"Bearer {self.bearer}")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as answer:  # noqa: S310
                return Answer(answer.status, json.loads(answer.read() or b"null"))
        except urllib.error.HTTPError as refused:
            text = refused.read()
            try:
                return Answer(refused.code, json.loads(text or b"null"))
            except ValueError:
                return Answer(refused.code, None)
        except (OSError, ValueError) as error:
            return Answer(0, f"the host did not answer ({type(error).__name__})")


@dataclass(slots=True)
class World:
    options: Options
    host: Host
    him: Him
    monotonic: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    answered: bool = False
    node_up: bool = False
    tag: str = ""
    account: str = ""
    session: bool = False
    rows_before: int = 0
    traded_at: float | None = None
    deployment: str = ""
    extras: list[str] = field(default_factory=list[str])

    def node(self, operation: str, **arguments: object) -> Json:
        """One node operation: the node's own answer, or a refusal in the same shape."""
        called = self.host.rest("POST", f"/api/apps/{NODE}/tools/{operation}", body=arguments)
        if not called.ok:
            return {"ok": False, "code": f"HTTP {called.status}", "message": called.said}
        found = cast(Json, called.body).get("result")
        return cast(Json, found) if isinstance(found, dict) else {"ok": False, "code": "no_answer"}


def _refusal(answer: Json) -> str:
    return f"{answer.get('code')}: {answer.get('message')}"


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")


# --- the connect dialog, on his answers ---


def _connect_once(world: World, answer: Json) -> Json | str:
    """One run of the connect kind: its finished job, or why it did not finish, in one sentence."""
    began = world.monotonic()
    started = world.host.rest(
        "POST", "/api/connect/jobs", body={"kind": KIND, "place": PLACE, "answer": answer}
    )
    if not started.ok:
        return f"the host did not start the node's setup: {started.said}"
    job = cast(Json, started.body)
    while job.get("state") == "running":
        if world.monotonic() - began > world.options.setup_s:
            return f"the setup stuck at step {job.get('step')} for {world.options.setup_s:.0f} s"
        world.sleep(POLL_S)
        read = world.host.rest("GET", f"/api/connect/jobs/{job['id']}")
        if not read.ok:
            return f"the host did not answer for its setup job: {read.said}"
        job = cast(Json, read.body)
    if job.get("state") != "finished":
        return f"the setup stopped: {job.get('line')}"
    return job


def _signature(world: World) -> str | None:
    """His signature for the node's version, from the host's operator-only sign route."""
    found = world.host.rest("GET", f"/api/apps/{NODE}")
    if not found.ok:
        return None
    app = cast(Json, found.body)
    query = {"definition_hash": str(app["definition_hash"])}
    active = cast(Json, app.get("road") or {}).get("active")
    if isinstance(active, dict):
        query["expected_active"] = str(cast(Json, active)["revision"])
    signed = world.host.rest("POST", f"/api/apps/{NODE}/sign", query=query)
    return str(cast(Json, signed.body)["signature"]) if signed.ok else None


def set_up(world: World) -> Json | str:
    """Run the connect kind, answering his app and his signature, until only the sign-in waits."""
    answer: Json = {}
    for _ in range(CONNECT_ROUNDS):
        job = _connect_once(world, answer)
        if isinstance(job, str):
            return job
        needs = cast("Json | None", job.get("needs"))
        card = None if needs is None else str(needs.get("card"))
        if card is None or card == "sign-in":
            return job
        if card == "ctrader-app":
            app = world.him.trading_app(str(cast(Json, needs).get("line")))
            if app is None:
                return "this PC's cTrader trading app was not given"
            stored = world.host.rest("PUT", f"/api/keys/{APP_SECRET_KEY}", body={"value": app[1]})
            if not stored.ok:
                return f"the host did not keep the trading app's secret: {stored.said}"
            answer = {"fields": {"client_id": app[0]}}
        elif card == "signature":
            signature = _signature(world)
            if signature is None:
                return "the host's sign route did not sign the node's version"
            answer = {"fields": {"signature": signature}}
        else:
            return f"the setup waits on you: {cast(Json, needs).get('line')}"
    return f"the setup asked more than {CONNECT_ROUNDS} times without finishing"


# --- the checks, in order ---


def _folder(world: World) -> tuple[bool, str]:
    home = world.options.home
    if not (home / LABEL).is_file():
        return False, f"{home} holds no {LABEL}, so it is not a QMX folder"
    health = world.host.rest("GET", "/api/health", timeout=10.0)
    if not health.ok:
        return False, f"the host on port {world.options.port} did not answer: {health.said}"
    held = cast(Json, health.body)
    if held.get("read_only"):
        return False, f"the host opened these read-only: {held.get('read_only')}"
    world.answered = True
    return True, f"{home}, its host answers as pid {held.get('pid')}"


def _ready(world: World) -> tuple[bool, str]:
    if not world.answered:
        return False, "no host answered, so nothing was set up"
    job = set_up(world)
    if isinstance(job, str):
        return False, job
    status = world.node("status")
    if status.get("ok") is not True:
        return False, f"the node did not answer its status ({_refusal(status)})"
    value = cast(Json, status["value"])
    world.tag = str(cast(Json, value.get("identity") or {}).get("tag") or "")
    world.node_up = True
    word = str(value.get("word"))
    if word not in READY_WORDS:
        return False, f"the node reads {word}: {value.get('reasons')}"
    return True, f"{value.get('headline')}, node {world.tag}"


def _ctrader(world: World) -> Json:
    status = world.node("status")
    venues = cast("list[Json]", cast(Json, status.get("value") or {}).get("venues") or [])
    return next((row for row in venues if row.get("venue") == "ctrader"), {})


def _sign_in(world: World) -> list[Json] | str:
    """cTrader's accounts for a new grant, or why there is none. A held grant lists none."""
    begun = world.node("sign_in_begin", op_id=f"first-start-begin-{_stamp()}", venue="ctrader")
    if begun.get("ok") is not True:
        return f"the sign-in did not begin ({_refusal(begun)})"
    link = str(cast(Json, begun["value"])["url"])
    code = world.him.sign_in_code(link, world.options.sign_in_s)
    if code is None:
        return f"no code came back from cTrader's page in {world.options.sign_in_s:.0f} s"
    signed = world.node("sign_in_code", op_id=f"first-start-code-{_stamp()}", code=code)
    if signed.get("ok") is not True:
        return f"the sign-in did not finish ({_refusal(signed)})"
    value = cast(Json, signed["value"])
    if value.get("kept") is not True:
        return f"the node did not keep the grant: {value.get('reason')}"
    return cast("list[Json]", value.get("accounts") or [])


def _account_to_bind(listed: Sequence[Json], named: str | None) -> str | None:
    demo = [str(row["account"]) for row in listed if row.get("is_live") is False]
    if named is not None:
        return named if named in demo else None
    return demo[0] if len(demo) == 1 else None


def _session(world: World) -> tuple[bool, str]:
    if not world.node_up:
        return False, "the node is not up, so no session can open"
    row = _ctrader(world)
    if row.get("session") == "not_set_up":
        return False, "the node holds no cTrader trading app, so no session can open"
    listed: list[Json] = []
    if row.get("session") in SIGNED_OUT:
        found = _sign_in(world)
        if isinstance(found, str):
            return False, found
        listed = found
        row = _ctrader(world)
    bound = [str(account) for account in cast("list[object]", row.get("accounts") or [])]
    if world.options.account is not None and world.options.account in bound:
        world.account = world.options.account
    elif bound and world.options.account is None:
        world.account = bound[0]
    else:
        chosen = _account_to_bind(listed, world.options.account)
        if chosen is None:
            names = [str(item.get("account")) for item in listed]
            return False, f"name one demo account with --account; cTrader lists {names}"
        bind = world.node(
            "bind",
            op_id=f"first-start-bind-{chosen}",
            account={"id": chosen, "ctid": int(chosen), "venue": world.options.venue},
            action="add",
        )
        if bind.get("ok") is not True:
            return False, f"the account did not bind ({_refusal(bind)})"
        world.account = chosen
    began = world.monotonic()
    while world.monotonic() - began <= world.options.session_s:
        row = _ctrader(world)
        if row.get("session") == "ready":
            world.session = True
            return True, f"account {world.account} on {row.get('environment')}"
        world.sleep(POLL_S)
    return False, (
        f"the demo session read {row.get('session')} for {world.options.session_s:.0f} s "
        f"({row.get('reason')})"
    )


def _rows(world: World, kind: str) -> tuple[int, str]:
    """The rows and the open month of one node journal kind in This PC's store."""
    series = f"journal-node/{world.tag}/{kind}/-"
    card = world.host.rest("GET", "/api/data/card", query={"series": series})
    if not card.ok:
        return 0, ""
    parts = cast("list[Json]", cast(Json, card.body).get("partitions") or [])
    opened = [part for part in parts if part.get("frozen") is False]
    return sum(int(part.get("rows") or 0) for part in parts), str(
        opened[-1].get("month") if opened else ""
    )


def _trade(world: World) -> tuple[bool, str]:
    if not world.session:
        return False, "no test trade ran, because the demo session is not ready"
    world.rows_before = _rows(world, "order")[0]
    before = cast(Json, world.node("passport").get("value") or {}).get("at")
    asked = world.node("self_test", op_id=f"first-start-test-{_stamp()}", account=world.account)
    if asked.get("ok") is not True:
        return False, f"the node did not take the test trade ({_refusal(asked)})"
    began = world.monotonic()
    while world.monotonic() - began <= world.options.trade_s:
        passport = cast(Json, world.node("passport").get("value") or {})
        checks = cast("list[Json]", passport.get("checks") or [])
        if passport.get("at") != before and checks:
            world.traded_at = world.monotonic()
            row = next((check for check in checks if check.get("name") == TEST_TRADE), {})
            value = cast(Json, row.get("value") or {})
            if row.get("ok") is not True:
                return False, f"the test trade did not finish: {value.get('detail')}"
            return True, (
                f"entry {value.get('entry')}, stop {value.get('stop')}, exit {value.get('exit')}"
            )
        world.sleep(POLL_S)
    return False, f"the node did not finish the test trade in {world.options.trade_s:.0f} s"


def _passport(world: World) -> tuple[bool, str]:
    if not world.node_up:
        return False, "the node is not up, so no passport can land"
    job = set_up(world)
    if isinstance(job, str):
        return False, job
    lines = cast("list[str]", cast(Json, job.get("result") or {}).get("lines") or [])
    world.extras = [line for line in lines if line.startswith("records:")]
    path = world.options.home / PASSPORT
    try:
        held = cast(Json, json.loads(path.read_text("utf-8")))
    except (OSError, ValueError):
        return False, f"{path} did not land"
    checks = {str(row.get("name")): row.get("ok") for row in held.get("checks") or []}
    wrong = [name for name in PASSPORT_CHECKS if checks.get(name) is not True]
    if wrong:
        return False, f"the passport landed and these checks are not ok: {', '.join(wrong)}"
    return True, f"{len(checks)} checks ok; {'; '.join(world.extras) or 'records already on main'}"


def _dummy_version(world: World) -> str | None:
    """The dummy unit's newest version the Library holds."""
    found = world.host.rest("GET", "/api/library", query={"query": DUMMY, "limit": "100"})
    rows = cast("list[Json]", found.body) if found.ok and isinstance(found.body, list) else []
    units = [
        row
        for row in rows
        if row.get("kind") == "unit"
        and cast(Json, row.get("content") or {}).get("unit_id") == DUMMY
    ]
    units.sort(key=lambda row: int(row.get("version") or 0))
    return str(units[-1]["id"]) if units else None


def _deployed(world: World) -> tuple[bool, str]:
    """His click on the market he named, checked on the node's own `deployments` read: the link
    settles a refused queued deploy silently, so the promote answer proves nothing."""
    if not world.session:
        return False, "no deploy was asked, because the demo session is not ready"
    version = _dummy_version(world)
    if version is None:
        return False, f"the Library holds no {DUMMY} unit"
    market = world.options.market
    click = world.host.rest(
        "POST",
        "/api/units/promote",
        body={
            "schema_version": "qmx.units.promote/1",
            "op_id": f"first-start-{market}",
            "unit": {"id": DUMMY, "version": version},
            "market_id": market,
            "to": "paper",
            "node": {"tag": world.tag},
            "account": {"id": world.account},
        },
    )
    if not click.ok:
        body = cast(Json, click.body) if isinstance(click.body, dict) else {}
        return False, f"the promote was refused: {click.said} {body.get('next_step') or ''}".strip()
    deployment = str(cast(Json, cast(Json, click.body).get("value") or {}).get("deployment_id"))
    read = world.node("deployments")
    rows = cast("list[Json]", read.get("value") or [])
    row = next((item for item in rows if item.get("deployment_id") == deployment), None)
    if row is None:
        return False, f"the node holds no deployment {deployment}, whatever the promote answered"
    if row.get("state") in {"refused", "withdrawing"}:
        return False, f"the node reads {row.get('state')}: {row.get('detail')}"
    world.deployment = deployment
    return True, f"{deployment} on {market} reads {row.get('state')}"


def _harvest_limit(world: World) -> float:
    records = world.host.rest("GET", "/api/settings/records")
    held = cast(Json, records.body) if records.ok and isinstance(records.body, dict) else {}
    open_s = held.get("open_harvest_s", 60)
    return float(open_s if isinstance(open_s, int) and open_s > 0 else 60) + HARVEST_GRACE_S


def _journal(world: World) -> tuple[bool, str]:
    if not world.tag:
        return False, "the node never answered, so it has no journal to find"
    limit, began = _harvest_limit(world), world.monotonic()
    while world.monotonic() - began <= limit:
        rows, month = _rows(world, "node_lifecycle")
        if rows and month:
            return (
                True,
                f"{rows} rows in open month {month} after {world.monotonic() - began:.1f} s",
            )
        world.sleep(POLL_S)
    return False, f"no node journal row reached the store in {limit:.0f} s"


def _trade_rows(world: World) -> tuple[bool, str]:
    if world.traded_at is None:
        return False, "no test trade ran, so it has no rows to find"
    limit = _harvest_limit(world)
    while world.monotonic() - world.traded_at <= limit:
        rows, month = _rows(world, "order")
        if rows > world.rows_before and month:
            took = world.monotonic() - world.traded_at
            return True, (
                f"{rows - world.rows_before} new rows in open month {month} after {took:.1f} s, "
                f"limit {limit:.0f} s"
            )
        world.sleep(POLL_S)
    return False, f"the test trade's rows did not reach the store in {limit:.0f} s"


CHECKS: Final[tuple[tuple[str, Callable[[World], tuple[bool, str]]], ...]] = (
    ("folder found", _folder),
    ("practice node Ready", _ready),
    ("demo session ready", _session),
    ("test trade with its stop placed, seen and closed", _trade),
    ("passport landed", _passport),
    ("dummy unit deployed on the chosen market", _deployed),
    ("node journal rows in This PC's store", _journal),
    ("test trade rows in This PC's store", _trade_rows),
)


# --- real mode's two gates: his landed code, and Credential Manager ---


def _git(source: Path, *args: str) -> str | None:
    done = subprocess.run(
        ["git", "-C", str(source), *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.strip() if done.returncode == 0 else None


def landed_refusal(source: Path) -> str | None:
    """Why this checkout does not hold his landed code, or None. "Landed" is the commit on
    `origin/main` that added this script being an ancestor of the checkout's head."""
    _git(source, "fetch", "--quiet", "origin", "main")
    added = _git(source, "log", "origin/main", "--diff-filter=A", "--format=%H", "--", SCRIPT)
    if not added:
        return (
            f"{source}: origin/main holds no {SCRIPT}, so nothing is landed. Land the stack, "
            "pull it here, then run this again"
        )
    first = added.splitlines()[-1]
    head = _git(source, "rev-parse", "HEAD")
    if _git(source, "merge-base", "--is-ancestor", first, "HEAD") is None:
        return (
            f"{source}: this checkout is at {head}, which lacks {first} from origin/main. "
            "Pull it here, restart the host, then run this again"
        )
    return None


class _FileTime(ctypes.Structure):
    _fields_ = (("low", ctypes.c_uint32), ("high", ctypes.c_uint32))


class _Credential(ctypes.Structure):
    _fields_ = (
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TargetName", ctypes.c_wchar_p),
        ("Comment", ctypes.c_wchar_p),
        ("LastWritten", _FileTime),
        ("CredentialBlobSize", ctypes.c_uint32),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", ctypes.c_uint32),
        ("AttributeCount", ctypes.c_uint32),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.c_wchar_p),
        ("UserName", ctypes.c_wchar_p),
    )


def credential_manager(target: str) -> str | None:
    """One generic Credential Manager entry the host's keyring wrote, whose blob is UTF-16."""
    if sys.platform != "win32":
        return None
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    found = ctypes.c_void_p()
    if not api.CredReadW(ctypes.c_wchar_p(target), 1, 0, ctypes.byref(found)):
        return None
    try:
        credential = ctypes.cast(found, ctypes.POINTER(_Credential)).contents
        blob = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
    finally:
        api.CredFree(found)
    return blob.decode("utf-16-le")


def real_bearer() -> str | None:
    return credential_manager(BEARER_SERVICE)


class AtTheKeyboard:
    """Him, at the keyboard and on cTrader's own page."""

    def trading_app(self, line: str) -> tuple[str, str] | None:
        print(line, flush=True)
        client_id = input("Client ID: ").strip()
        secret = getpass.getpass("Client secret: ").strip()
        return (client_id, secret) if client_id and secret else None

    def sign_in_code(self, link: str, wait_s: float) -> str | None:
        print(f"Sign in with your demo account on cTrader's own page:\n{link}", flush=True)
        webbrowser.open(link)
        return _receive_code(wait_s)


def _receive_code(wait_s: float) -> str | None:
    """The one code cTrader's page sends to the node's redirect on this machine."""
    codes: list[str] = []

    class Receiver(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            codes.extend(query.get("code", [])[:1])
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"QMX has the code. You can close this page.")

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    try:
        server = http.server.HTTPServer(RECEIVER, Receiver)
    except OSError:
        return None
    began = time.monotonic()
    server.timeout = 1.0
    try:
        while not codes and time.monotonic() - began <= wait_s:
            server.handle_request()
    finally:
        server.server_close()
    return codes[0] if codes else None


class ThrowawayStore:
    """The rehearsal's only store: its bearer and his canned answers, in one JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self, service: str, user: str) -> str | None:
        held = cast(Json, json.loads(self.path.read_text("utf-8")))
        found = held.get(f"{service}|{user}")
        return found if isinstance(found, str) else None

    def trading_app(self, line: str) -> tuple[str, str] | None:
        del line
        client_id = self.read("rehearsal/app", "client_id")
        secret = self.read("rehearsal/app", "client_secret")
        return (client_id, secret) if client_id and secret else None

    def sign_in_code(self, link: str, wait_s: float) -> str | None:
        del link, wait_s
        return self.read("rehearsal/code", "code")


def rehearsal_refusal(home: Path, store: Path | None) -> str | None:
    """A rehearsal runs only on a folder beside its throwaway store file."""
    if store is None or not store.is_file():
        return "a rehearsal needs --store, its throwaway store file; nothing was run"
    if store.resolve().parent not in home.resolve().parents:
        return f"{home} does not sit beside the throwaway store {store}; nothing was run"
    return None


def _pointed_home() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    try:
        named = tomllib.loads((Path(appdata) / "QMX" / "home.toml").read_text("utf-8")).get("home")
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return Path(named) if isinstance(named, str) else None


def run_checks(world: World) -> int:
    began = world.monotonic()
    failed = 0
    for name, check in CHECKS:
        ok, said = check(world)
        failed += not ok
        print(Line(name, ok, said), flush=True)
    print(f"METRIC seconds end to end: {world.monotonic() - began:.1f}", flush=True)
    return 1 if failed else 0


def main(
    argv: Sequence[str] | None = None,
    *,
    bearer: Callable[[], str | None] = real_bearer,
    him: Him | None = None,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--home", type=Path, help="his QMX folder; his pointer file by default")
    parser.add_argument("--port", type=int, default=Options.port)
    parser.add_argument("--account", help="the demo account, when cTrader lists more than one")
    parser.add_argument("--venue", default=Options.venue)
    parser.add_argument("--market", default=Options.market)
    parser.add_argument("--setup-s", type=float, default=Options.setup_s)
    parser.add_argument("--session-s", type=float, default=Options.session_s)
    parser.add_argument("--trade-s", type=float, default=Options.trade_s)
    parser.add_argument("--sign-in-s", type=float, default=Options.sign_in_s)
    parser.add_argument("--rehearsal", action="store_true")
    parser.add_argument("--store", type=Path, help="the rehearsal's throwaway store file")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="the source checkout his host runs from; this script's own by default",
    )
    args = parser.parse_args(argv)
    home = cast("Path | None", args.home) or _pointed_home()
    if home is None:
        print("FAIL folder found: name the QMX folder with --home", flush=True)
        return 1
    options = Options(
        home,
        args.port,
        args.account,
        args.venue,
        args.market,
        args.setup_s,
        args.session_s,
        args.trade_s,
        args.sign_in_s,
    )
    if args.rehearsal:
        refused = rehearsal_refusal(home, args.store)
        if refused is not None:
            print(f"FAIL rehearsal refused: {refused}", flush=True)
            return 1
        store = ThrowawayStore(cast(Path, args.store))
        held, asked = store.read(BEARER_SERVICE, BEARER_USER), him or store
    else:
        if args.store is not None:
            print("FAIL real mode refused: --store belongs to a rehearsal", flush=True)
            return 1
        refused = landed_refusal(cast(Path, args.source))
        if refused is not None:
            print(f"FAIL code landed: {refused}", flush=True)
            return 1
        print(f"PASS code landed: {args.source} holds the landed code", flush=True)
        held, asked = bearer(), him or AtTheKeyboard()
    if not held:
        print(f"FAIL folder found: no bearer in {BEARER_SERVICE}; start the host first", flush=True)
        return 1
    world = World(options, Host(options.port, held), asked, monotonic, sleep)
    return run_checks(world)


if __name__ == "__main__":
    sys.exit(main())
