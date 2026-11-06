"""His own test: a copilot chat builds a unit, checks it, backtests it and says the verdict.

Check 18 of the foundation proof. It runs through a real host on a scratch QMX folder, over the
host's chat routes, on `haiku`, and it is opt-in with `QMX_TEST_LIVE=1` so the package suite never
starts a host or a model.

What it does, in order. It takes the engine lane lock, makes a throwaway QMX folder with the
first-start card so QMB is enabled and `[qmb] bars` stays empty, makes the plan login one junction,
and lands EURUSD for March 2025 through the shipped `download-dukascopy` template. If that refuses,
times out, or `QMX_TEST_SAVED_MONTH=1` is set, it lands the saved March m15 pair through the real
market door instead and says so. Then it starts `python -m qmx_host serve` with the throwaway file
keyring, opens one chat on `haiku`, sends the sentence below, answers every ask as the operator
would, and waits for the turn to end.

It asserts the chat's tool calls in order, the saved draft's bindings, the result's trades and its
`consumed` edge to a `dataset`, the stored verdict, and that the chat's last message holds the
verdict's own words before " by the ". It does not assert which verdict, because his question is
whether an agent can build and backtest, not whether the dummy passes.

The script is the one R09 proved at `S/evidence/r09/december_real.py` and the tick form is the one
R08 proved at `S/proofs/ground-qmb/bridge.py`. From `qmx-agents/` on This PC, with the agents venv
and the engine lane lock free:

    QMX_TEST_LIVE=1 uv run --no-sync pytest -p no:xdist -s \\
        packages/qma-harness/tests/live/test_his_own_test.py

On another host set `QMX_REPAIR_SHIP`, `QMX_LANE_LOCK`, `QMX_R14_LOGIN` and `QMX_SAVED_DATA`.
"""

from __future__ import annotations

import csv
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Protocol, cast

import pytest

if TYPE_CHECKING:
    from qmx_library.store import Store

REPO: Final = Path(__file__).resolve().parents[5]
S: Final = Path(os.environ.get("QMX_REPAIR_SHIP", "D:/QMX-worktrees/repair-ship"))
LOCK: Final = Path(os.environ.get("QMX_LANE_LOCK", "D:/QMX-worktrees/.engine-lane-lock"))
LOGIN: Final = Path(os.environ.get("QMX_R14_LOGIN", "D:/QMX-worktrees/qma-ship/home/claude"))
SAVED: Final = Path(
    os.environ.get("QMX_SAVED_DATA", "D:/QMX-worktrees/unit-ship/data/dukascopy-node")
)
FOLDER: Final = S / "homes" / "r14-18" / "QMX"
SENTENCE: Final = (
    "Build me a unit on EURUSD from the dictionary blocks that only enters when ADX is above 25, "
    "backtest it on March 2025, and tell me in plain words what the judge says."
)
SYMBOL: Final = "EURUSD"
MONTH: Final = "2025-03"
SCALE: Final = 5
KEEP: Final = ("C38_KEYRING_FILE", "PYTHONPATH", "PYTHON_KEYRING_BACKEND", "UV_CACHE_DIR")
LOCK_WAIT_S: Final = 1800.0
HOST_LIMIT_S: Final = 600.0
DATA_LIMIT_S: Final = 1500.0
TURN_LIMIT_S: Final = 1500.0
POLL_S: Final = 2.0
BOUND: Final = {"adx@1", "value-above@1"}
TOOL_NAMES: Final = (
    "blocks_find",
    "blocks_match",
    "unit_new",
    "unit_check",
    "backtest_run",
    "backtest_judge_run",
)


class Log:
    """One PASS or FAIL line per step, then one verdict, as the lane log reads them."""

    def __init__(self) -> None:
        self.failed: list[str] = []

    def __call__(self, line: str) -> None:
        print(line.encode("ascii", "backslashreplace").decode(), flush=True)

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        if not ok:
            self.failed.append(name)

    def verdict(self) -> None:
        self("FAIL" if self.failed else "PASS")
        assert not self.failed, self.failed


class _Scaled(Protocol):
    """R08's door method, which this lane meets at the joined stack tip."""

    def state_scale(self, series: str, scale: int) -> Any: ...


