from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal
from unittest.mock import Mock

import psutil
import pytest
from qmx_agents.guards.journal import fingerprint
from qmx_agents.workflows import WorkflowSpec

from qmx_remote.code import publish
from qmx_remote.models import (
    Document,
    Manifest,
    RemoteError,
    RemoteSettings,
    RunBundle,
    Status,
    Target,
)
from qmx_remote.providers import AmpProvider, E2BProvider, ModalProvider, SSHProvider
from qmx_remote.runs import RemoteRuns
from qmx_remote.store import ResultsStore, snapshot_checkpoint
from qmx_remote.worker import Worker, execute_amp, execute_job, execute_workflow


def echo(value: str) -> str:
    return value


def fail_once(marker: str) -> str:
    path = Path(marker)
    if not path.exists():
        path.touch()
        raise ValueError("interrupted")
    return "resumed"


def bundle(
    kind: Literal["workflow", "agent", "app", "job", "amp"] = "job", **kwargs: Any
) -> RunBundle:
    definition = kwargs.pop("definition", {})
    sources = kwargs.pop("files", {})
    return RunBundle(
        kind=kind,
        definition=definition,
        definition_hash=fingerprint({"definition": definition, "files": sources}),
        files=sources,
        command=kwargs.pop("command", [sys.executable, "-c", "print('hello')"]),
        **kwargs,
    )


def settings(root: Path) -> RemoteSettings:
    return RemoteSettings(
        bucket=str(root / "bucket"),
        targets={
            "vps": Target(host="vps", image="qmx-worker:test"),
            "gpu": Target(host="gpu-node", gpu=2, image="qmx-worker:test"),
        },
    )


class FakeProvider:
    def __init__(self) -> None:
        self.phase: Status = "running"
        self.calls: list[str] = []
        self.credentials: dict[str, str] = {}

    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        self.calls.append("provision")
        return {"run_id": run_id}

    def start(self, handle: Document, secrets: dict[str, str]) -> Document:
        self.calls.append("start")
        self.credentials = dict(secrets)
        self.phase = "running"
        return handle

    def status(self, handle: Document) -> Status:
        self.calls.append("status")
        return self.phase

    def logs(self, handle: Document) -> str:
        return "fake logs"

    def stop(self, handle: Document) -> None:
        self.calls.append("stop")
        self.phase = "stopped"

    def teardown(self, handle: Document) -> None:
        self.calls.append("teardown")
        self.credentials.clear()


def test_fake_lifecycle_persists_handles_and_fetches_verified_outputs(tmp_path: Path) -> None:
    provider = FakeProvider()
    config = settings(tmp_path)
    runs = RemoteRuns(
        tmp_path / "home",
        config,
        providers=lambda target, bucket: provider,
        secret_getter=lambda service, user: "vault-value",
    )
    started = runs.start(bundle(credentials_scope={"TOKEN": "qmx/test"}))
    run_id = str(started["run_id"])
    assert provider.credentials == {"TOKEN": "vault-value"}
    restarted = RemoteRuns(runs.home, config, providers=lambda target, bucket: provider)
    assert restarted.status(run_id)["status"] == "running"
    root = tmp_path / "worker"
    (root / "outputs").mkdir(parents=True)
    (root / "outputs/result.json").write_text('{"ok":true}')
    manifest = Manifest.model_validate(started)
    manifest.status = "completed"
    ResultsStore(config.bucket).publish(root, manifest)
    fetched = restarted.fetch(run_id)
    assert (Path(str(fetched["path"])) / "outputs/result.json").read_text() == '{"ok":true}'
    assert "vault-value" not in (runs.home / "remote" / run_id / "state.json").read_text()
    assert "remote_fetch" in (runs.home / "journals" / f"remote-{run_id}.jsonl").read_text()
    restarted.stop(run_id)
    assert provider.calls[-2:] == ["stop", "teardown"]
    assert not provider.credentials


def test_missing_credential_fails_before_allocating_and_remains_readable(tmp_path: Path) -> None:
    provider = FakeProvider()
    runs = RemoteRuns(
        tmp_path / "home",
        settings(tmp_path),
        providers=lambda target, bucket: provider,
        secret_getter=lambda service, user: None,
    )
    with pytest.raises(RemoteError, match="scoped credential is missing"):
        runs.start(bundle(credentials_scope={"TOKEN": "qmx/missing"}))
    run_id = next((runs.home / "remote").iterdir()).name
    assert runs.status(run_id)["status"] == "failed"
    assert provider.calls == ["provision"]
    assert runs.stop(run_id)["status"] == "stopped"
    assert provider.calls == ["provision"]


