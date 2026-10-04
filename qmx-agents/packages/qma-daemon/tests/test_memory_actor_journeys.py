"""Fresh jobs use host role/workflow pins, even with the same behavioral actor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_actor_workflow import accepted, final, save_catalog, setup, wait_status
from test_request_runtime_daemon import compose, connection, mint


@pytest.mark.parametrize("change", ["role_version", "workflow_version"])
def test_new_host_role_or_workflow_pin_withholds_prior_actor_memory_after_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    scripted = setup(
        tmp_path,
        monkeypatch,
        [
            final("prior private analysis"),
            final("prior private review"),
            final("new analysis"),
            final("new review"),
        ],
    )
    process = compose(tmp_path, boot="memory-pins-one")
    try:
        mint(process)
        request_id = accepted(process, connection(process))
        wait_status(process, connection(process), request_id, "completed")
    finally:
        process.close()
    body = json.loads((tmp_path / "actor-workflows.json").read_text(encoding="utf-8"))
    if change == "role_version":
        body["roles"][0]["version"] = "2"
        body["workflows"][0]["steps"][1]["role"] = "analyst:2"
    body["workflows"][0]["version"] = "2"
    body["routes"][0]["workflow"] = "assessment:2"
    save_catalog(tmp_path, body)
    process = compose(tmp_path, boot="memory-pins-two")
    try:
        request_id = accepted(process, connection(process), "new-pins")
        result = wait_status(process, connection(process), request_id, "completed")
        assert json.loads(result["content"])["actor_id"] == "quant:research"
        assert len(scripted.requests) == 4
        for request in scripted.requests[2:]:
            invocation = json.loads(json.loads(request.prompt)["user_request"])
            assert invocation["actor_memory"] == ""
        assert scripted.requests[0].graph_thread_id != scripted.requests[2].graph_thread_id
    finally:
        process.close()