class HttpRefused(Exception):
    def __init__(self, code: int, detail: str) -> None:
        super().__init__(f"{code}: {detail[:300]}")
        self.code = code


@contextmanager
def lane_lock() -> Generator[None]:
    deadline = time.monotonic() + LOCK_WAIT_S  # ambient-scan: allow - a bounded lane lock wait
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:  # ambient-scan: allow - a bounded lane lock wait
                pytest.fail(f"the lane lock {LOCK} stayed held for {LOCK_WAIT_S:.0f} s")
            time.sleep(20)
    try:
        yield
    finally:
        LOCK.rmdir()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def make_junction(link: Path, target: Path) -> None:
    """The boot recipe's one login junction, so the plan login is linked and never copied."""
    if link.is_junction():
        remove_junction(link)
    elif link.exists():
        if any(link.iterdir()):
            raise AssertionError(
                f"{link} holds files; refuse to replace it with the login junction"
            )
        link.rmdir()
    if os.name != "nt":
        link.symlink_to(target, target_is_directory=True)
        return
    done = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],  # noqa: S607 - the OS console
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise AssertionError(f"no login junction at {link}: {done.stderr or done.stdout}")


def remove_junction(link: Path) -> None:
    if not link.exists() and not link.is_junction():
        return
    if os.name != "nt":
        link.unlink(missing_ok=True)
        return
    subprocess.run(
        ["cmd", "/c", "rmdir", str(link)],  # noqa: S607 - the OS console
        capture_output=True,
        text=True,
        check=False,
    )


def make_folder() -> Path:
    """A new QMX folder with the first-start card and the guard's keep list."""
    from qmx_home import resolve

    folder = FOLDER
    assert folder.is_relative_to(S / "homes"), folder
    remove_junction(folder / "data" / "claude")
    shutil.rmtree(folder, ignore_errors=True)
    (folder.parent / "serve.log").unlink(missing_ok=True)
    layout = resolve(folder, create=True, drives=[])
    home = layout.home
    (home / "first-party.json").write_text(json.dumps({"enable": ["qmb", "mis"]}), "utf-8")
    keep = json.dumps(sorted(KEEP))
    (home / "settings.toml").write_text(
        f"[environment]\nkeep = {keep}\n\n[qmb]\nagent_wait_s = 1800\n", "utf-8"
    )
    return folder


def last_json(text: str) -> dict[str, Any]:
    for raw in reversed(text.splitlines()):
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            body = json.loads(line)
        except ValueError:
            continue
        if isinstance(body, dict):
            return cast("dict[str, Any]", body)
    return {}


def saved_month(folder: Path, say: Log) -> bool:
    """Run the shipped download template for March 2025. False when it refused or ran out."""
    from qmx_engine.templates.catalog import PACK

    script = PACK / "download-dukascopy" / "scripts" / "download.py"
    work = folder.parent / "download"
    shared = folder / "cache" / "zones" / "real" / "work"
    work.mkdir(parents=True, exist_ok=True)
    shared.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "QMX_WORK": str(work), "QMX_WORK_SHARED": str(shared)}
    source = {"symbol": SYMBOL, "month": MONTH, "price_scale": SCALE}
    started = time.monotonic()  # ambient-scan: allow - the lane's own timing
    try:
        done = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps({"in": {"source": source}}),
            capture_output=True,
            text=True,
            env=environment,
            cwd=work,
            timeout=DATA_LIMIT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        say(f"INFO download-dukascopy gave no month in {DATA_LIMIT_S:.0f} s; the door stands in")
        return False
    seconds = time.monotonic() - started  # ambient-scan: allow - the lane's own timing
    landed = last_json(done.stdout)
    if landed.get("status") != "landed":
        say(
            f"INFO download-dukascopy did not land a month (exit {done.returncode}); "
            f"{done.stdout.strip()[:300]} {done.stderr.strip()[-300:]}"
        )
        return False
    say(
        f"PASS data: download-dukascopy landed {SYMBOL} {MONTH} "
        f"({landed.get('rows')} rows in {seconds:.0f} s)"
    )
    return True


