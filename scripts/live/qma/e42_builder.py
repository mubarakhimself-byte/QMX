"""TPL2 lanes 2 to 4: the copilot builds a workflow from one line (E42), the publish card, and a
script-only request.

From `qmx-agents/` with the agents venv, under `QMA_EVIDENCE_DIR`:

    $env:QMA_EVIDENCE_DIR = "D:/QMX-worktrees/qma-ship/build/evidence/tpl2"
    uv run --no-sync python ../scripts/live/qma/e42_builder.py --lane 2

It takes the lane lock `D:/QMX-worktrees/.engine-lane-lock` itself and removes it after, so never
wrap it in an outer lock. Under the lock it starts `qmx_host` on the ship home through
`scripts/live/engine/lane_host.py` with a bearer made for this run, so nothing but the chat, the
draft and the run is written into the home. It hashes the ship home's `settings.toml` before and
after and never writes it. Every lane drives one `claude/haiku` chat in the default permission
mode, which is the mode the operator runs, so "no ask" is the real thing and not a bypass.

Lane 2, E42. He types one line. PASS when the chat saves a draft through `workflows_drafts_put`,
the saved draft holds three nodes or more, a fresh validation finds no problem, a test run of it
passed (the draft reads `tested`), the Library holds the draft's agent ref, and the turn wrote no
permission, question or needs_you block.

Lane 3, the publish card. He says publish. PASS when the publish row answers with a card and
nothing is published: no version and no `main` ref.

Lane 4, a script-only request. PASS when the draft holds no model-bearing node and its test run
spent no tokens.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Final

import httpx
import psutil

ENGINE_LANES: Final = Path(__file__).resolve().parents[1] / "engine"
LANE_HOST: Final = ENGINE_LANES / "lane_host.py"
AGENTS: Final = Path(__file__).resolve().parents[3] / "qmx-agents"
BEARER_ENV: Final = "QMX_LANE_BEARER"

from common import SHIP_HOME, Log, boot, require_login, session_blocks, use_fake_home  # noqa: E402

SETTINGS: Final = SHIP_HOME / "settings.toml"
LIBRARY: Final = SHIP_HOME / "library"
REQUEST: Final = (
    "every weekday at 7, pull the ECB calendar, summarise it, and save it to the Library. "
    "Call the workflow {item}."
)
"""The one-line request, with the workflow's name in it so each lane run builds its own item: a
home that already holds a tested draft of this line would otherwise be finished already."""
SCRIPT_REQUEST: Final = (
    "a script-only workflow with no model at all: read my trades.csv, total the size column by "
    "symbol, and write the totals to a file. Call the workflow {item}."
)
PUBLISH: Final = "publish it now"
REBUILD: Final = (
    "save the draft for {item} again with expected_revision set to its current revision, and "
    "test-run it; the one I have is stale"
)


def run_item(prefix: str) -> str:
    """A workflow id for this lane run, so a home that already holds an earlier draft of the
    same line still gets a build."""
    return f"{prefix}-{time.strftime('%y%m%d-%H%M%S')}"
TURN_S: Final = 900.0
START_S: Final = 180.0
LANES: Final = {2: "owner-tpl2-e42", 3: "owner-tpl2-publish", 4: "owner-tpl2-script"}
MODEL_NODES: Final = ("llm", "agent", "rlm", "grader")


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def healthy(port: int, headers: dict[str, str]) -> int | None:
    try:
        found = httpx.get(f"http://127.0.0.1:{port}/api/health", headers=headers, timeout=2)
    except httpx.HTTPError:
        return None
    return found.json().get("pid") if found.status_code == 200 else None


def kill_tree(pid: int) -> None:
    with contextlib.suppress(psutil.NoSuchProcess):
        root = psutil.Process(pid)
        tree = [*root.children(recursive=True), root]
        for member in tree:
            with contextlib.suppress(psutil.NoSuchProcess):
                member.kill()
        psutil.wait_procs(tree, timeout=10)


def settings_sha() -> str:
    return hashlib.sha256(SETTINGS.read_bytes()).hexdigest()


@contextlib.contextmanager
def served(log: Log, bearer: str) -> Iterator[httpx.Client]:
    """`qmx_host` on the ship home and a client carrying this lane's bearer."""
    port = free_port()
    headers = {"Authorization": f"Bearer {bearer}"}
    output = Path(str(log.path)).with_suffix(".out").open("wb")
    env = {**os.environ, BEARER_ENV: bearer}
    began = time.perf_counter()
    process = subprocess.Popen(
        [sys.executable, str(LANE_HOST), "qmx_host", "serve", "--home", str(SHIP_HOME),
         "--port", str(port)],
        cwd=AGENTS,
        env=env,
        stdout=output,
        stderr=output,
    )  # fmt: skip
    while healthy(port, headers) is None:
        if process.poll() is not None or time.perf_counter() - began > START_S:
            output.close()
            kill_tree(process.pid)
            raise SystemExit(f"qmx_host did not start on the ship home; see {output.name}")
        time.sleep(0.1)
    log(f"qmx_host pid {process.pid} healthy on port {port} after {time.perf_counter() - began:.2f} s")
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", headers=headers, timeout=180)
    try:
        yield client
    finally:
        client.close()
        kill_tree(process.pid)
        output.close()


