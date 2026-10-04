"""Actual authenticated daemon routing/restart against released SDK protocol peers."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("openai_codex", reason="Install optional pinned native SDKs")
pytest.importorskip("claude_agent_sdk", reason="Install optional pinned native SDKs")


def proof_module() -> Any:
    path = Path(__file__).resolve().parents[3] / "examples/native_daemon_proof.py"
    spec = importlib.util.spec_from_file_location("native_daemon_proof_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def options(tmp_path: Path) -> list[str]:
    return [
        "--provider",
        "codex",
        "--executable",
        str(tmp_path / "fake-codex.exe"),
        "--native-home",
        str(tmp_path / "home"),
        "--empty-workspace",
        str(tmp_path / "empty"),
        "--root",
        str(tmp_path / "proof"),
    ]


def install_peer(proof: Any, monkeypatch: Any) -> None:
    def start(root: Path, boot: str) -> tuple[subprocess.Popen[str], dict[str, Any]]:
        stderr = (root / f"fixture-daemon-{boot}.stderr").open("w", encoding="utf-8")
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).with_name("native_daemon_fixture.py")),
                str(root),
                boot,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
        )
        stderr.close()
        try:
            line = proof.read_pipe_line(process)
            assert line, (root / f"fixture-daemon-{boot}.stderr").read_text()
            return process, json.loads(line)
        except Exception:
            proof.stop_worker(process)
            raise

    monkeypatch.setattr(proof, "start_worker", start)


def test_daemon_proof_default_does_not_prepare_or_launch(tmp_path: Path, monkeypatch: Any) -> None:
    proof = proof_module()

    def forbidden(_args: Any) -> None:
        pytest.fail("Dry proof cannot prepare")

    monkeypatch.setattr(proof, "prepare", forbidden)
    assert proof.main(options(tmp_path)) == 0
    assert not list(tmp_path.iterdir())


def test_existing_proof_store_is_never_overwritten(tmp_path: Path) -> None:
    proof = proof_module()
    root = tmp_path / "proof"
    root.mkdir()
    sentinel = root / "daemon-proof-result.json"
    sentinel.write_text("original evidence")
    assert proof.main([*options(tmp_path), "--allow-live"]) == 1
    assert sentinel.read_text() == "original evidence"


def test_authenticated_native_operator_start_fresh_process_resume_and_host_receipt(
    tmp_path: Path, monkeypatch: Any
) -> None:
    proof = proof_module()
    (tmp_path / "home").mkdir()
    (tmp_path / "empty").mkdir()
    install_peer(proof, monkeypatch)
    assert proof.main([*options(tmp_path), "--allow-live"]) == 0
    root = tmp_path / "proof"
    report = json.loads((root / "daemon-proof-result.json").read_text())
    assert report["verified"] and len(set(report["pids"])) == 2
    assert report["host_effect_receipts"] == 1
    trace = [
        json.loads(line) for line in (root / "fixture-protocol.jsonl").read_text().splitlines()
    ]
    turns = [row["params"] for row in trace if row.get("method") == "turn/start"]
    assert len(turns) == 2
    assert "NATIVE-PROOF-" in json.dumps(turns[0]) and "NATIVE-PROOF-" not in json.dumps(turns[1])
    assert sum(row.get("method") == "thread/start" for row in trace) == 1
    assert sum(row.get("method") == "thread/resume" for row in trace) == 1
    responses = [row["result"] for row in trace if row.get("id") == "server-call"]
    assert len(responses) == 1 and responses[0]["success"]
    assert "README.md" in json.dumps(responses[0]) and "IDEA.md" not in json.dumps(responses[0])


def test_authenticated_native_cancel_scope_denial_and_revocation_after_restart(
    tmp_path: Path, monkeypatch: Any
) -> None:
    proof = proof_module()
    (tmp_path / "home").mkdir()
    (tmp_path / "empty").mkdir()
    install_peer(proof, monkeypatch)
    assert proof.main([*options(tmp_path), "--allow-live"]) == 0
    root = tmp_path / "proof"
    (root / "fixture-scenario.txt").write_text("wait")

    async def exercise() -> None:
        process, info = proof.start_worker(root, "three")
        writer = None
        try:
            with pytest.raises(RuntimeError, match="Authenticated daemon connection refused"):
                await proof.connect(info, proof="wrong-proof")
            reader, writer = await proof.connect(info)
            params = {
                "product_session_ref": proof.SESSION,
                "profile_id": "reader",
                "prompt": "Wait for host cancellation",
                "idempotency_key": "cancel",
            }
            for addition in (
                {"thread_id": "model-session"},
                {"provider_id": "paid-api"},
                {"cwd": "private"},
                {"profile_id": "unconfigured"},
                {"product_session_ref": "psess:other"},
            ):
                assert "error" in await proof.rpc(
                    reader, writer, "submit_agent_request", params | addition
                )
            row = proof.receipt(await proof.rpc(reader, writer, "submit_agent_request", params))
            trace_path = root / "fixture-protocol.jsonl"
            deadline = time.monotonic() + 5
            while (
                sum(
                    json.loads(line).get("method") == "turn/start"
                    for line in trace_path.read_text().splitlines()
                )
                < 3
            ):
                assert time.monotonic() < deadline
                await asyncio.sleep(0.01)
            assert "error" in await proof.rpc(
                reader,
                writer,
                "cancel_agent_request",
                {"product_session_ref": "psess:other", "request_id": row["request_id"]},
            )
            proof.receipt(
                await proof.rpc(
                    reader,
                    writer,
                    "cancel_agent_request",
                    {"product_session_ref": proof.SESSION, "request_id": row["request_id"]},
                )
            )
            cancelled = await proof.wait_result(reader, writer, row["request_id"])
            assert cancelled["status"] == "cancelled", cancelled
            records = proof.control(process, "evidence")
            assert any(
                item["kind"] == "native_session" and item["body"]["status"] == "interrupted"
                for item in records
            )
            before = trace_path.read_text()
            proof.control(process, "revoke")
            refused = proof.receipt(
                await proof.rpc(
                    reader, writer, "submit_agent_request", params | {"idempotency_key": "revoked"}
                )
            )
            failed = await proof.wait_result(reader, writer, refused["request_id"])
            assert failed["status"] == "failed" and trace_path.read_text() == before
            denied = proof.receipt(
                await proof.rpc(
                    reader,
                    writer,
                    "get_agent_request",
                    {"product_session_ref": proof.SESSION, "request_id": row["request_id"]},
                )
            )
            assert denied["content_withheld"]
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            proof.stop_worker(process)

    asyncio.run(exercise())