def bars(path: Path) -> dict[int, tuple[str, str, str, str]]:
    found: dict[int, tuple[str, str, str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        at = {name: index for index, name in enumerate(header)}
        for row in reader:
            found[int(row[at["timestamp"]])] = (
                row[at["open"]],
                row[at["high"]],
                row[at["low"]],
                row[at["close"]],
            )
    return found


def door_month(folder: Path, say: Log) -> None:
    """The saved March m15 pair cut into ticks and committed through the real door."""
    from qmf.core import is_refusal
    from qmf.data.series import SeriesKey
    from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter
    from qmx_host.market_data import (  # pyright: ignore[reportMissingTypeStubs]
        MarketDoor,
        Placement,
    )

    home = folder / "data"
    root = home / "market"
    staging = root / "staging"
    year, month = (int(part) for part in MONTH.split("-"))
    key = SeriesKey.try_create("dukascopy", SYMBOL, "ticks", year, month)
    assert not is_refusal(key), key
    opened = MarketDoor.open(root, {}, placement=Placement.PC)
    assert not is_refusal(opened), opened
    door = opened.value
    bids = bars(SAVED / f"{SYMBOL.lower()}-m15-bid-{MONTH}-01-2025-04-01.csv")
    asks = bars(SAVED / f"{SYMBOL.lower()}-m15-ask-{MONTH}-01-2025-04-01.csv")
    say(f"INFO saved month: {len(bids)} bid bars, {len(asks)} ask bars")
    rows: list[tuple[int, int, int, float, float]] = []
    for stamp in sorted(set(bids) & set(asks)):
        bid, ask = bids[stamp], asks[stamp]
        points = ((bid[0], ask[0]), (bid[1], ask[1]), (bid[2], ask[2]), (bid[3], ask[3]))
        for offset, (left, right) in zip((0, 200_000, 400_000, 880_000), points, strict=True):
            rows.append(
                (
                    stamp + offset,
                    int(Decimal(left).scaleb(SCALE)),
                    int(Decimal(right).scaleb(SCALE)),
                    1.0,
                    1.0,
                )
            )
    staged = staging / "dukascopy" / SYMBOL / "ticks" / "-" / f"{MONTH}.parquet"
    staged.parent.mkdir(parents=True, exist_ok=True)
    TypedWriter(staged, key.value.text, TICK_COLUMNS).add(rows).finish()
    landed = door.commit([staged], staging=staging, born_on=Placement.PC)
    assert not is_refusal(landed), landed
    scaled = cast("_Scaled", door).state_scale(f"dukascopy/{SYMBOL}/ticks/-", SCALE)
    assert not is_refusal(scaled), scaled
    say(
        f"PASS data: the door landed {SYMBOL} {MONTH} through the saved m15 pair "
        f"({len(rows)} ticks)"
    )


def host_environment(keyring: Path, token: str) -> dict[str, str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("CLAUDE", "ANTHROPIC"))
    }
    environment.update(
        {
            "PYTHON_KEYRING_BACKEND": "owner_lane_keyring.FileKeyring",
            "C38_KEYRING_FILE": str(keyring),
            "PYTHONPATH": os.pathsep.join((str(S / "tools"), str(S / "tools" / "guard"))),
            "TEMP": os.environ.get("TEMP") or tempfile.gettempdir(),
            "TMP": os.environ.get("TMP") or tempfile.gettempdir(),
            "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR")
            or str(Path(tempfile.gettempdir()) / "uv"),
        }
    )
    keyring.parent.mkdir(parents=True, exist_ok=True)
    keyring.write_text(json.dumps({"qmx/control-token|control-token": token}), "utf-8")
    return environment


def start_host(folder: Path) -> tuple[subprocess.Popen[bytes], int, str, Path]:
    port = free_port()
    keyring = folder.parent / f"{folder.name}-keyring.json"
    token = secrets.token_urlsafe(32)
    log = folder.parent / "serve.log"
    handle = log.open("ab")
    process = subprocess.Popen(
        [sys.executable, "-m", "qmx_host", "serve", "--home", str(folder), "--port", str(port)],
        cwd=REPO / "qmx-agents",
        env=host_environment(keyring, token),
        stdout=handle,
        stderr=handle,
    )
    handle.close()
    return process, port, token, log


