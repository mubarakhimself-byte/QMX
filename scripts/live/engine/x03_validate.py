"""EP3's live lanes and perf probe: the qmx.workflow/1 validator through `python -m qmx_engine`.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x03_validate.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression hash bad money token overlay draft schema unavailable broadcast refusals
perf`; none
named runs all. Each lane writes `evidence/ep3/<ENGINE_LOG_PREFIX>ep3-<lane>.log`, and the script
exits 1 if any lane failed. No lane needs a model, a key or the ship home.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

import jsonschema
from common import Log, throwaway_home
from ep2_lanes import GIT, REPO, clean_env, git
from qmx_engine.definition.folder import load
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.overlay import resolve
from qmx_engine.definition.registry import REGISTRY
from qmx_engine.definition.validate import runnable, validate

AGENTS: Final = REPO / "qmx-agents"
ENGINE: Final = AGENTS / "packages" / "qmx-engine"
FIXTURES: Final = ENGINE / "tests" / "fixtures" / "workflows"
SCHEMA: Final = ENGINE / "src" / "qmx_engine" / "definition" / "schema" / "qmx.workflow.1.json"
HARNESS: Final = "qmx-agents/packages/qma-harness"
PERF_NODES: Final = 50
PERF_ROUNDS: Final = 20


def cli(log: Log, folder: Path, *flags: str, quiet: bool = False) -> tuple[int, str]:
    done = subprocess.run(
        [sys.executable, "-m", "qmx_engine", "validate", str(folder), *flags],
        cwd=AGENTS,
        env=clean_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if not quiet:
        log(f"$ python -m qmx_engine validate {folder.name} {' '.join(flags)}".rstrip())
        for line in (done.stdout + done.stderr).splitlines():
            log(f"  | {line}")
    return done.returncode, done.stdout


def codes(stdout: str) -> list[str]:
    return [line.split(" ", 1)[0] for line in stdout.splitlines() if not line.startswith("ok ")]


def copy(name: str, slug: str) -> Path:
    return Path(shutil.copytree(FIXTURES / name, throwaway_home("ep3", slug) / name))


def rewrite(folder: Path, change: Callable[[dict[str, Any]], None]) -> None:
    path = folder / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def regression(log: Log, base: str, trunk: str) -> None:
    on_trunk = subprocess.run(
        [
            GIT,
            "cat-file",
            "-e",
            f"{trunk}:qmx-agents/packages/qmx-engine/src/qmx_engine/definition/validate.py",
        ],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    log.check("trunk has no validator to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    code, out = cli(log, FIXTURES / "paper-scout-min")
    log.check(
        "paper-scout-min validates at head", code == 0 and out.startswith("ok sha256:"), out.strip()
    )


def hashes(log: Log) -> None:
    folder = copy("paper-scout-min", "hash")
    first, second = (cli(log, folder)[1].strip() for _ in range(2))

    def move(document: dict[str, Any]) -> None:
        for node in document["nodes"]:
            node["position"] = [node["position"][0] * 2 + 7, 480]

    rewrite(folder, move)
    moved = cli(log, folder)[1].strip()
    prompt = folder / "prompts" / "triage.md"
    prompt.write_bytes(b"S" + prompt.read_bytes()[1:])
    edited = cli(log, folder)[1].strip()
    log.check(
        "two validations print the same hash",
        first == second and first.startswith("ok sha256:"),
        first,
    )
    log.check("moving every node keeps the hash", moved == first, moved)
    log.check(
        "a one-byte prompt edit changes the hash",
        edited.startswith("ok sha256:") and edited != first,
        edited,
    )


def bad(log: Log) -> None:
    folders = sorted(FIXTURES.glob("bad-*"))
    log(f"{len(folders)} bad fixtures")
    for folder in folders:
        expected = json.loads((folder / "definition.json").read_text(encoding="utf-8"))["meta"][
            "expect"
        ]
        code, out = cli(log, folder)
        log.check(
            f"{folder.name} fails with {expected}", code == 1 and codes(out) == expected, codes(out)
        )


def money(log: Log) -> None:
    folder = FIXTURES / "bad-money"
    action = json.loads((folder / "definition.json").read_text(encoding="utf-8"))["nodes"][1][
        "parameters"
    ]["action"]
    log(f"llm node parameter action = {action!r}")
    code, out = cli(log, folder)
    log.check(
        "lint refuses the llm node's place_order with money_act",
        code == 1 and codes(out) == ["money_act"],
        codes(out),
    )


def token(log: Log) -> None:
    folder = copy("bad-money", "token")
    literal = "sk-" + "Qx7" * 13 + "Z"

    def plant(document: dict[str, Any]) -> None:
        document["nodes"][1]["parameters"] = {"prompt": "Summarise.", "api": literal}

    rewrite(folder, plant)
    code, out = cli(log, folder, quiet=True)
    log(f"$ python -m qmx_engine validate {folder.name}  (output checked before logging)")
    log.check("the planted literal is sk- plus 40 characters", len(literal) == 43, len(literal))
    log.check(
        "the output does not echo the literal",
        literal not in out,
        "not echoed" if literal not in out else "ECHOED",
    )
    for line in out.splitlines():
        log(f"  | {line.replace(literal, '[literal]')}")
    log.check(
        "lint refuses it with secret_literal",
        code == 1 and codes(out) == ["secret_literal"],
        codes(out),
    )


def overlay(log: Log) -> None:
    root = throwaway_home("ep3", "overlay")
    parent = json.loads(
        (FIXTURES / "paper-scout-min" / "definition.json").read_text(encoding="utf-8")
    )
    variant = {
        "schema": "qmx.workflow/1",
        "id": "paper-scout-fx",
        "name": "Paper scout for FX papers",
        "extends": {
            "workflow_item": "paper-scout",
            "object_id": "obj-7f3a",
            "patches": [
                {"op": "replace", "path": "/nodes/2/parameters/max_items", "value": 3},
                {"op": "add", "path": "/nodes/3/parameters/tools/-", "value": "Grep"},
            ],
        },
    }
    resolved = resolve(variant, parent)
    folder = Path(shutil.copytree(FIXTURES / "paper-scout-min", root / "paper-scout-fx"))
    (folder / "definition.json").write_text(
        json.dumps(resolved.snapshot, indent=2), encoding="utf-8"
    )
    code, out = cli(log, folder)
    log.check(
        "the resolved snapshot validates", code == 0 and out.startswith("ok sha256:"), out.strip()
    )
    log.check(
        "it records its parent",
        resolved.variant_of == ("paper-scout", "obj-7f3a"),
        resolved.variant_of,
    )
    snapshot: Any = resolved.snapshot
    max_items = snapshot["nodes"][2]["parameters"]["max_items"]
    log.check("max_items was patched to 3", max_items == 3, max_items)


def draft(log: Log) -> None:
    folder = FIXTURES / "draft-note"
    code, out = cli(log, folder)
    log.check("a draft with a note and an unconnected node validates", code == 0, out.strip())
    code, out = cli(log, folder, "--publish")
    expected = ["note_at_publish", "unconnected_at_publish"]
    log.check(
        f"the publish check refuses both with {expected}",
        code == 1 and codes(out) == expected,
        codes(out),
    )


def schema(log: Log) -> None:
    document = json.loads(
        (FIXTURES / "paper-scout-min" / "definition.json").read_text(encoding="utf-8")
    )
    shipped = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(document, shipped)
        log.check("paper-scout-min validates against the shipped JSON schema", True, SCHEMA.name)
    except jsonschema.ValidationError as error:
        log.check("paper-scout-min validates against the shipped JSON schema", False, error.message)


def unavailable(log: Log) -> None:
    folder = FIXTURES / "draft-rlm"
    code, out = cli(log, folder)
    rlm = REGISTRY.kind("rlm")
    refused = runnable(Workflow.model_validate(load(folder).document))
    log.check("a draft using rlm validates", code == 0, out.strip())
    log.check("the registry reports rlm unavailable", rlm is not None and not rlm.available, rlm)
    log.check(
        "a run would refuse it with kind_not_available",
        ("kind_not_available", "nodes[1].type") in [(p.code, p.path) for p in refused],
        [(p.code, p.path) for p in refused],
    )


def broadcast(log: Log) -> None:
    code, out = cli(log, FIXTURES / "bad-broadcast")
    log.check(
        "broadcast of a list into an agent fails with chunk_required",
        code == 1 and codes(out) == ["chunk_required"],
        codes(out),
    )
    folder = copy("bad-broadcast", "broadcast")

    def chunk(document: dict[str, Any]) -> None:
        document["connections"]["List papers"]["main"][0][0] |= {
            "map": "chunk",
            "chunk": {"by": "items", "size": 5},
        }

    rewrite(folder, chunk)
    code, out = cli(log, folder)
    log.check("the same fixture with map: chunk validates", code == 0, out.strip())


REFUSALS: Final = {
    "bad-nested-fan-out": ("nesting_unsupported", "node again"),
    "bad-loop-over-fan-out": ("nesting_unsupported", "loop cycle"),
    "bad-loop-in-loop": ("nesting_unsupported", "loop inner"),
    "bad-grader-llm": ("mode_unavailable", "node judge"),
}
"""BUG2's refusal fixtures: the code each must fail with and the node its line must name."""