def until[T](predicate: Callable[[], T | None], seconds: float, every: float = 2.0) -> T | None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = predicate()
        if found:
            return found
        time.sleep(every)
    return None


def chat_blocks(chat: str) -> list[dict[str, Any]]:
    """The chat's durable blocks, read beside the running host: readers are free (AD-23)."""
    from qma.harness import QmxHome, control_service  # noqa: PLC0415

    return session_blocks(control_service(QmxHome(SHIP_HOME)), chat)


def tool_calls(blocks: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [
        block["content"]
        for block in blocks
        if block.get("type") == "tool" and block["content"].get("name") == name
    ]


def refs_log() -> list[str]:
    path = LIBRARY / "refs" / "log.jsonl"
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def draft_of(client: httpx.Client, item: str) -> dict[str, Any]:
    return client.get(f"/api/workflows/{item}/draft").json()


def runs_of(client: httpx.Client, item: str) -> list[dict[str, Any]]:
    return [
        run
        for run in client.get("/api/workflow-runs", params={"workflow_id": item}).json()
        if run.get("workflow_item") == item
    ]


def new_chat(client: httpx.Client, title: str, slug: str) -> str:
    workspace = Path(os.environ.get("TMP", "D:/Temp")) / f"tpl2-{slug}"
    workspace.mkdir(parents=True, exist_ok=True)
    made = client.post(
        "/api/chats",
        json={"title": title, "model": "haiku", "profile": "claude", "workspace": str(workspace)},
    ).json()
    return str(made["session_id"])


def asking(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        block
        for block in blocks
        if block["type"] in ("permission", "question")
        and block["content"].get("state") == "asking"
    ]


def press(log: Log, client: httpx.Client, chat: str, block: dict[str, Any], allow: bool) -> None:
    """His click on an ask: allow runs the row, reject leaves it undone. The ask's id is the
    chat and the block's own per-session `seq`, not the event feed's row id."""
    decision = {"decision": "allow_once"} if allow else {"decision": "reject", "message": "not now"}
    reply = client.post(f"/api/approvals/{chat}.{block['seq']}", json=decision).json()
    log(f"asked for {block['content'].get('tool')}: {reply}")


def handle_asks(
    log: Log, client: httpx.Client, chat: str, pressed: dict[int, dict[str, Any]], allow: bool
) -> list[dict[str, Any]]:
    """Press every new ask once. A publish ask is the card's own click, so the build rejects it
    and the publish lane allows it; any other ask is a failure the caller checks for."""
    found: list[dict[str, Any]] = []
    for block in asking(chat_blocks(chat)):
        if block["seq"] in pressed:
            continue
        press(log, client, chat, block, allow and "workflows__put" in str(block["content"]))
        pressed[block["seq"]] = block
        found.append(block)
    return found


def ask_turn(client: httpx.Client, chat: str, text: str) -> float:
    sent = client.post(f"/api/sessions/{chat}/turns", json={"text": text})
    if sent.status_code != 202:
        raise SystemExit(f"the turn was refused: {sent.status_code} {sent.text[:200]}")
    return time.perf_counter()


def wait_idle(client: httpx.Client, chat: str, seconds: float) -> str:
    def idle() -> str | None:
        turn = client.get(f"/api/chats/{chat}").json().get("turn")
        return "idle" if turn == "idle" else None

    return "idle" if until(idle, seconds) else str(client.get(f"/api/chats/{chat}").json().get("turn"))


def answer_of(blocks: list[dict[str, Any]], call: dict[str, Any]) -> str:
    """The engine's answer to one tool call, found by the call's id."""
    for block in blocks:
        content = block["content"]
        if block.get("type") == "tool" and str(content.get("id")) == str(call.get("id")):
            if "result" in content:
                return str(content["result"])
    return ""


def draft_item(blocks: list[dict[str, Any]]) -> str | None:
    """The last draft the chat saved that the engine accepted. A call whose answer carries no
    `revision` was refused, so it is not a save."""
    saved = [
        call
        for call in tool_calls(blocks, "mcp__qmx_workflows__drafts_put")
        if '"revision"' in answer_of(blocks, call)
    ]
    if not saved:
        return None
    found = saved[-1].get("arguments", {}).get("workflow_id")
    return str(found) if found else None


def node_types(definition: dict[str, Any]) -> list[str]:
    return [str(node.get("type")) for node in definition.get("nodes", [])]


def tokens(run: dict[str, Any]) -> dict[str, Any]:
    return dict((run.get("totals") or {}).get("tokens") or {})


def turn(
    log: Log,
    client: httpx.Client,
    chat: str,
    text: str,
    *,
    allow_publish: bool,
    needs_draft: bool,
    pressed: dict[int, dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], float]:
    """One operator turn to its end, pressing each ask once, and the draft id it saved. `pressed`
    carries across a lane's turns, because an answered ask stays in the log as an asking one."""
    began = ask_turn(client, chat, text)
    log(f"request: {text}")
    asks: list[dict[str, Any]] = []
    item = ""
    deadline = time.monotonic() + TURN_S
    while time.monotonic() < deadline:
        asks += handle_asks(log, client, chat, pressed, allow_publish)
        item = draft_item(chat_blocks(chat)) or item
        if client.get(f"/api/chats/{chat}").json().get("turn") == "idle":
            if not needs_draft or item:
                break
            time.sleep(5)
            asks += handle_asks(log, client, chat, pressed, allow_publish)
            item = draft_item(chat_blocks(chat)) or item
            break
        time.sleep(3)
    wait_idle(client, chat, 60)
    return item, asks, time.perf_counter() - began


def show(log: Log, blocks: list[dict[str, Any]]) -> None:
    for block in blocks:
        log(f"  [{block['type']}] {json.dumps(block['content'], ensure_ascii=False)[:240]}")


def build(
    log: Log, client: httpx.Client, chat: str, pressed: dict[int, dict[str, Any]]
) -> tuple[str, float, dict[str, Any]]:
    """Lane 2. The request, the draft, the ask check, and the perf number."""
    name = run_item("ecb-digest")
    item, asks, seconds = turn(
        log, client, chat, REQUEST.format(item=name), allow_publish=False, needs_draft=True,
        pressed=pressed,
    )  # fmt: skip
    if not item:
        log(f"no draft saved for {name}; asking once more before the check")
        item, more, spent = turn(
            log, client, chat, REBUILD.format(item=name), allow_publish=False, needs_draft=True,
            pressed=pressed,
        )  # fmt: skip
        asks += more
        seconds += spent
    blocks = chat_blocks(chat)
    show(log, blocks)
    log(f"{len(blocks)} blocks; {len(asks)} asks")
    others = [str(ask["content"].get("tool")) for ask in asks if "workflows__put" not in str(ask)]
    log.check(
        "the build, validation and test run asked him nothing; the only ask is the publish row",
        not others,
        {"asks": [str(ask["content"].get("tool")) for ask in asks], "unexpected": others},
    )
    log.check("the chat saved a draft through workflows_drafts_put", item != "", item)
    if not item:
        return "", seconds, {}
    draft = draft_of(client, item)
    kinds = node_types(draft.get("definition", {}))
    log(f"draft {item} revision {draft.get('revision')} state {draft.get('state')} nodes {kinds}")
    log.check("the draft holds three nodes or more", len(kinds) >= 3, kinds)
    checked = client.post(
        "/api/workflows/validate",
        json={"definition": draft.get("definition"), "files": draft.get("files", {})},
    ).json()
    log(f"validation: {json.dumps(checked)[:300]}")
    log.check(
        "a fresh validation of the saved draft finds no problem",
        checked.get("valid") is True and checked.get("problems") == [],
        checked.get("problems"),
    )
    tested = until(
        lambda: draft_of(client, item).get("state") == "tested",
        TURN_S,
    )
    log.check("the draft reads tested", bool(tested), draft_of(client, item).get("state"))
    runs = runs_of(client, item)
    done = [run for run in runs if run.get("status") == "passed"]
    log(f"runs of {item}: {[(r.get('run_id'), r.get('mode'), r.get('status')) for r in runs]}")
    log.check(
        "a test run of it passed and nothing ran live",
        bool(done) and all(run.get("mode") == "test" for run in runs),
        [(r.get("mode"), r.get("status")) for r in runs],
    )
    agent_ref = f"refs/agents/{chat}/{item}"
    landed = [line for line in refs_log() if agent_ref in line]
    log(f"the Library's ref log holds the agent ref: {len(landed)} moves")
    log.check("the draft landed on the agent ref", bool(landed), agent_ref)
    log(f"request to tested draft: {seconds:.1f} s")
    return item, seconds, {} if not done else done[-1]


def card_in(answer: str) -> dict[str, Any] | None:
    """The card a `user`-only row answers a non-`user` caller with, or None."""
    try:
        found = json.loads(answer)
    except ValueError:
        return None
    return found if isinstance(found, dict) and found.get("card") else None


def publish(
    log: Log, client: httpx.Client, chat: str, item: str, pressed: dict[int, dict[str, Any]]
) -> None:
    """Lane 3. His publish click, allowed, and the card the row returns."""
    _, asks, seconds = turn(
        log, client, chat, PUBLISH, allow_publish=True, needs_draft=False, pressed=pressed
    )
    blocks = chat_blocks(chat)
    show(log, blocks)
    log(f"asks in the publish turn: {[str(ask['content'].get('tool')) for ask in asks]}")
    answers = [answer_of(blocks, call) for call in tool_calls(blocks, "mcp__qmx_workflows__put")]
    cards = [card for answer in answers for card in [card_in(answer)] if card]
    log(f"publish answers: {[answer[:200] for answer in answers]}")
    log.check("the publish row answered with a card", bool(cards), cards[-1] if cards else answers[-1:])
    versions = client.get(f"/api/workflows/{item}/versions").json()
    log(f"versions of {item}: {len(versions)}")
    log.check("nothing was published", versions == [], versions)
    log(f"publish lane: {seconds:.1f} s")


def script_only(log: Log, client: httpx.Client, chat: str, pressed: dict[int, dict[str, Any]]) -> None:
    """Lane 4. A request with no model step anywhere, and a run that spends nothing."""
    name = run_item("trades-totals")
    item, asks, seconds = turn(
        log, client, chat, SCRIPT_REQUEST.format(item=name), allow_publish=False, needs_draft=True,
        pressed=pressed,
    )  # fmt: skip
    blocks = chat_blocks(chat)
    show(log, blocks)
    others = [str(ask["content"].get("tool")) for ask in asks if "workflows__put" not in str(ask)]
    log.check(
        "the script-only build asked him nothing but the publish row",
        not others,
        {"asks": [str(ask["content"].get("tool")) for ask in asks], "unexpected": others},
    )
    log.check("the chat saved a draft", item != "", item)
    if not item:
        return
    draft = draft_of(client, item)
    kinds = node_types(draft.get("definition", {}))
    log(f"draft {item} revision {draft.get('revision')} state {draft.get('state')} nodes {kinds}")
    log.check(
        "the draft holds no model-bearing node",
        not [kind for kind in kinds if kind in MODEL_NODES],
        kinds,
    )
    tested = until(lambda: draft_of(client, item).get("state") == "tested", TURN_S)
    log.check("the script-only draft reads tested", bool(tested), draft_of(client, item).get("state"))
    runs = runs_of(client, item)
    log(f"runs of {item}: {[(r.get('run_id'), r.get('mode'), r.get('status')) for r in runs]}")
    passed = [run for run in runs if run.get("status") == "passed"]
    spent = tokens(passed[-1]) if passed else {}
    log(f"the test run's tokens: {spent or '{}'}")
    log.check(
        "the test run spent no tokens",
        bool(passed) and not spent,
        {"status": [r.get("status") for r in runs], "tokens": spent},
    )
    log(f"script-only lane: {seconds:.1f} s")


LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
LOCK_WAIT_S: Final = 3600.0
LOCK_POLL_S: Final = 20.0


@contextlib.contextmanager
def lane_lock(say: Callable[[str], None]) -> Iterator[None]:
    """The engine lanes' lock: one lane on the ship home at a time, waited for, never doubled."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit("BLOCKED: the lane lock stayed held for an hour") from None
            say(f"lane lock held by another lane; retry in {LOCK_POLL_S:.0f} s")
            time.sleep(LOCK_POLL_S)
    say(f"took {LOCK}")
    try:
        yield
    finally:
        LOCK.rmdir()
        say(f"removed {LOCK}")


def summary(log: Log, client: httpx.Client, chat: str, item: str) -> None:
    """What he is looking at on the card: the tested draft and the row's publish card."""
    draft = draft_of(client, item)
    definition = draft.get("definition", {})
    named = [
        (node.get("id"), node.get("name"), node.get("type")) for node in definition.get("nodes", [])
    ]
    files = sorted(draft.get("files", {}))
    log(f"the draft he sees: {item} ({definition.get('name')})")
    log(f"  state {draft.get('state')} revision {draft.get('revision')}")
    log(f"  nodes {named}")
    log(f"  files {files}")
    runs = runs_of(client, item)
    log(f"  runs {[(r.get('mode'), r.get('status')) for r in runs]}")
    blocks = chat_blocks(chat)
    cards = [
        card
        for call in tool_calls(blocks, "mcp__qmx_workflows__put")
        for card in [card_in(answer_of(blocks, call))]
        if card
    ]
    log(f"  publish card {cards[-1] if cards else 'none'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="TPL2's lanes 2 to 4")
    parser.add_argument("--lane", type=int, choices=sorted(LANES), default=2)
    args = parser.parse_args()
    log = Log(LANES[args.lane])
    boot()
    use_fake_home()
    require_login(log)
    before = settings_sha()
    log(f"ship home settings.toml sha256 before: {before}")
    bearer = secrets.token_urlsafe(32)
    pressed: dict[int, dict[str, Any]] = {}
    with lane_lock(log):
        try:
            with served(log, bearer) as client:
                chat = new_chat(client, f"TPL2 lane {args.lane}", LANES[args.lane])
                log(f"copilot chat {chat} on claude/haiku, default permission mode")
                if args.lane == 2:
                    item, seconds, _ = build(log, client, chat, pressed)
                    log(f"PERF request to tested draft: {seconds:.1f} s for {item or 'no draft'}")
                elif args.lane == 3:
                    item, seconds, _ = build(log, client, chat, pressed)
                    log(f"the build before the publish: {seconds:.1f} s for {item or 'no draft'}")
                    log.check("the draft exists to publish", item != "", item)
                    if item:
                        publish(log, client, chat, item, pressed)
                        summary(log, client, chat, item)
                else:
                    script_only(log, client, chat, pressed)
        finally:
            after = settings_sha()
            log.check("the ship home's settings.toml is unchanged", after == before, after[:16])
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
