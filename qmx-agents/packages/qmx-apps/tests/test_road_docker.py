"""Road proofs must retain the app's T2 boundary, including on failure."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

import qmx_apps.docker as container
from qmx_apps.docker import DockerSupervisor
from qmx_apps.manifest import Definition
from qmx_apps.road.validation import validate
from qmx_apps.volume import Volume

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"


@pytest.mark.parametrize("timeout", [False, True])
def test_own_tests_keep_container_boundary_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timeout: bool
) -> None:
    source = tmp_path / "source"
    shutil.copytree(EXAMPLE, source)
    manifest = source / "app.toml"
    manifest.write_text(manifest.read_text().replace("network = []", 'network = ["example.com"]'))
    image = Definition.load(source)
    commands: list[tuple[str, ...]] = []
    volume: Path | None = None

    def docker(*args: str, **kwargs: Any) -> str:
        nonlocal volume
        commands.append(args)
        if args[0] == "create":
            assert args[args.index("--network") + 1] == "none"
            binding = next(arg for arg in args if arg.startswith("type=bind,src="))
            volume = Path(binding.removeprefix("type=bind,src=").removesuffix(",dst=/volume"))
            assert (volume / "road").is_dir()
            assert f"type=bind,src={volume / 'road'},dst=/volume/road,readonly" in args
            config = json.loads(args[-1])
            assert config["tier"] == "T2" and config["tests"] is True
            assert config["recorded"] is True and config["jobs"] == []
        return ""

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        assert command[:4] == ["docker-fixture", "start", "--attach", "--interactive"]
        assert volume is not None
        if timeout:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        (volume / "data/test-result.json").write_text('{"passed": true, "tests_run": 1}')
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(container, "docker", docker)

    def which(name: str) -> str:
        return "docker-fixture"

    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(subprocess, "run", run)
    owner = DockerSupervisor(tmp_path / "home")
    Volume(owner.home, image.manifest.id).create(agents=False)
    try:
        _, result = validate(owner, image, "tests")
        assert result["passed"] is (not timeout)
        assert not any(args[0] == "network" for args in commands)
        assert any(args[:3] == ("container", "rm", "--force") for args in commands)
        assert volume is not None and not volume.exists()
    finally:
        owner.close()
