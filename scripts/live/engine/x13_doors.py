"""EP13's live lanes: the ControlService doors and the engine host.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x13_doors.py [--base REV] [lane ...]`
Lanes are `regression rest tools fallback cancel menu perf`; none named runs all. Each writes
`evidence/ep13/<ENGINE_LOG_PREFIX>ep13-<lane>.log`, and the script exits 1 if any lane failed.

- `regression` (lane 1): the harness is byte-identical to its base and its suite, `test_tools.py`
  included, passes with the same counts at base and head.
- `rest` (lane 2): `python -m qmx_engine.host` on a throwaway home; over REST the script chain is
  saved as a draft, validated, tested, published and run live, and each call answers with the
  engine's document.
- `tools` (lane 3): a default-mode chat on the fake model calls `workflow_drafts_put`,
  `workflow_tests_run` and `workflows_put` through the `qmx` tools, with an allow rule for the two
  quiet rows as "always allow" leaves one. The draft saves and the test passes with no ask, and
  publish raises exactly one ask.
- `fallback` (lane 3): a `workflow` object saved with `library_save` and a new
  `meta.test_requested` is imported as a draft and test-run on its own.
- `cancel` (lane 4): a run held on a `wait` node is cancelled over REST and ends `stopped`
  (reason `operator`); `GET /api/runs` lists none of the engine's runs.
- `menu` (lanes 5 to 9): plain `qma.serve` still answers 501; REST explain equals the CLI's; a
  second host on one home is refused by pid; a run's events stream in `seq` order; no bearer, 401.
- `perf`: start to a healthy `/api/health`, three starts of `qma.serve` first, then the host.

No model, no key, no ship home. Hosts run on throwaway homes through `lane_host.py`, with a
bearer made for each home and kept in its `lane-bearer` file; the operator's control token in the
OS vault is never read.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import secrets
import socket
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Final

import httpx
import psutil
from common import LIVE_QMA, Log, boot, live, throwaway_home
from ep2_lanes import AGENTS, ENGINE, clean_env
from ep2_lanes import regression as harness_regression
from lane_host import BEARER_FILE
from qmx_engine.ledger.store import Reader

PR: Final = "ep13"
BASE: Final = "e34277ee77469e5058e66833dd0628782eed1e2a"
BASE_TREE: Final = Path("D:/QMX-worktrees/eng-hg2")
LANE_HOST: Final = Path(__file__).with_name("lane_host.py")
CHAIN: Final = ENGINE / "tests" / "fixtures" / "workflows" / "script-chain"
START_S: Final = 90.0


def chain(item: str) -> dict[str, Any]:
    from qmx_engine.ports.library import Bundle  # noqa: PLC0415

    bundle = Bundle.read(CHAIN)
    files = {ref: data.decode() for ref, data in bundle.files.items()}
    return {"definition": bundle.definition | {"id": item}, "files": files}


def waiting(item: str) -> dict[str, Any]:
    return {
        "schema": "qmx.workflow/1",
        "id": item,
        "name": "Wait an hour",
        "nodes": [
            {"id": "start", "name": "Start", "type": "trigger", "typeVersion": 1,
             "parameters": {"kinds": ["manual"]}},
            {"id": "pause", "name": "Pause", "type": "wait", "typeVersion": 1,
             "parameters": {"seconds": 3600}},
        ],
        "connections": {"Start": {"main": [[{"node": "Pause", "port": "in", "map": "one"}]]}},
    }  # fmt: skip


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def bearer(home: Path) -> dict[str, str]:
    """The home's own lane bearer, made on first use."""
    path = home / BEARER_FILE
    if not path.exists():
        path.write_text(secrets.token_urlsafe(32), encoding="utf-8")
    return {"Authorization": f"Bearer {path.read_text(encoding='utf-8')}"}


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


