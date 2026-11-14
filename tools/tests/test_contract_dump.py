"""contracts/ against the code: the apps file from each app.toml, what a stale file reports, the
guard that keeps the dump's router list equal to the host's, and the committed files are current."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import contract_dump

REPO = Path(__file__).resolve().parents[2]

APP = """id = "demo"
name = "Demo"
version = "1.2.3"
kind = "headless"

[operations.status]
description = "Its state."
approval = "read"
state = "none"

[operations.act]
description = "Do it."
approval = "manage"
reversibility = "compensable"
state = "instance"
"""


def test_apps_json_lists_each_app_and_its_operations_by_name(tmp_path: Path) -> None:
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "app.toml").write_text(APP, "utf-8")
    assert contract_dump.apps_contract(tmp_path) == {
        "demo": {
            "version": "1.2.3",
            "kind": "headless",
            "operations": [
                {
                    "name": "act",
                    "approval": "manage",
                    "reversibility": "compensable",
                    "state": "instance",
                    "description": "Do it.",
                },
                {
                    "name": "status",
                    "approval": "read",
                    "reversibility": "",
                    "state": "none",
                    "description": "Its state.",
                },
            ],
        }
    }


def _spec(*ops: tuple[str, str, str]) -> dict[str, object]:
    paths: dict[str, dict[str, object]] = {}
    for method, path, op_id in ops:
        paths.setdefault(path, {})[method] = {"operationId": op_id, "responses": {}}
    return {"openapi": "3.1.0", "paths": paths, "components": {"schemas": {}}}


def test_a_stale_schema_names_each_operation_added_removed_or_changed(tmp_path: Path) -> None:
    old = _spec(("get", "/api/a", "a"), ("post", "/api/b", "b"), ("get", "/api/c", "c"))
    (tmp_path / "host-openapi.json").write_text(contract_dump.render(old), "utf-8")
    (tmp_path / "apps.json").write_text(contract_dump.render({}), "utf-8")
    new = _spec(("get", "/api/a", "a"), ("post", "/api/b", "b2"), ("put", "/api/d", "d"))
    report = contract_dump.stale(tmp_path, {"host-openapi.json": new, "apps.json": {}})
    assert report == [
        "contracts/host-openapi.json: stale",
        "  added   PUT /api/d (d)",
        "  removed GET /api/c (c)",
        "  changed POST /api/b (b2)",
    ]


def test_a_current_file_reports_nothing_and_a_missing_one_is_named(tmp_path: Path) -> None:
    spec = _spec(("get", "/api/a", "a"))
    (tmp_path / "host-openapi.json").write_text(contract_dump.render(spec), "utf-8")
    report = contract_dump.stale(tmp_path, {"host-openapi.json": spec, "apps.json": {}})
    assert report == ["contracts/apps.json: missing"]


def test_an_app_operation_added_or_changed_is_named(tmp_path: Path) -> None:
    op = {"name": "status", "approval": "read", "reversibility": "", "state": "", "description": ""}
    old: dict[str, object] = {"demo": {"version": "1", "kind": "headless", "operations": [op]}}
    new: dict[str, object] = {
        "demo": {
            "version": "1",
            "kind": "headless",
            "operations": [{**op, "approval": "manage"}, {**op, "name": "kill"}],
        }
    }
    (tmp_path / "apps.json").write_text(contract_dump.render(old), "utf-8")
    assert contract_dump.stale(tmp_path, {"apps.json": new}) == [
        "contracts/apps.json: stale",
        "  added   operation demo.kill",
        "  changed operation demo.status",
    ]


SERVE = """
async def serve(home, sock):
    adopt_router(relay)
    harness_api = chat_routes(harness, scrubbed=s, keep=k)
    answering = [*answering_router(home, engine), drain_router(core)]
    answering.append(host_router(a))
    answering.append(templates_router(engine))
    answering.append(backups_router(backups))
    answering.append(maintenance_router(backups, t, r))
    answering.append(publish_collection_router(control))
    answering.extend(dialog_routers(connect, control))
    answering.append(market_router(door) if open else closed_market_router(door))
    answering.append(promote_router(p))
    {new}
    app = compose(control, engine, harness_api, bearer, origin, answering, passes,
                  library_service(home, store, serving, bearer))
"""


def test_the_dump_mounts_exactly_the_routers_serve_mounts() -> None:
    assert contract_dump.mirror_gaps(SERVE.format(new="")) == []
    assert contract_dump.mirror_gaps(SERVE.format(new="answering.append(lab_router(x))")) == [
        "serve mounts lab_router(), which contract_dump.py does not know"
    ]
    dropped = SERVE.format(new="").replace("    answering.append(promote_router(p))\n", "")
    assert contract_dump.mirror_gaps(dropped) == [
        "contract_dump.py mounts promote_router(), which serve no longer calls"
    ]


def test_the_hosts_own_serve_matches_the_dump() -> None:
    assert contract_dump.mirror_gaps(contract_dump.HOST_SOURCE.read_text("utf-8")) == []


def test_the_committed_contracts_are_current() -> None:
    """The check CI's lint job runs, run for real in the agents workspace (about 20 s)."""
    uv = shutil.which("uv")
    assert uv is not None
    done = subprocess.run(
        [
            *(uv, "run", "--project", "qmx-agents", "--frozen", "--no-sync", "python"),
            str(REPO / "tools" / "contract_dump.py"),
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr[-3000:]
    assert done.stdout.startswith("contracts are current (")


def test_the_files_are_sorted_json_with_a_final_newline() -> None:
    for name in ("host-openapi.json", "apps.json"):
        text = (REPO / "contracts" / name).read_text("utf-8")
        assert text == contract_dump.render(json.loads(text)), name