def stop_host(process: subprocess.Popen[bytes], said: Log) -> None:
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],  # noqa: S607 - the OS tool
                capture_output=True,
                check=False,
            )
        else:
            process.terminate()
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=60)
    said(f"INFO host stopped, exit {process.returncode}")


class Http:
    def __init__(self, port: int, token: str) -> None:
        self.port, self.token = port, token

    def __call__(self, method: str, path: str, body: Mapping[str, object] | None = None) -> Any:
        data = None if body is None else json.dumps(dict(body)).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            raise HttpRefused(error.code, error.read().decode("utf-8", "replace")) from error
        return json.loads(raw) if raw else None


def obj(value: object) -> dict[str, Any] | None:
    """One JSON object, or None when the value is not one."""
    return cast("dict[str, Any]", value) if isinstance(value, dict) else None


def wait_health(http: Http, say: Log) -> None:
    deadline = time.monotonic() + HOST_LIMIT_S  # ambient-scan: allow - a bounded host start
    while time.monotonic() < deadline:  # ambient-scan: allow - a bounded host start
        try:
            health = obj(http("GET", "/api/health"))
        except HttpRefused, OSError:
            health = None
        if health is not None and health.get("status") == "ok":
            break
        time.sleep(1)
    else:
        raise AssertionError(f"the host did not answer /api/health in {HOST_LIMIT_S:.0f} s")
    say("PASS host: /api/health answered")
    deadline = time.monotonic() + HOST_LIMIT_S  # ambient-scan: allow - a bounded app install
    while time.monotonic() < deadline:  # ambient-scan: allow - a bounded app install
        try:
            installed = obj(http("GET", "/api/apps/qmb"))
        except HttpRefused:
            installed = None
        runtime = obj(installed.get("runtime")) if installed is not None else None
        if runtime is not None and runtime.get("status") == "running":
            say("PASS host: QMB is running")
            return
        time.sleep(2)
    raise AssertionError(f"QMB did not reach running in {HOST_LIMIT_S:.0f} s")


def blocks(http: Http, chat: str) -> list[dict[str, Any]]:
    events = http("GET", f"/api/sessions/{chat}/events?after=0&limit=1000")
    found: list[dict[str, Any]] = []
    for event in cast("list[object]", events or []):
        row = obj(event)
        if row is None:
            continue
        data = obj(row.get("data"))
        block = obj(data.get("block")) if data is not None else None
        if block is not None:
            found.append(block)
    return found


def unanswered(block: dict[str, Any], answered: set[int]) -> bool:
    content = obj(block.get("content"))
    return bool(
        block.get("type") in {"permission", "question"}
        and content is not None
        and content.get("state") == "asking"
        and int(block.get("seq", -1)) not in answered
    )


def answer(http: Http, chat: str, block: dict[str, Any], answered: set[int]) -> None:
    content = cast("dict[str, Any]", block["content"])
    seq = int(block["seq"])
    if block.get("type") == "permission":
        body: dict[str, object] = {"decision": "allow_once"}
    else:
        body = {"decision": "answers", "answers": answers(content)}
    http("POST", f"/api/approvals/{chat}.{seq}", body)
    answered.add(seq)


def answers(content: dict[str, Any]) -> dict[str, str]:
    given = obj(content.get("input"))
    questions = cast("list[object]", given.get("questions") or []) if given is not None else []
    found: dict[str, str] = {}
    for question in questions:
        asked = obj(question)
        if asked is None:
            continue
        text = str(asked.get("question") or "")
        options = cast("list[object]", asked.get("options") or [])
        first = obj(options[0]) if options else None
        found[text] = str(first.get("label") or "") if first is not None else "Yes, go ahead."
    return found


def transcript(folder: Path, chat: str) -> Path | None:
    projects = folder / "data" / "claude" / "projects"
    return next(iter(sorted(projects.glob(f"*/{chat}.jsonl"))), None)


def entries(path: Path) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        entry = obj(value)
        if entry is not None:
            found.append(entry)
    return found