@contextlib.contextmanager
def started(
    log: Log, module: list[str], home: Path, slug: str
) -> Iterator[tuple[httpx.Client, subprocess.Popen[bytes], float]]:
    """A host process on `home`, its client, and the seconds it took to answer `/api/health`."""
    port = free_port()
    command = [sys.executable, str(LANE_HOST), *module, "serve", "--home", str(home)]
    command += ["--port", str(port)]
    output = (log.path.parent / f"{log.path.stem}-{slug}.out").open("wb")
    began = time.perf_counter()
    process = subprocess.Popen(command, cwd=AGENTS, env=clean_env(), stdout=output, stderr=output)
    headers = bearer(home)
    while healthy(port, headers) is None:
        if process.poll() is not None or time.perf_counter() - began > START_S:
            output.close()
            kill_tree(process.pid)
            raise SystemExit(f"{' '.join(module)} did not start; see {output.name}")
        time.sleep(0.05)
    seconds = time.perf_counter() - began
    log(f"{' '.join(module)} pid {process.pid} healthy on port {port} after {seconds:.2f} s")
    client = httpx.Client(base_url=f"http://127.0.0.1:{port}", headers=headers, timeout=60)
    try:
        yield client, process, seconds
    finally:
        client.close()
        kill_tree(process.pid)
        output.close()


def host(log: Log, home: Path, slug: str = "host") -> Any:
    return started(log, ["qmx_engine.host"], home, slug)


def reply(log: Log, name: str, found: httpx.Response) -> Any:
    body = found.json()
    log(f"{name}: http {found.status_code} {json.dumps(body)[:300]}")
    return body


def until(predicate: Callable[[], Any], seconds: float = 30) -> Any:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if found := predicate():
            return found
        time.sleep(0.25)
    return None


def regression(log: Log, base: str) -> None:
    harness_regression(log, base, BASE_TREE)


def rest(log: Log) -> None:
    home = throwaway_home(PR, "rest")
    with host(log, home) as (client, _, _):
        saved = reply(
            log, "draft put", client.put("/api/workflows/chain/draft", json=chain("chain"))
        )
        log.check(
            "the draft saves as the engine's draft document",
            (saved.get("workflow_id"), saved.get("revision"), saved.get("state"))
            == ("chain", 1, "validated"),
            {k: saved.get(k) for k in ("workflow_id", "revision", "state", "content_hash")},
        )
        checked = reply(log, "validate", client.post("/api/workflows/validate", json=chain("x")))
        log.check(
            "validate answers with the engine's result",
            checked.get("valid") is True and checked.get("content_hash") == saved["content_hash"],
            checked,
        )
        tested = reply(log, "test", client.post("/api/workflows/chain/test"))
        report = tested.get("report") or {}
        log.check(
            "the test run passes and binds its report to the draft's hash",
            (tested["run"]["mode"], report.get("status"), report.get("content_hash"))
            == ("test", "passed", saved["content_hash"]),
            tested["run"],
        )
        published = reply(log, "publish", client.put("/api/workflows/chain", json={}))
        log.check(
            "publish freezes version 1.0.0",
            (published.get("semver"), published.get("state"), published.get("tested"))
            == ("1.0.0", "published", True),
            published,
        )
        ran = reply(log, "live run", client.post("/api/workflows/chain/run"))
        log.check(
            "the live run of the version finishes passed",
            (ran.get("mode"), ran.get("status"), ran.get("object_id"))
            == ("live", "passed", published["object_id"]),
            ran,
        )
        listed = reply(log, "workflow runs", client.get("/api/workflow-runs"))
        log.check(
            "GET /api/workflow-runs lists the live run and the test run",
            [(r["run_id"], r["mode"]) for r in listed]
            == [(ran["run_id"], "live"), (tested["run"]["run_id"], "test")],
            [(r["run_id"], r["mode"], r["status"]) for r in listed],
        )
        got = reply(log, "workflow get", client.get("/api/workflows/chain"))
        log.check(
            "GET /api/workflows/chain reads the published definition",
            got.get("state") == "published" and got["definition"]["id"] == "chain",
            got.get("state"),
        )


def tools(log: Log) -> None:
    helpers = qma_helpers()
    live.use_fake_key()
    asyncio.run(tools_chat(log, *helpers))


def qma_helpers() -> tuple[Any, Any, Any]:
    """`approval_lane`, `fake_model` and `money_lane` from `scripts/live/qma`, which import their
    own `common`; that name is this folder's here, so it points at theirs while they load."""
    live.SCRATCH  # noqa: B018 - loads scripts/live/qma/common.py
    ours = sys.modules["common"]
    sys.path.append(str(LIVE_QMA))
    sys.modules["common"] = live.module
    try:
        import approval_lane  # noqa: PLC0415
        import fake_model  # noqa: PLC0415
        import money_lane  # noqa: PLC0415
    finally:
        sys.modules["common"] = ours
    return approval_lane, fake_model, money_lane


