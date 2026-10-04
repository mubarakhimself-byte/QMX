"""Test-only daemon child with the released Codex SDK and a protocol fixture."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from openai_codex.client import CodexClient, CodexConfig
from qma.daemon.request_runtime import native_composition
from qma.daemon.request_runtime.native_codex import CONFIG, CodexSessionBackend

proof_path = Path(__file__).resolve().parents[3] / "examples/native_daemon_proof.py"
proof_spec = importlib.util.spec_from_file_location("native_daemon_proof_fixture", proof_path)
assert proof_spec and proof_spec.loader
native_daemon_proof = importlib.util.module_from_spec(proof_spec)
proof_spec.loader.exec_module(native_daemon_proof)

root, boot = Path(sys.argv[1]), sys.argv[2]


def backend(**options: Any) -> CodexSessionBackend:
    arguments = {
        "snapshot_ref": options["tool_schemas"]["research_browse"]["properties"]["snapshot_ref"][
            "enum"
        ][0],
        "locator": "README.md",
    }
    scenario_file = root / "fixture-scenario.txt"
    scenario = scenario_file.read_text().strip() if scenario_file.exists() else "proof"

    def client_factory(*, config: CodexConfig, approval_handler: Any) -> CodexClient:
        config.launch_args_override = (
            sys.executable,
            str(Path(__file__).with_name("native_codex_fixture.py")),
            json.dumps(CONFIG),
            json.dumps(arguments),
            scenario,
            str(options["empty_workspace"]),
            str(root / "fixture-protocol.jsonl"),
        )
        return CodexClient(config=config, approval_handler=approval_handler)

    return CodexSessionBackend(**options, client_factory=client_factory, verify_runtime=False)


def forbidden(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("Native route cannot run generic inference or paid API fallback")


if __name__ == "__main__":
    with (
        patch.object(native_composition, "CodexSessionBackend", backend),
        patch("qma.daemon.request_runtime.tool_loop.ToolLoopProvider.execute", forbidden),
        patch(
            "qma.daemon.request_runtime.http_provider.ChatCompletionsProvider.execute", forbidden
        ),
    ):
        asyncio.run(native_daemon_proof.worker(root, boot))
