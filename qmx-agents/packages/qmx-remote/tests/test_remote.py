from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal
from unittest.mock import Mock

import pytest
from qmx_ledger.journal import fingerprint

from qmx_remote.code import publish
from qmx_remote.models import RemoteError, RemoteSettings, RunBundle, Target
from qmx_remote.providers import AmpProvider, E2BProvider, ModalProvider, SSHProvider


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


def test_amp_provider_takes_only_delegated_agent_tasks() -> None:
    target = Target(provider="amp", host="vps", image="worker", runner_id="runner")
    task = bundle("amp", inputs={"prompt": "Research this"})
    assert AmpProvider(target).provision("amp1", task)["run_id"] == "amp1"
    with pytest.raises(RemoteError, match="delegated agent tasks only"):
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