async def tools_chat(log: Log, lane: Any, fake_model: Any, money: Any) -> None:
    from qmx_engine.control_door import EngineDoor  # noqa: PLC0415

    quiet = ["mcp__qmx__workflow_drafts_put", "mcp__qmx__workflow_tests_run"]
    calls = [
        (quiet[0], {"workflow_id": "chain", "graph": chain("chain")}),
        (quiet[1], {"workflow_id": "chain"}),
        ("mcp__qmx__workflows_put", {"workflow_id": "chain", "graph": {}}),
    ]
    script = [fake_model.Turn([fake_model.tool_use(name, args)]) for name, args in calls]
    script.append(fake_model.Turn([fake_model.text("calls done")]))
    root, fake, session = await lane.fake_session("ep13-tools", script, tools=["Read"])
    try:
        live.put_claude(root, {"permissions": {"allow": quiet}})
        chat = await lane.new_chat(session, "ep13 tools", live.SCRATCH / "ep13-tools-ws")
        async with EngineDoor.open(session.control), lane.Host(session) as served:
            answered = await lane.answered_turn(log, served, chat, lane.always(lane.ALLOW_ONCE))
        asked = [ask["tool"] for ask in answered.asks]
        log.check(
            "draft save and test run raise no ask; publish raises exactly one",
            asked == ["mcp__qmx__workflows_put"],
            asked,
        )
        said = {tool: (error, text) for tool, _, error, text in money.results(fake).values()}
        for tool, (error, text) in said.items():
            log(f"  {tool} error={error} -> {text[:200]!r}")
        draft = json.loads(said[quiet[0]][1])
        test = json.loads(said[quiet[1]][1])
        version = json.loads(said["mcp__qmx__workflows_put"][1])
        log.check(
            "each tool returns the engine's result",
            (draft["state"], test["report"]["status"], version["semver"])
            == ("validated", "passed", "1.0.0"),
            (draft["state"], test["report"]["status"], version["semver"]),
        )
    finally:
        await session.harness.close()
        fake.stop()


def fallback(log: Log) -> None:
    home = throwaway_home(PR, "fallback")
    with host(log, home) as (client, _, _):
        content = chain("saved")
        content["definition"]["meta"] = {"test_requested": "nonce-1"}
        item = {"title": "saved", "kind": "workflow", "content": content}
        reply(log, "library_save", client.post("/api/library", json=item))

        def passed() -> list[Any]:
            found = client.get("/api/workflow-runs", params={"workflow_id": "saved"}).json()
            return [r for r in found if r["status"] == "passed"]

        runs = until(passed) or []
        log.check(
            "the saved workflow is test-run on its own",
            [r["mode"] for r in runs] == ["test"],
            [(r["run_id"], r["mode"], r["status"]) for r in runs],
        )
        draft = reply(log, "draft", client.get("/api/workflows/saved/draft"))
        log.check("its draft reads tested", draft.get("state") == "tested", draft.get("state"))
        reply(log, "same save again", client.post("/api/library", json=item))
        time.sleep(3)
        again = passed()
        log.check("saving the same object again starts nothing", len(again) == 1, len(again))


def cancel(log: Log) -> None:
    home = throwaway_home(PR, "cancel")
    with host(log, home) as (client, _, _):
        reply(log, "draft put", client.put("/api/workflows/hold/draft", json=waiting("hold")))
        run = reply(log, "test", client.post("/api/workflows/hold/test"))["run"]
        log.check(
            "the run waits on its wait node",
            (run["status"], run["reason"]) == ("waiting", "wait"),
            run,
        )
        stopped = reply(log, "cancel", client.post(f"/api/workflow-runs/{run['run_id']}/cancel"))
        log.check(
            "the cancelled run ends stopped, reason operator",
            (stopped.get("status"), stopped.get("reason")) == ("stopped", "operator"),
            stopped,
        )
        with Reader.open(home) as reader:
            kinds = [event.kind for event in reader.events(run["run_id"])]
        log(f"ledger kinds of the run: {kinds}")
        log.check("the ledger ends run_cancelled", kinds[-1:] == ["run_cancelled"], kinds[-1:])
        remote = reply(log, "GET /api/runs", client.get("/api/runs"))
        engine = {run["run_id"]}
        log.check(
            "GET /api/runs lists none of the engine's runs",
            not engine & {str(r.get("id")) for r in remote},
            [r.get("id") for r in remote],
        )