@pytest.mark.parametrize("attack", ["blob", "manifest", "identity", "traversal"])
def test_corruption_is_detected_before_fetch_writes_outputs(tmp_path: Path, attack: str) -> None:
    store = ResultsStore(str(tmp_path / "bucket"))
    root = tmp_path / "worker"
    (root / "outputs").mkdir(parents=True)
    (root / "outputs/result").write_bytes(b"good")
    manifest = Manifest(run_id="run1", bundle=bundle(), target="vps")
    store.publish(root, manifest)
    remote = Path(store.location("run1"))
    if attack == "blob":
        (remote / "artifacts" / manifest.artifacts[0].sha256).write_bytes(b"bad")
    else:
        data = json.loads((remote / "manifest.json").read_text())
        if attack == "manifest":
            data["status"] = "completed"
        elif attack == "identity":
            data["run_id"] = "other"
        else:
            data["artifacts"][0]["path"] = "../../escaped"
        (remote / "manifest.json").write_text(json.dumps(data))
    with pytest.raises(RemoteError):
        store.fetch("run1", tmp_path / "fetched")
    assert not (tmp_path / "fetched/outputs/result").exists()


def test_killed_upload_retains_the_last_complete_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ResultsStore(str(tmp_path / "bucket"))
    root = tmp_path / "worker"
    (root / "logs").mkdir(parents=True)
    log = root / "logs/worker.log"
    log.write_text("first flush\n")
    manifest = Manifest(run_id="killed", bundle=bundle(), target="vps", status="running")
    store.publish(root, manifest)
    copy = ResultsStore.copy

    def interrupted(source: str | Path, target: str | Path, *, include: str = "") -> None:
        if include:
            raise RemoteError("killed before manifest commit")
        copy(source, target, include=include)

    log.write_text("first flush\nsecond flush\n")
    monkeypatch.setattr(store, "copy", interrupted)
    with pytest.raises(RemoteError):
        store.publish(root, manifest)
    recovered = ResultsStore(store.bucket)
    fetched = recovered.fetch("killed", tmp_path / "fetched")
    assert fetched.revision == 1
    assert (tmp_path / "fetched/logs/worker.log").read_text() == "first flush\n"


def test_workflow_resumes_on_another_worker_from_uploaded_sqlite(tmp_path: Path) -> None:
    definition: dict[str, Any] = {
        "name": "remote-flow",
        "entry": "first",
        "nodes": [
            {
                "id": "first",
                "kind": "python",
                "function": "test_remote.echo",
                "args": {"value": "first"},
            },
            {
                "id": "second",
                "kind": "python",
                "function": "test_remote.fail_once",
                "inputs": {"value": {}},
                "args": {"marker": str(tmp_path / "marker")},
            },
        ],
        "edges": [
            {
                "mapping": "one",
                "source": {"node": "first", "port": "result"},
                "target": {"node": "second", "port": "value"},
            }
        ],
    }
    spec = WorkflowSpec.model_validate(definition)
    run_bundle = bundle("workflow", definition=spec.model_dump(mode="json", by_alias=True))
    manifest = Manifest(run_id="resume1", bundle=run_bundle, target="vps")
    store = ResultsStore(str(tmp_path / "bucket"))
    first = Worker(store, tmp_path / "first", manifest)
    result = first.run(lambda w: execute_workflow(w, False))
    assert result.status == "failed"
    assert result.checkpoint is not None
    second = tmp_path / "second"
    downloaded = store.fetch("resume1", second)
    (second / "state.db").write_bytes((second / "checkpoints/latest.db").read_bytes())
    worker = Worker(store, second, downloaded)
    resumed = worker.run(lambda w: execute_workflow(w, True))
    assert resumed.status == "completed"
    output = json.loads((second / "outputs/result.json").read_text())
    assert output["values"]["first"]["result"] == "first"
    assert output["values"]["second"]["result"] == "resumed"


