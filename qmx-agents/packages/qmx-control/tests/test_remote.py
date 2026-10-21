from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from fastmcp import Client
from qmx_ledger.journal import fingerprint
from qmx_remote.models import Document, Manifest, RunBundle, Status, Target
from qmx_remote.runs import RemoteRuns
from qmx_remote.store import ResultsStore

from qmx_control.server import create_app, create_mcp
from qmx_control.service import ControlService


class FakeProvider:
    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        return {"run_id": run_id}

    def start(self, handle: Document, secrets: dict[str, str]) -> Document:
        return handle

    def status(self, handle: Document) -> Status:
        return "running"

    def logs(self, handle: Document) -> str:
        return "recorded"

    def stop(self, handle: Document) -> None:
        pass

    def teardown(self, handle: Document) -> None:
        pass


def test_remote_rest_and_mcp_use_one_owner_and_register_verified_artifacts(tmp_path: Path) -> None:
    service = ControlService(tmp_path / "home")
    service.settings_put(
        "remote",
        {
            "bucket": str(tmp_path / "bucket"),
            "targets": {"vps": {"host": "vps", "image": "worker"}},
        },
    )
    runtime = service.remote_runtime()
    provider = FakeProvider()

    def providers(target: Target, bucket: str) -> FakeProvider:
        return provider

    runtime.providers = providers
    definition: Document = {}
    bundle = RunBundle(
        kind="job",
        definition=definition,
        definition_hash=fingerprint({"definition": definition, "files": {}}),
        command=["python", "-c", "print('ok')"],
    )
    token = str(uuid4())
    headers = {"Authorization": "Bearer " + token}
    with TestClient(create_app(service, token)) as rest:
        response = rest.post(
            "/api/runs/remote", headers=headers, json=bundle.model_dump(mode="json")
        )
        assert response.status_code == 200
        run_id = response.json()["run_id"]
        assert response.json()["kind"] == "job"
        assert response.json()["node"] == "vps"
        assert service.jobs_list()[0]["run_id"] == run_id
        status = rest.get(f"/api/runs/{run_id}/status", headers=headers)
        assert status.status_code == 200

        async def compare() -> None:
            async with Client(create_mcp(service)) as mcp:
                result = await mcp.call_tool("workflows_remote_status", {"run_id": run_id})
                assert result.data == status.json()
                names = {tool.name for tool in await mcp.list_tools()}
                assert {
                    "workflows_jobs_run",
                    "workflows_jobs_status",
                    "workflows_jobs_logs",
                    "workflows_jobs_fetch",
                    "workflows_remote_resume",
                    "workflows_remote_stop",
                } <= names

        asyncio.run(compare())
        root = tmp_path / "worker"
        (root / "outputs").mkdir(parents=True)
        (root / "outputs/result.json").write_text('{"result":42}')
        manifest = Manifest.model_validate(runtime.status(run_id))
        manifest.status = "completed"
        ResultsStore(runtime.settings.bucket).publish(root, manifest)
        fetched = rest.post(f"/api/runs/{run_id}/fetch", headers=headers)
        assert fetched.status_code == 200
        ids = fetched.json()["library_items"]
        assert len(ids) == 1
        assert service.library_get(ids[0])["source"] == "remote:" + run_id
        assert service.runs_get(run_id)["status"] == "completed"
        assert service.jobs_list()[0]["status"] == "completed"
        assert rest.post(f"/api/runs/{run_id}/stop", headers=headers).status_code == 200
        assert rest.get("/api/runs/missing/status", headers=headers).status_code == 409

    restarted = RemoteRuns(
        runtime.home, runtime.settings, providers=lambda target, bucket: provider
    )
    assert restarted.status(run_id)["status"] == "stopped"