def explain_cli(home: Path, run_id: str) -> dict[str, Any]:
    command = [sys.executable, "-m", "qmx_engine", "explain", run_id, "--home", str(home)]
    done = subprocess.run(
        [*command, "--json"], cwd=AGENTS, env=clean_env(), capture_output=True, text=True
    )
    return json.loads(done.stdout) if done.returncode == 0 else {"error": done.stdout}


def menu(log: Log) -> None:
    plain = throwaway_home(PR, "menu-serve")
    with started(log, ["qma.serve"], plain, "qma-serve") as (client, _, _):
        found = client.put("/api/workflows/x", json={"semver": "1.0.0"})
        log.check(
            "lane 5: plain qma.serve still answers 501",
            (found.status_code, found.json()["error"]["code"]) == (501, "not_implemented"),
            found.status_code,
        )
    home = throwaway_home(PR, "menu")
    with host(log, home) as (client, _, _):
        serving = client.get("/api/health").json()["pid"]
        client.put("/api/workflows/chain/draft", json=chain("chain"))
        run = client.post("/api/workflows/chain/test").json()["run"]
        over_rest = client.get(f"/api/workflow-runs/{run['run_id']}/explain").json()
        log.check(
            "lane 6: REST explain equals the CLI's explain",
            over_rest == explain_cli(home, run["run_id"]),
            over_rest.get("status"),
        )
        second = subprocess.run(
            [
                sys.executable,
                str(LANE_HOST),
                "qmx_engine.host",
                "serve",
                "--home",
                str(home),
                "--port",
                "1",
            ],
            cwd=AGENTS,
            env=clean_env(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        log(f"second host: exit {second.returncode} {second.stderr.strip()}")
        log.check(
            "lane 7: a second host on the home is refused by the recorded pid",
            second.returncode == 1 and f"PID {serving}" in second.stderr,
            (second.returncode, serving),
        )
        streamed = client.get(
            "/api/engine/events", params={"run_id": run["run_id"], "max_events": 12}
        )
        frames = [
            json.loads(line[5:]) for line in streamed.text.splitlines() if line[:5] == "data:"
        ]
        seqs = [frame["seq"] for frame in frames]
        nodes = [f"{f['kind']}:{f['data'].get('node_id')}" for f in frames if "node" in f["kind"]]
        log(f"events: {nodes}")
        log.check("lane 8: events arrive in seq order", seqs == list(range(1, 13)), seqs)
        bare = httpx.Client(base_url=str(client.base_url), timeout=10)
        codes = [bare.get(path).status_code for path in ("/api/workflow-runs", "/api/triggers")]
        bare.close()
        log.check("lane 9: no bearer, 401", codes == [401, 401], codes)


def perf(log: Log) -> None:
    def three(module: list[str], slug: str) -> list[float]:
        home = throwaway_home(PR, f"perf-{slug}")
        times = []
        for n in range(3):
            with started(log, module, home, f"{slug}-{n}") as (_, _, seconds):
                times.append(seconds)
        return times

    baseline = three(["qma.serve"], "qma-serve")
    head = three(["qmx_engine.host"], "host")
    log(f"qma.serve start to healthy, s: {[round(t, 2) for t in baseline]}")
    log(f"engine host start to healthy, s: {[round(t, 2) for t in head]}")
    log(
        f"perf median: qma.serve {statistics.median(baseline):.2f} s, "
        f"engine host {statistics.median(head):.2f} s (recorded, not gated)"
    )


LANES: Final = {
    "rest": rest,
    "tools": tools,
    "fallback": fallback,
    "cancel": cancel,
    "menu": menu,
    "perf": perf,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    parser.add_argument("lanes", nargs="*", choices=["regression", *LANES])
    args = parser.parse_args()
    prefix = os.environ.get("ENGINE_LOG_PREFIX", "")
    boot()
    os.environ["ENGINE_LOG_PREFIX"] = prefix  # the boot scrub drops it
    failed = 0
    for name in args.lanes or ["regression", *LANES]:
        log = Log(PR, f"ep13-{name}")
        if name == "regression":
            regression(log, args.base)
        else:
            LANES[name](log)
        failed += log.verdict()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