def test_resume_requires_checkpoint_and_selects_gpu_node(tmp_path: Path) -> None:
    provider = FakeProvider()
    config = settings(tmp_path)
    runs = RemoteRuns(tmp_path / "home", config, providers=lambda target, bucket: provider)
    started = runs.start(bundle(resources={"gpu": 1}))
    assert started["target"] == "gpu"
    run_id = str(started["run_id"])
    with pytest.raises(RemoteError, match="Only"):
        runs.resume(run_id)
    runs.stop(run_id)
    with pytest.raises(RemoteError, match="checkpoint"):
        runs.resume(run_id)
    with pytest.raises(RemoteError, match="GPUs"):
        runs.start(bundle(resources={"gpu": 1}), "vps")
    with pytest.raises(RemoteError, match="GPU node"):
        runs.start(bundle(resources={"gpu": 3}))
    database = tmp_path / "checkpoint.db"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE checkpoint (value TEXT)")
    output = tmp_path / "worker"
    snapshot_checkpoint(database, output / "checkpoints/latest.db")
    manifest = Manifest.model_validate(started)
    manifest.status = "failed"
    ResultsStore(config.bucket).publish(output, manifest)
    assert runs.resume(run_id, "gpu")["status"] == "running"
    assert runs.status(run_id)["status"] == "running"
    assert ResultsStore(config.bucket).read(run_id).checkpoint == manifest.checkpoint


def test_job_logs_are_incrementally_shipped_and_credentials_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUN_SECRET", "scoped-secret")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    cache = tmp_path / "cache"
    monkeypatch.setenv("TMPDIR", str(scratch))
    monkeypatch.setenv("UV_CACHE_DIR", str(cache))
    manifest = Manifest(
        run_id="job1",
        bundle=bundle(
            credentials_scope={"RUN_SECRET": "qmx/test"},
            command=[
                sys.executable,
                "-c",
                "import os,tempfile; print(os.environ['RUN_SECRET']); "
                "print(tempfile.gettempdir()); print(os.environ['UV_CACHE_DIR'])",
            ],
        ),
        target="vps",
    )
    worker = Worker(
        ResultsStore(str(tmp_path / "bucket")), tmp_path / "worker", manifest, interval=0.01
    )
    assert worker.run(execute_job).status == "completed"
    recovered = worker.store.fetch("job1", tmp_path / "fetched")
    assert recovered.revision >= 2
    text = (tmp_path / "fetched/logs/worker.log").read_text()
    assert "[redacted]" in text and "scoped-secret" not in text
    assert str(scratch) in text and str(cache) in text


def test_ssh_uses_detached_docker_and_secrets_only_on_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def run(args: list[str], **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout=b"container", stderr=b"")

    monkeypatch.setattr("qmx_remote.providers.shutil.which", Mock(return_value="ssh"))
    monkeypatch.setattr("qmx_remote.providers.subprocess.run", run)
    provider = SSHProvider(settings(tmp_path).targets["gpu"])
    provider.start(provider.provision("run1", bundle(resources={"gpu": 2})), {"TOKEN": "hidden"})
    args, kwargs = calls[-1]
    assert "hidden" not in str(args)
    request = json.loads(kwargs["input"])
    assert "--detach" in request["args"] and "--gpus" in request["args"]
    assert "HOME=/work" in request["args"]
    assert "TMPDIR=/work" in request["args"]
    assert not any("src=/srv/qmx/bucket,dst=" in arg for arg in request["args"])
    assert request["env"] == {"TOKEN": "hidden"}