def messages(entry: dict[str, Any]) -> list[dict[str, Any]]:
    message = obj(entry.get("message"))
    content = message.get("content") if message is not None else None
    parts = cast("list[object]", content or [])
    return [part for part in map(obj, parts) if part is not None]


def tool_calls(rows: Sequence[dict[str, Any]]) -> list[tuple[str, str, dict[str, Any]]]:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    for entry in rows:
        if entry.get("type") != "assistant":
            continue
        for part in messages(entry):
            if part.get("type") != "tool_use":
                continue
            given = part.get("input")
            calls.append(
                (
                    str(part.get("name")),
                    str(part.get("id")),
                    cast("dict[str, Any]", given) if isinstance(given, dict) else {},
                )
            )
    return calls


def tool_results(rows: Sequence[dict[str, Any]]) -> dict[str, str]:
    found: dict[str, str] = {}
    for entry in rows:
        if entry.get("type") != "user":
            continue
        for part in messages(entry):
            if part.get("type") != "tool_result":
                continue
            body = part.get("content")
            if isinstance(body, str):
                text = body
            else:
                text = "".join(
                    str(chunk.get("text") or "")
                    for chunk in map(obj, cast("list[object]", body or []))
                    if chunk is not None
                )
            found[str(part.get("tool_use_id"))] = text
    return found


def payload(text: str) -> dict[str, Any]:
    try:
        body = obj(json.loads(text))
    except ValueError:
        return {}
    if body is None:
        return {}
    inner = obj(body.get("result"))
    return inner if inner is not None else body


def assistant_text(rows: Sequence[dict[str, Any]]) -> str:
    said: list[str] = []
    for entry in rows:
        if entry.get("type") != "assistant":
            continue
        said += [
            str(part["text"])
            for part in messages(entry)
            if part.get("type") == "text" and part.get("text")
        ]
    return said[-1] if said else ""


def follow(http: Http, chat: str, folder: Path, said: Log) -> str:
    deadline = time.monotonic() + TURN_LIMIT_S  # ambient-scan: allow - a bounded turn
    answered: set[int] = set()
    while time.monotonic() < deadline:  # ambient-scan: allow - a bounded turn
        blocks_now = blocks(http, chat)
        for block in blocks_now:
            if unanswered(block, answered):
                answer(http, chat, block, answered)
        record = obj(http("GET", f"/api/chats/{chat}"))
        state = record.get("turn") if record is not None else None
        if state == "idle":
            path = transcript(folder, chat)
            last = assistant_text(entries(path)) if path is not None else ""
            waiting = any(unanswered(block, answered) for block in blocks(http, chat))
            if last and not waiting:
                time.sleep(POLL_S)  # the last assistant entry reaches the transcript after idle
                path = transcript(folder, chat)
                return (assistant_text(entries(path)) if path is not None else "") or last
        time.sleep(POLL_S)
    raise AssertionError(f"the chat's turn did not end in {TURN_LIMIT_S:.0f} s")


def check_draft(store: Store, item: str, said: Log) -> None:
    from qmx_library.principal import Principal, drafts_ref

    head = store.head(item, drafts_ref(item))
    said.check("store: the unit has a saved draft", head is not None, item)
    assert head is not None
    draft = store.get(Principal("operator"), head[0])
    bound: set[str] = set()
    for pin in cast("list[object]", draft.fields.get("pins") or []):
        found = obj(pin)
        if found is not None:
            bound.add(f"{found.get('entry_id')}@{found.get('version')}")
    said.check(
        "store: the draft binds adx@1 and value-above@1", BOUND.issubset(bound), sorted(bound)
    )


def check_result(store: Store, result_id: str, said: Log) -> None:
    from qmx_library.principal import Principal

    operator = Principal("operator")
    result = store.get(operator, result_id)
    measures = cast("dict[str, Any]", result.fields.get("measures") or {})
    trades = measures.get("trades")
    said.check(
        "store: the result has at least one trade", isinstance(trades, int) and trades >= 1, trades
    )
    consumed = store.walk(operator, [result_id], ("consumed",), "out", depth=1)
    kinds = [store.get(operator, step.object_id).kind for step in consumed]
    said.check(
        "store: a consumed edge names a dataset item",
        any(kind == "dataset" for kind in kinds),
        kinds,
    )