def refusals(log: Log) -> None:
    for name, (expected, named) in REFUSALS.items():
        code, out = cli(log, FIXTURES / name)
        log.check(
            f"{name} is refused with {expected} and names {named}",
            code == 1 and codes(out) == [expected] and named in out,
            out.strip(),
        )


def perf(log: Log) -> None:
    root = throwaway_home("ep3", "perf") / "fifty"
    root.mkdir()
    nodes = [{"id": "n0", "name": "Start", "type": "trigger", "typeVersion": 1, "position": [0, 0]}]
    connections: dict[str, Any] = {}
    for i in range(1, PERF_NODES):
        nodes.append(
            {
                "id": f"n{i}",
                "name": f"Step {i}",
                "type": "script",
                "typeVersion": 1,
                "position": [i * 200, 0],
            }
        )
        connections[nodes[i - 1]["name"]] = {
            "main": [[{"node": f"Step {i}", "port": "in", "map": "one"}]]
        }
    document = {
        "schema": "qmx.workflow/1",
        "id": "fifty",
        "name": "Fifty nodes",
        "nodes": nodes,
        "connections": connections,
    }
    (root / "definition.json").write_text(json.dumps(document), encoding="utf-8")
    started = time.perf_counter()
    code, out = cli(log, root)
    whole = (time.perf_counter() - started) * 1000
    log.check(f"the {PERF_NODES}-node fixture validates", code == 0, out.strip())
    validate(load(root))
    rounds: list[float] = []
    for _ in range(PERF_ROUNDS):
        started = time.perf_counter()
        problems = validate(load(root))
        rounds.append((time.perf_counter() - started) * 1000)
    log.check("in-process validation finds no problem", problems == [], len(problems))
    median, slowest = statistics.median(rounds), max(rounds)
    log(
        f"perf: one timed CLI validate of {PERF_NODES} nodes {whole:.0f} ms, process start included"
    )
    log(f"perf: in-process load+validate median {median:.2f} ms, max {slowest:.2f} ms")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep2")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base, trunk = git("rev-parse", args.base), git("rev-parse", args.trunk)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, trunk),
        "hash": hashes,
        "bad": bad,
        "money": money,
        "token": token,
        "overlay": overlay,
        "draft": draft,
        "schema": schema,
        "unavailable": unavailable,
        "broadcast": broadcast,
        "refusals": refusals,
        "perf": perf,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep3", f"ep3-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
