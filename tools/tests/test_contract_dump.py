"""contracts/ against the code: the apps file from each app.toml, what a stale file reports, the
guard that keeps the dump's router list equal to the host's, and the committed files are current."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import contract_dump
import pytest
import qci

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
    for name in ("host-openapi.json", "first-start-openapi.json", "apps.json"):
        text = (REPO / "contracts" / name).read_text("utf-8")
        assert text == contract_dump.render(json.loads(text)), name


def test_a_router_serve_calls_is_found_by_its_return_annotation_or_a_direct_route() -> None:
    probe = SERVE.format(new="answering.append(probe_api())") + (
        "\n\ndef probe_api() -> APIRouter:\n    return APIRouter()\n"
    )
    assert contract_dump.mirror_gaps(probe) == [
        "serve mounts probe_api(), which contract_dump.py does not know"
    ]
    listed = SERVE.format(new="extra = probe_apis()") + (
        "\n\ndef probe_apis() -> list[APIRouter]:\n    return []\n"
    )
    assert contract_dump.mirror_gaps(listed) == [
        "serve mounts probe_apis(), which contract_dump.py does not know"
    ]
    for call in ("add_api_route", "api_route", "add_route", "include_router", "mount"):
        direct = SERVE.format(new=f'app.{call}("/api/x", handler)')
        assert contract_dump.mirror_gaps(direct) == [
            f"serve adds a route itself: {call}() at line 14"
        ], call
    other = SERVE.format(new="sock = make_socket()") + (
        "\n\ndef make_socket() -> Socket:\n    return Socket()\n"
    )
    assert contract_dump.mirror_gaps(other) == []


def test_an_imported_router_factory_is_resolved_through_its_package() -> None:
    resolve = contract_dump.resolver(contract_dump.HOST_SOURCE.read_text("utf-8"))
    assert resolve("chat_routes") == "list[APIRouter]"
    assert resolve("engine_router") == "APIRouter"
    assert resolve("compose") == "FastAPI"
    assert resolve("no_such_name") is None


def _op(op_id: str, **extra: object) -> dict[str, object]:
    return {"operationId": op_id, "responses": {}, **extra}


A_PATH: dict[str, object] = {"get": _op("a"), "parameters": [{"name": "p"}]}
PATHS: dict[str, object] = {"/a": A_PATH, "/b": {"post": _op("b")}}
BASE: dict[str, object] = {
    "openapi": "3.1.0",
    "info": {"title": "QMX control", "version": "1"},
    "paths": PATHS,
    "components": {"schemas": {"S": {"type": "object"}}},
}


def _with(**changes: object) -> dict[str, object]:
    return json.loads(json.dumps({**BASE, **changes}))


@pytest.mark.parametrize(
    ("new", "expected"),
    [
        (BASE, []),
        (_with(paths={"/a": A_PATH}), ["removed POST /b (b)"]),
        (_with(paths={**PATHS, "/c": {"put": _op("c")}}), ["added   PUT /c (c)"]),
        (
            _with(paths={**PATHS, "/b": {"post": _op("b", responses={"200": {}})}}),
            ["changed POST /b (b)"],
        ),
        (_with(paths={**PATHS, "/a": {"get": _op("a"), "parameters": []}}), []),
        (_with(components={"schemas": {"S": {"type": "string"}}}), ["changed schema S"]),
        (
            _with(components={"schemas": {"S": {"type": "object"}, "T": {}}}),
            ["added   schema T"],
        ),
        (_with(components={"schemas": {}}), ["removed schema S"]),
        (_with(info={"title": "QMX control", "version": "2"}), ["changed info"]),
    ],
    ids=["same", "removed", "added", "changed", "path-params", "schema", "new-schema",
         "gone-schema", "info"],
)
def test_each_kind_of_schema_change_is_named(
    new: dict[str, object], expected: list[str]
) -> None:
    assert contract_dump.openapi_changes(BASE, new) == expected


def test_operations_are_only_the_http_methods_of_a_path() -> None:
    assert sorted(contract_dump.operations(BASE)) == ["GET /a", "POST /b"]


APP_OP = {"name": "x", "approval": "read", "reversibility": "", "state": "", "description": ""}
DEMO: dict[str, object] = {"version": "1", "kind": "headless", "operations": [APP_OP]}
APPS: dict[str, object] = {"demo": DEMO}


@pytest.mark.parametrize(
    ("new", "expected"),
    [
        ({"demo": {**DEMO, "version": "2"}}, ["changed app demo"]),
        ({"demo": {**DEMO, "operations": []}}, ["removed operation demo.x"]),
        ({}, ["removed app demo", "removed operation demo.x"]),
    ],
    ids=["version", "operation-removed", "app-removed"],
)
def test_each_kind_of_app_change_is_named(new: dict[str, object], expected: list[str]) -> None:
    assert contract_dump.apps_changes(APPS, new) == expected


def test_a_file_that_is_not_json_or_differs_only_in_formatting_is_stale(tmp_path: Path) -> None:
    (tmp_path / "host-openapi.json").write_text("{not json", "utf-8")
    (tmp_path / "apps.json").write_text(json.dumps(APPS), "utf-8")
    assert contract_dump.stale(tmp_path, {"host-openapi.json": BASE, "apps.json": APPS}) == [
        "contracts/host-openapi.json: not JSON",
        "contracts/apps.json: stale",
        "  formatting only",
    ]


def test_render_sorts_keys_and_ends_with_a_newline() -> None:
    assert contract_dump.render({"b": 1, "a": {"d": 2, "c": 3}}) == (
        '{\n "a": {\n  "c": 3,\n  "d": 2\n },\n "b": 1\n}\n'
    )


# ---- the lint job's contract step ----------------------------------------------------------------


def test_the_contract_check_runs_when_a_slice_touches_the_host_or_its_imports() -> None:
    for path in (
        "qmx-agents/packages/qmx-control/src/qmx_control/service.py",
        "contracts/apps.json",
        "packages/qmf-core/src/qmf/core/exact.py",
        "qmn/src/qmn/order/door.py",
        "tools/contract_dump.py",
    ):
        assert qci.contract_due(qci.Level.SLICE, [path]), path
    assert not qci.contract_due(qci.Level.SLICE, ["qml/src/qml/x.py", "docs/a.md"])
    assert qci.contract_due(qci.Level.DEEP, [])
    assert not qci.contract_due(qci.Level.BASELINE, ["contracts/apps.json"])


STALE_REPORT = (
    "contracts/host-openapi.json: stale\n"
    "  added   GET /api/ops/probe (ops_probe)\n"
    "contracts/apps.json: missing\n"
    "FAIL the contract files are stale: run `python tools/contract_dump.py`\n"
)


@pytest.mark.parametrize(
    ("rc", "expected"),
    [
        (
            1,
            [
                "contracts:0: [contract] stale: added   GET /api/ops/probe (ops_probe)",
                "contracts:0: [contract] stale: contracts/apps.json: missing",
            ],
        ),
        (2, ["contracts:0: [contract] contract check failed (rc=2)"]),
        (0, []),
    ],
    ids=["stale", "crashed", "current"],
)
def test_the_contract_step_names_each_stale_operation_or_says_it_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rc: int, expected: list[str]
) -> None:
    def fake_run(argv: list[str], cwd: Path, **kwargs: object) -> int:
        out = kwargs["stdout_to"]
        assert isinstance(out, Path)
        out.write_text(STALE_REPORT, "utf-8")
        assert argv[-2:] == ["tools/contract_dump.py", "--check"]
        return rc

    monkeypatch.setattr(qci, "OUT", tmp_path)
    monkeypatch.setattr(qci, "run", fake_run)
    monkeypatch.setattr(qci, "uv", lambda: "uv")
    assert [f.text() for f in qci.contract_findings()] == expected
