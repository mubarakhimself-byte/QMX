from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from qmx_control import ControlService, create_app
from qmx_control.service import WorkflowEngine

BEARER = {"Authorization": "Bearer door-check"}


class Recorder:
    """Answers every workflow door with its own name and the arguments it was given."""

    def __getattr__(self, name: str) -> Any:
        def door(*args: object) -> dict[str, object]:
            return {"door": name, "args": list(args)}

        return door


def test_the_workflow_doors_answer_501_until_an_engine_is_attached(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    with TestClient(create_app(service, "door-check")) as rest:
        before = rest.put("/api/workflows/wf-1", json={"semver": "1.0.0"}, headers=BEARER)
        service.attach_workflow_engine(cast(WorkflowEngine, Recorder()))
        published = rest.put("/api/workflows/wf-1", json={"semver": "1.0.0"}, headers=BEARER)
        validated = rest.post("/api/workflows/validate", json={"nodes": []}, headers=BEARER)
        tested = rest.post(
            "/api/workflows/wf-1/test", params={"fake": True}, json=["a"], headers=BEARER
        )
        service.attach_workflow_engine(None)
        after = rest.get("/api/workflow-runs", headers=BEARER)

    assert (before.status_code, before.json()["error"]["code"]) == (501, "not_implemented")
    assert published.json() == {"door": "workflows_put", "args": ["wf-1", {"semver": "1.0.0"}]}
    assert validated.json() == {"door": "workflows_validate", "args": [{"nodes": []}]}
    assert tested.json() == {"door": "workflow_tests_run", "args": ["wf-1", ["a"], True]}
    assert (after.status_code, after.json()["error"]["code"]) == (501, "not_implemented")


def test_a_direct_call_reaches_the_attached_engine(tmp_path: Path) -> None:
    service = ControlService(tmp_path)
    service.attach_workflow_engine(cast(WorkflowEngine, Recorder()))

    assert service.workflow_runs_list() == {"door": "workflow_runs_list", "args": [None]}
    assert service.workflow_versions_archive("wf-1", 2) == {
        "door": "workflow_versions_archive",
        "args": ["wf-1", 2],
    }
