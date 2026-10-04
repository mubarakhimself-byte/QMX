from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
from google.protobuf import descriptor_pb2
from qmf.core.refusal import is_ok, is_refusal
from qmf.venue.proto import descriptor_set_digest
from qmn.host.configured_runtime import assess_configured_runtime

_QMN = Path(__file__).resolve().parents[1]
_DEPLOY = _QMN / "deploy"


def _load() -> ModuleType:
    name = "qmn_deploy_config_test"
    spec = importlib.util.spec_from_file_location(name, _DEPLOY / "config.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def config_mod() -> ModuleType:
    return _load()


def test_init_and_validate_run_pure_scaffold_and_report_boot_block(
    config_mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert config_mod.main(["init", "--root", str(tmp_path)]) == 0
    artifact = json.loads((tmp_path / "node-config.json").read_text(encoding="utf-8"))
    assert artifact["class"] == "resolved-node-config"
    assert len(artifact["rows"]) == 71
    capsys.readouterr()

    assert config_mod.main(["validate", "--root", str(tmp_path)]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "schema_valid_boot_blocked"
    assert report["may_boot"] is False

    before = (tmp_path / "node-config.json").read_bytes()
    assert config_mod.main(["init", "--root", str(tmp_path)]) == 2
    assert (tmp_path / "node-config.json").read_bytes() == before


def test_explain_uses_pure_layer_report_without_secret_values(
    config_mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert config_mod.main(["init", "--root", str(tmp_path)]) == 0
    capsys.readouterr()
    assert config_mod.main(["explain", "--root", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["layer_precedence"] == ["roster", "bms", "book", "node_defaults"]
    assert report["row_count"] == 71
    assert report["may_bind_role_live"] is False
    assert "<secret-ref>" not in json.dumps(report["rows"])


@pytest.mark.parametrize("name", ["missing.json", "../outside.json"])
def test_deployment_validate_refuses_missing_or_traversal_without_child_process(
    config_mod: ModuleType, tmp_path: Path, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []

    def record_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(
        subprocess,
        "run",
        record_run,
    )
    assert config_mod.main(["validate-deployment", "--root", str(tmp_path), "--path", name]) == 2
    assert calls == []


def test_deployment_validate_refuses_symlink_without_child_process(
    config_mod: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = tmp_path.parent / "qmn-outside-deployment.json"
    outside.write_text("{}", encoding="utf-8")
    link = tmp_path / "qmn-deployment.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    calls: list[object] = []
    def record_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(
        subprocess,
        "run",
        record_run,
    )
    assert config_mod.main(["validate-deployment", "--root", str(tmp_path)]) == 2
    assert calls == []


def test_valid_pinned_deployment_uses_actual_preflight_module_no_credentials(
    config_mod: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deployment = tmp_path / "qmn-deployment.json"
    deployment.write_text("{}", encoding="utf-8")
    observed: dict[str, object] = {}

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            argv,
            0,
            '{"status":"preflight_valid_not_activated","provider_calls":0}\n',
            "",
        )

    monkeypatch.setattr(subprocess, "run", runner)
    assert config_mod.main(["validate-deployment", "--root", str(tmp_path)]) == 0
    capsys.readouterr()
    argv = cast("list[str]", observed["argv"])
    assert argv[argv.index("-m") + 1] == "qmn.host.configured_runtime"
    assert str(deployment) in argv
    assert "--qmx-root" in argv
    assert "--password" not in argv and "--token" not in argv
    arguments = cast("dict[str, object]", observed["kwargs"])
    environment = cast("dict[str, str]", arguments["env"])
    assert "SYSTEMD_CREDENTIALS_DIRECTORY" not in environment
    assert "VENUE_CLIENT_SECRET" not in environment
    assert "PYTHONPATH" not in environment
    if os.name == "nt":
        assert environment.get("SYSTEMROOT") == os.environ["SYSTEMROOT"]


def test_deployment_child_runs_real_host_preflight_for_selected_file(
    config_mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    deployment = tmp_path / "qmn-deployment.json"
    deployment.write_text("{}", encoding="utf-8")

    assert config_mod.main(["validate-deployment", "--root", str(tmp_path)]) == 2
    output = capsys.readouterr()
    assert "versioned configured-runtime fields" in output.err
    assert "provider_calls" in output.err


def test_real_governed_deployment_document_passes_child_preflight_without_activation(
    config_mod: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixture_path = _QMN / "tests" / "test_qmn_configured_runtime.py"
    spec = spec_from_file_location("qmn_configured_runtime_fixture_for_deploy", fixture_path)
    assert spec is not None and spec.loader is not None
    fixture_mod = module_from_spec(spec)
    sys.modules[spec.name] = fixture_mod
    spec.loader.exec_module(fixture_mod)

    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "deploy-fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    digest = descriptor_set_digest(descriptor_set.SerializeToString())
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(descriptor_set.SerializeToString())
    generated = fixture_mod._deployment(tmp_path, descriptor_path, digest.value)
    generated.rename(tmp_path / "qmn-deployment.json")

    assert config_mod.main(["validate-deployment", "--root", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "preflight_valid_not_activated"
    assert report["provider_calls"] == 0
    assert report["provider_ready"] is False
    assert report["activation_authorized"] is False


def test_config_init_rejects_parent_swap_to_symlink_without_outside_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import qmn.config.cli as config_cli

    root = tmp_path / "root"
    root.mkdir()
    parent = root / "configs"
    parent.mkdir()
    held = root / "held"
    outside = tmp_path / "outside"
    outside.mkdir()
    target = parent / "node.json"
    original_open = os.open
    swapped = False

    def swap_before_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal swapped
        if (
            path == "configs"
            and dir_fd is not None
            and flags & cast("int", getattr(os, "O_DIRECTORY", 0))
        ):
            parent.rename(held)
            parent.symlink_to(outside, target_is_directory=True)
            swapped = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(config_cli.os, "open", swap_before_open)
    assert config_cli.main(["init", "--root", str(root), "--path", "configs/node.json"]) == 2
    assert swapped
    assert not (outside / "node.json").exists()
    assert not target.exists()


def test_config_read_refuses_fifo_without_blocking(tmp_path: Path) -> None:
    import qmn.config.cli as config_cli

    fifo = tmp_path / "config.json"
    mkfifo = cast("Callable[[str | os.PathLike[str]], None] | None", getattr(os, "mkfifo", None))
    if mkfifo is None:
        pytest.skip("FIFO creation is unavailable")
    try:
        mkfifo(fifo)
    except (OSError, NotImplementedError):
        pytest.skip("FIFO creation is unavailable")
    assert config_cli.main(["validate", "--root", str(tmp_path), "--path", fifo.name]) == 2

    host_fifo = tmp_path / "qmn-deployment.json"
    mkfifo(host_fifo)
    assessed = assess_configured_runtime(host_fifo, qmx_root=tmp_path)
    assert is_refusal(assessed)


def test_host_preflight_rejects_symlink_leaf_and_directory_without_following(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / "outside-qmn-config-target"
    outside.write_text("{}", encoding="utf-8")
    leaf = tmp_path / "leaf.json"
    directory = tmp_path / "linked-dir"
    try:
        leaf.symlink_to(outside)
        directory.symlink_to(outside.parent, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    assert is_refusal(assess_configured_runtime(leaf, qmx_root=tmp_path))
    nested = directory / outside.name
    assert is_refusal(assess_configured_runtime(nested, qmx_root=tmp_path))


def test_config_init_refuses_when_safe_dirfd_operations_are_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import qmn.config.cli as config_cli

    monkeypatch.setattr(config_cli, "_DIRFD_IO_SUPPORTED", False)
    assert config_cli.main(["init", "--root", str(tmp_path), "--path", "node-config.json"]) == 2
    assert not (tmp_path / "node-config.json").exists()


def test_unit_template_pins_operator_deployment_under_current_tree() -> None:
    unit = (_DEPLOY / "systemd" / "templates" / "qmn.service.in").read_text(encoding="utf-8")
    assert "Environment=QMX_ROOT=/opt/qmx/current" in unit
    assert "Environment=QMN_DEPLOYMENT_CONFIG=/opt/qmx/current/qmn-deployment.json" in unit
