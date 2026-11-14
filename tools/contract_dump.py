"""The contract files the UI and the ship kit read: generated from the code, never edited by hand.

    python tools/contract_dump.py            # rewrite contracts/host-openapi.json and apps.json
    python tools/contract_dump.py --check    # exit 1 with a diff summary when either file is stale

`contracts/host-openapi.json` is the OpenAPI schema of the one REST app the host serves on This PC
(role `pc`). The host serves it only at run time, behind its bearer; this script builds the same
app in-process instead, on a throwaway home, with a fixed test bearer and the keyring library's
`fail` backend, so it starts no server, opens no socket and can never read a real credential (any
keyring read during the build fails it loudly). The routers come from the host's own factories, as
`qmx_host.host.serve` mounts them; their live objects (engine, harness, backups, market door) are
stand-ins, because a schema reads only routes and types. `serve` is read with `ast` on every run,
and a router factory it calls that this script does not mount (or one it mounts that `serve` no
longer calls) fails the run, so the mirror cannot fall behind silently.

`contracts/apps.json` holds each first-party app's id, version, kind and operations, read from
`qmx-agents/apps/*/app.toml`. An app operation is called through
`POST /api/apps/{app_id}/tools/{tool}`.

The host's packages live in the `qmx-agents` workspace. Run from the root environment, the script
builds the schema in a child process of that workspace (`uv run --project qmx-agents --no-sync`).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import tomllib

REPO = Path(__file__).resolve().parents[1]
CONTRACTS = REPO / "contracts"
OPENAPI_FILE = "host-openapi.json"
APPS_FILE = "apps.json"
APPS_DIR = REPO / "qmx-agents" / "apps"
HOST_SOURCE = REPO / "qmx-agents" / "packages" / "qmx-host" / "src" / "qmx_host" / "host.py"
TEST_BEARER = "contract-dump-test-bearer"
"""A fixed stand-in for the host's bearer, never a real one."""
FAIL_KEYRING = "keyring.backends.fail.Keyring"
BUILD_TIMEOUT_S = 600
# Every router factory `serve` calls, and whether the dump mounts it. Two are left out on purpose:
# `closed_market_router` replaces `market_router` only when the market door did not open (a
# catch-all 503 over /api/data/*), and `library_service` mounts the Library hub on role `server`
# only, never on This PC. `adopt_router` hands the harness's model relay its router, which is no
# HTTP router at all.
SERVE_ROUTERS: dict[str, bool] = {
    "chat_routes": True,
    "answering_router": True,
    "drain_router": True,
    "host_router": True,
    "templates_router": True,
    "backups_router": True,
    "maintenance_router": True,
    "publish_collection_router": True,
    "dialog_routers": True,
    "market_router": True,
    "closed_market_router": False,
    "promote_router": True,
    "library_service": False,
    "adopt_router": False,
}
HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")


# ---- the files ------------------------------------------------------------------------------


def render(document: Mapping[str, object]) -> str:
    """Sorted keys, one-space indent, a final newline: the same bytes on every machine."""
    return json.dumps(document, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def apps_contract(apps_dir: Path = APPS_DIR) -> dict[str, object]:
    """`{app_id: {version, kind, operations: [{name, approval, reversibility, state,
    description}]}}` from every `app.toml`, operations sorted by name."""
    found: dict[str, object] = {}
    for manifest in sorted(apps_dir.glob("*/app.toml")):
        data = tomllib.loads(manifest.read_text("utf-8"))
        table = cast("dict[str, dict[str, object]]", data.get("operations") or {})
        operations = [
            {
                "name": name,
                "approval": str(op.get("approval", "")),
                "reversibility": str(op.get("reversibility", "")),
                "state": str(op.get("state", "")),
                "description": str(op.get("description", "")),
            }
            for name, op in sorted(table.items())
        ]
        found[str(data["id"])] = {
            "version": str(data.get("version", "")),
            "kind": str(data.get("kind", "")),
            "operations": operations,
        }
    return found


# ---- the host's schema ------------------------------------------------------------------------


def serve_router_calls(source: str) -> set[str]:
    """The router factories `serve` calls: every called name ending `_router`, `_routers` or
    `_routes`, and `library_service`."""
    tree = ast.parse(source)
    serve = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "serve"),
        None,
    )
    if serve is None:
        raise SystemExit(f"FAIL no `async def serve` in {HOST_SOURCE.relative_to(REPO)}")
    names: set[str] = set()
    for node in ast.walk(serve):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name.endswith(("_router", "_routers", "_routes")) or name == "library_service":
                names.add(name)
    return names


