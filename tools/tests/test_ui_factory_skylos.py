"""Skylos 4.33.2 .svelte parser check. Auto-detect is not proof of coverage."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "skylos_svelte"


def test_skylos_pin_in_ci() -> None:
    text = (ROOT / ".github" / "workflows" / "skylos.yml").read_text(encoding="utf-8")
    assert "skylos==4.33.2" in text
    assert "ui-integration" in text


@pytest.mark.skipif(shutil.which("skylos") is None, reason="skylos CLI not on PATH")
def test_svelte_secret_fixture(tmp_path: Path) -> None:
    src = FIXTURES / "must_flag" / "secret.svelte"
    dest = tmp_path / "secret.svelte"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    report = tmp_path / "report.json"
    proc = subprocess.run(
        ["skylos", str(tmp_path), "-a", "--no-upload", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = proc.stdout or ""
    if payload.strip():
        report.write_text(payload, encoding="utf-8")
    parsed = None
    try:
        stripped = payload.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            parsed = json.loads(payload)
        else:
            parsed = None
    except json.JSONDecodeError:
        parsed = None
    blob = payload.lower() + (proc.stderr or "").lower()
    saw_secret = "akia" in blob or "secret" in blob
    if not saw_secret:
        pytest.fail(
            "Skylos 4.33.2 did not report the .svelte secret fixture; "
            "do not treat extension auto-detect as full Svelte coverage. "
            f"exit={proc.returncode} parsed={parsed is not None}"
        )