def check_verdict(store: Store, verdict_id: str, message: str, log: Log) -> None:
    from qmx_library.principal import Principal

    verdict = store.get(Principal("operator"), verdict_id)
    words = str(verdict.fields.get("says") or "").split(" by the ")[0].strip()
    log.check("store: the verdict exists", verdict.kind == "verdict", verdict.kind)
    log.check(
        "chat: the last message holds the verdict's words",
        bool(words) and words.casefold() in message.casefold(),
        words,
    )


@pytest.mark.skipif(
    os.environ.get("QMX_TEST_LIVE") != "1", reason="opt-in live test on a real host and haiku"
)
def test_his_own_test() -> None:
    said = Log()
    said(f"INFO sentence: {SENTENCE}")
    with lane_lock():
        folder = make_folder()
        make_junction(folder / "data" / "claude", LOGIN)
        try:
            if os.environ.get("QMX_TEST_SAVED_MONTH") == "1" or not saved_month(folder, said):
                door_month(folder, said)
            process, port, token, log = start_host(folder)
            http = Http(port, token)
            said(f"INFO host pid {process.pid} on port {port}, log {log}")
            chat = ""
            try:
                wait_health(http, said)
                opened = http("POST", "/api/chats", {"title": "r14 his own test", "model": "haiku"})
                chat = str(opened["session_id"])
                said(f"PASS host: chat {chat}")
                http("POST", f"/api/sessions/{chat}/turns", {"text": SENTENCE})
                last = follow(http, chat, folder, said)
            finally:
                stop_host(process, said)
            assert chat, "the host opened no chat"

            path = transcript(folder, chat)
            assert path is not None, "the chat left no SDK transcript in the plan home"
            rows = entries(path)
            calls = tool_calls(rows)
            results = tool_results(rows)
            names = [name for name, _, _ in calls]
            said(f"INFO tools: {names}")

            positions = {
                name: [index for index, called in enumerate(names) if called == name]
                for name in TOOL_NAMES
            }
            blocks_seen = sorted(positions["blocks_find"] + positions["blocks_match"])
            news, checks = positions["unit_new"], positions["unit_check"]
            runs, judges = positions["backtest_run"], positions["backtest_judge_run"]
            said.check("journal: blocks were found first", bool(blocks_seen), blocks_seen)
            said.check("journal: unit_new was called", bool(news), news)
            said.check("journal: unit_check was called", bool(checks), checks)
            said.check("journal: backtest_run was called", bool(runs), runs)
            said.check("journal: backtest_judge_run was called", bool(judges), judges)
            assert blocks_seen and news and checks and runs and judges
            said.check(
                "journal: blocks, unit_new and unit_check come in order",
                min(blocks_seen) < min(news) < min(checks),
                names,
            )
            before_run = [index for index in checks if index < min(runs)]
            said.check("journal: unit_check runs before backtest_run", bool(before_run), before_run)
            said.check(
                "journal: backtest_judge_run follows backtest_run",
                min(runs) < min(judges),
                names,
            )
            assert before_run
            last_check = payload(results.get(calls[before_run[-1]][1], ""))
            said.check(
                "journal: the last unit_check before the run passed",
                last_check.get("verdict") == "pass",
                last_check.get("verdict"),
            )

            item = str(payload(results.get(calls[min(news)][1], "")).get("item") or "")
            result_id = str(payload(results.get(calls[min(runs)][1], "")).get("result_id") or "")
            verdict_id = str(
                payload(results.get(calls[min(judges)][1], "")).get("verdict_id") or ""
            )
            said.check("journal: unit_new answered an item", bool(item), item)
            said.check("journal: backtest_run answered a result", bool(result_id), result_id)
            said.check("journal: the judge answered a verdict", bool(verdict_id), verdict_id)
            assert item and result_id and verdict_id

            from qmx_engine.ledger import redact
            from qmx_library.store import Store

            with Store.open(folder / "data" / "library", redactor=redact) as store:
                check_draft(store, item, said)
                check_result(store, result_id, said)
                check_verdict(store, verdict_id, last, said)
        finally:
            remove_junction(folder / "data" / "claude")
    said.verdict()