def test_amp_uses_documented_sdk_and_remote_mcp_settings(tmp_path: Path) -> None:
    calls: list[Any] = []

    class Message:
        def __init__(self, type: str):
            self.type = type
            self.session_id = "T-123"
            self.is_error = False
            self.result = "done"

        def model_dump_json(self) -> str:
            return json.dumps(vars(self))

    async def execute(prompt: str, options: Any) -> AsyncIterator[Message]:
        calls.append((prompt, options))
        yield Message("system")
        yield Message("result")

    def options(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    sdk = SimpleNamespace(AmpOptions=options, execute=execute)
    target = Target(provider="amp", host="vps", image="worker", runner_id="runner")
    run_bundle = bundle("amp", inputs={"prompt": "Research this"})
    worker = Worker(
        ResultsStore(str(tmp_path / "bucket")),
        tmp_path / "worker",
        Manifest(run_id="amp1", bundle=run_bundle, target="amp"),
    )
    result = asyncio.run(execute_amp(worker, target, sdk=sdk))
    assert result["result"] == "done"
    assert calls[0][1]["executor"] == "runner"
    assert "mcp_config" not in calls[0][1]
    assert AmpProvider(target).provision("amp1", run_bundle)["run_id"] == "amp1"
    with pytest.raises(RemoteError):
        AmpProvider(target).provision("amp1", bundle())


@pytest.mark.parametrize("kind", ["modal", "e2b"])
def test_sandbox_adapters_reconnect_and_teardown_with_stub_sdk(
    tmp_path: Path, kind: Literal["modal", "e2b"]
) -> None:
    calls: list[Any] = []
    sandbox = SimpleNamespace(
        object_id="sb-1",
        sandbox_id="sb-1",
        poll=lambda: None,
        terminate=lambda: calls.append("terminated"),
        kill=lambda: calls.append("killed"),
        commands=SimpleNamespace(
            run=Mock(return_value=SimpleNamespace(pid=7)),
            list=lambda: [SimpleNamespace(pid=7)],
            kill=calls.append,
        ),
    )

    def create(*args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs)
        return sandbox

    sdk = SimpleNamespace(
        Client=SimpleNamespace(from_credentials=Mock(return_value="client")),
        Sandbox=SimpleNamespace(
            create=create, from_id=Mock(return_value=sandbox), connect=Mock(return_value=sandbox)
        ),
        App=SimpleNamespace(lookup=Mock(return_value="app")),
        Image=SimpleNamespace(from_registry=Mock(return_value="image")),
        Secret=SimpleNamespace(from_dict=Mock(return_value="secret")),
    )
    target = Target(provider=kind, image="worker", gpu=1 if kind == "modal" else 0, gpu_type="A10")
    provider = (
        ModalProvider(
            target, "vps:/bucket", sdk=sdk, secret_getter=lambda service, username: "fake"
        )
        if kind == "modal"
        else E2BProvider(
            target, "vps:/bucket", sdk=sdk, secret_getter=lambda service, username: "fake"
        )
    )
    handle = provider.start(provider.provision("sandbox1", bundle()), {"KEY": "value"})
    assert handle["sandbox_id"] == "sb-1"
    assert provider.status(handle) == "running"
    provider.stop(handle)
    provider.teardown(handle)
    assert "terminated" in calls if kind == "modal" else "killed" in calls


def test_code_publication_uses_only_the_run_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, ...]] = []

    def git(root: Path, *args: str) -> str:
        calls.append(args)
        return "runs/code1" if args == ("branch", "--show-current") else ""

    monkeypatch.setattr("qmx_remote.code.git", git)
    publish(tmp_path, "code1")
    assert calls[-1] == ("push", "origin", "HEAD:refs/heads/runs/code1")
    with pytest.raises(RemoteError, match="changed branches"):
        publish(tmp_path, "other")


def test_incremental_results_survive_a_hard_killed_worker(tmp_path: Path) -> None:
    config = settings(tmp_path)
    provider = FakeProvider()
    runs = RemoteRuns(tmp_path / "home", config, providers=lambda target, bucket: provider)
    submitted = runs.start(
        bundle(
            command=[
                sys.executable,
                "-u",
                "-c",
                "import time; print('durable first line', flush=True); time.sleep(300)",
            ]
        )
    )
    run_id = str(submitted["run_id"])
    store = ResultsStore(config.bucket)
    with subprocess.Popen(
        [sys.executable, "-m", "qmx_remote.worker", "--bucket", config.bucket, "--run-id", run_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    ) as process:
        try:
            deadline = time.monotonic() + 150
            while time.monotonic() < deadline:
                manifest = store.read(run_id)
                if any(item.path == "logs/worker.log" for item in manifest.artifacts):
                    break
                if process.poll() is not None:
                    pytest.fail("Worker exited before its first incremental log flush")
                time.sleep(0.1)
            else:
                pytest.fail("Worker never published its incremental log")
        finally:
            children = psutil.Process(process.pid).children(recursive=True)
            # Cut off the shipper first; a killed job must not get a graceful final flush.
            process.kill()
            for child in children:
                child.kill()
            process.wait()
    recovered = store.fetch(run_id, tmp_path / "recovered")
    assert recovered.status == "running"
    assert "durable first line" in (tmp_path / "recovered/logs/worker.log").read_text()