def mirror_gaps(source: str) -> list[str]:
    """Where this script's list of routers and `serve`'s differ, one line each."""
    called = serve_router_calls(source)
    gaps = [
        f"serve mounts {name}(), which contract_dump.py does not know"
        for name in sorted(called - set(SERVE_ROUTERS))
    ]
    gaps += [
        f"contract_dump.py mounts {name}(), which serve no longer calls"
        for name in sorted(set(SERVE_ROUTERS) - called)
    ]
    return gaps


def build_openapi() -> dict[str, object]:
    """The host app's OpenAPI document, built in this process. Needs the `qmx-agents` packages."""
    os.environ["PYTHON_KEYRING_BACKEND"] = FAIL_KEYRING
    keyring: Any = importlib.import_module("keyring")
    fail: Any = importlib.import_module("keyring.backends.fail")
    keyring.set_keyring(fail.Keyring())
    mock: Any = importlib.import_module("unittest.mock")
    stand_in = mock.MagicMock
    with tempfile.TemporaryDirectory(prefix="qmx-contract-") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        os.environ["QMX_HOME"] = str(home)
        host: Any = importlib.import_module("qmx_host.host")
        control = host.control_service(host.QmxHome(home))
        engine, backups, connect = stand_in(), stand_in(), stand_in()
        harness = stand_in()
        harness.home, harness.control = home, control
        answering: list[Any] = [
            *host.answering_router(home, engine),
            host.drain_router(engine.svc.ctx.engine),
            host.host_router(
                host.Answering(
                    stand_in(),
                    pass_keys=list,
                    heartbeats=dict,
                    store_root=lambda: None,
                    answers=host.Answers(home / host.ANSWERS),
                    door=lambda: None,
                )
            ),
            host.templates_router(engine),
            host.backups_router(backups),
            host.maintenance_router(backups, host.triggers_of(control), None),
            host.publish_collection_router(control),
            *host.dialog_routers(connect, control),
            host.market_router(stand_in()),
            host.promote_router(stand_in()),
        ]
        harness_api = host.chat_routes(harness, scrubbed=(), keep=())
        app = host.compose(control, engine, harness_api, TEST_BEARER, "", answering, None, ("", ()))
        document = cast("dict[str, object]", app.openapi())
        control.close()
    return json.loads(render(document))


def agents_importable() -> bool:
    try:
        importlib.import_module("qmx_host")
    except ModuleNotFoundError:
        return False
    return True


def host_openapi() -> dict[str, object]:
    """Built here when the `qmx-agents` packages import, else in a child of that workspace."""
    gaps = mirror_gaps(HOST_SOURCE.read_text("utf-8"))
    if gaps:
        raise SystemExit("FAIL the host's routers changed:\n" + "\n".join(f"  {g}" for g in gaps))
    if agents_importable():
        return build_openapi()
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("FAIL uv is not on PATH, and this environment has no qmx-agents packages")
    argv = [uv, "run", "--project", "qmx-agents", "--frozen", "--no-sync", "python"]
    done = subprocess.run(
        [*argv, str(Path(__file__).resolve()), "--print-openapi"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=BUILD_TIMEOUT_S,
        env={**os.environ, "PYTHON_KEYRING_BACKEND": FAIL_KEYRING, "PYTHONUTF8": "1"},
        check=False,
    )
    if done.returncode != 0:
        raise SystemExit(f"FAIL building the host's schema:\n{done.stderr[-4000:]}")
    return cast("dict[str, object]", json.loads(done.stdout))


# ---- what changed -----------------------------------------------------------------------------


def digest(value: object) -> str:
    return hashlib.sha256(render({"v": value}).encode("utf-8")).hexdigest()[:12]


def operations(document: Mapping[str, object]) -> dict[str, tuple[str, str]]:
    """`METHOD /path` -> (operation id, hash of the operation's whole entry)."""
    found: dict[str, tuple[str, str]] = {}
    paths = cast("dict[str, dict[str, object]]", document.get("paths") or {})
    for path, item in paths.items():
        for method, raw in item.items():
            if method not in HTTP_METHODS:
                continue
            op = cast("dict[str, object]", raw)
            found[f"{method.upper()} {path}"] = (str(op.get("operationId", "")), digest(op))
    return found


def openapi_changes(old: Mapping[str, object], new: Mapping[str, object]) -> list[str]:
    """Operations added, removed or changed, then schemas, then anything else."""
    before, after = operations(old), operations(new)
    lines = [f"added   {k} ({after[k][0]})" for k in sorted(set(after) - set(before))]
    lines += [f"removed {k} ({before[k][0]})" for k in sorted(set(before) - set(after))]
    lines += [
        f"changed {k} ({after[k][0]})"
        for k in sorted(set(before) & set(after))
        if before[k] != after[k]
    ]
    old_s = cast("dict[str, object]", old.get("components") or {})
    new_s = cast("dict[str, object]", new.get("components") or {})
    old_schemas = cast("dict[str, object]", old_s.get("schemas") or {})
    new_schemas = cast("dict[str, object]", new_s.get("schemas") or {})
    for name in sorted(set(old_schemas) | set(new_schemas)):
        if name not in old_schemas:
            lines.append(f"added   schema {name}")
        elif name not in new_schemas:
            lines.append(f"removed schema {name}")
        elif digest(old_schemas[name]) != digest(new_schemas[name]):
            lines.append(f"changed schema {name}")
    rest = {k for k in set(old) | set(new) if k not in ("paths", "components")}
    lines += [f"changed {k}" for k in sorted(rest) if digest(old.get(k)) != digest(new.get(k))]
    return lines


def apps_changes(old: Mapping[str, object], new: Mapping[str, object]) -> list[str]:
    def ops(doc: Mapping[str, object]) -> dict[str, str]:
        found: dict[str, str] = {}
        for app_id, raw in doc.items():
            app = cast("dict[str, object]", raw)
            found[f"app {app_id}"] = digest({k: v for k, v in app.items() if k != "operations"})
            for op in cast("list[dict[str, object]]", app.get("operations") or []):
                found[f"operation {app_id}.{op['name']}"] = digest(op)
        return found

    before, after = ops(old), ops(new)
    lines = [f"added   {k}" for k in sorted(set(after) - set(before))]
    lines += [f"removed {k}" for k in sorted(set(before) - set(after))]
    lines += [f"changed {k}" for k in sorted(set(before) & set(after)) if before[k] != after[k]]
    return lines


def stale(contracts: Path, wanted: Mapping[str, Mapping[str, object]]) -> list[str]:
    """For each contract file that differs from what the code gives, a header and its changes."""
    report: list[str] = []
    for name, document in wanted.items():
        path = contracts / name
        if not path.is_file():
            report.append(f"contracts/{name}: missing")
            continue
        text = path.read_text("utf-8")
        if text == render(document):
            continue
        try:
            old = cast("dict[str, object]", json.loads(text))
        except json.JSONDecodeError:
            report.append(f"contracts/{name}: not JSON")
            continue
        changes = (openapi_changes if name == OPENAPI_FILE else apps_changes)(old, document)
        report.append(f"contracts/{name}: stale")
        report += [f"  {line}" for line in changes or ["formatting only"]]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check contracts/ from the code.")
    parser.add_argument("--check", action="store_true", help="exit 1 when a file is stale")
    parser.add_argument("--print-openapi", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.print_openapi:
        sys.stdout.write(render(build_openapi()))
        return 0
    wanted = {OPENAPI_FILE: host_openapi(), APPS_FILE: apps_contract()}
    if args.check:
        report = stale(CONTRACTS, wanted)
        for line in report:
            print(line)
        if report:
            print("FAIL the contract files are stale: run `python tools/contract_dump.py`")
            return 1
        print(f"contracts are current ({len(operations(wanted[OPENAPI_FILE]))} host operations)")
        return 0
    CONTRACTS.mkdir(exist_ok=True)
    for name, document in wanted.items():
        (CONTRACTS / name).write_text(render(document), "utf-8", newline="\n")
        print(f"wrote contracts/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
