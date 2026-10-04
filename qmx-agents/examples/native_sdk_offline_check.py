"""Version/schema checks only: never initialize auth or run a native session."""

from __future__ import annotations

import argparse
import inspect
import json
import subprocess
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from claude_agent_sdk import ClaudeAgentOptions
from claude_agent_sdk._cli_version import __cli_version__
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from codex_cli_bin import (  # pyright: ignore[reportMissingTypeStubs] - official runtime package
    bundled_codex_path,
)
from openai_codex import AsyncCodex
from openai_codex._runtime_requirements import require_runtime_version


def check_codex(executable: Path) -> dict[str, object]:
    reported = subprocess.run(
        [str(executable), "--version"], capture_output=True, text=True, check=True, timeout=10
    ).stdout.strip()
    runtime_version = reported.removeprefix("codex-cli ")
    require_runtime_version(runtime_version)
    with TemporaryDirectory(prefix="qmx-native-schema-") as directory:
        subprocess.run(
            [str(executable), "app-server", "generate-json-schema", "--out", directory],
            capture_output=True,
            check=True,
            timeout=30,
        )
        schema = json.loads((Path(directory) / "v2" / "TurnStartParams.json").read_text())
        policies = schema["definitions"]["SandboxPolicy"]["oneOf"]
        read_only = next(item for item in policies if item["title"] == "ReadOnlySandboxPolicy")
        read_fields = sorted(read_only["properties"])
    return {
        "executable": str(executable),
        "version": runtime_version,
        "sdk_version_floor_passed": True,
        "read_only_policy_fields": read_fields,
        "restricted_read_roots_available": "readOnlyAccess" in read_fields,
        "native_session_admitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed-codex", type=Path, required=True)
    parser.add_argument("--claude", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert version("openai-codex") == "0.160.0"
    assert version("openai-codex-cli-bin") == "0.160.0"
    assert version("claude-agent-sdk") == "0.2.163"
    # Bind the exact public high-level lifecycle arguments offline.
    inspect.signature(AsyncCodex.thread_start).bind(
        None,
        cwd="fixture",
        model=None,
        developer_instructions="host",
    )
    inspect.signature(AsyncCodex.thread_resume).bind(None, "thread-fixture", cwd="fixture")
    claude_version = subprocess.run(
        [str(args.claude), "--version"], capture_output=True, text=True, check=True, timeout=10
    ).stdout.strip()
    assert claude_version == "2.1.286 (Claude Code)"
    options = ClaudeAgentOptions(
        cli_path=args.claude,
        tools=[],
        setting_sources=[],
        strict_mcp_config=True,
        skills=[],
        agents={},
        plugins=[],
        verbatim_prompts=True,
        extra_args={"disable-slash-commands": None},
    )
    command = SubprocessCLITransport("fixture", options)._build_command()  # pyright: ignore[reportPrivateUsage] - offline flag construction
    assert command[command.index("--tools") + 1] == ""
    assert "--setting-sources=" in command and "--strict-mcp-config" in command
    assert "--disable-slash-commands" in command
    report = {
        "sdk_pins": {
            name: version(name)
            for name in (
                "openai-codex",
                "openai-codex-cli-bin",
                "claude-agent-sdk",
                "mcp",
            )
        },
        "codex": [check_codex(args.installed_codex), check_codex(bundled_codex_path())],
        "claude": {
            "version": claude_version,
            "sdk_expected_cli_version": __cli_version__,
            "tool_removal_flags_verified": True,
            "verbatim_prompts": options.verbatim_prompts,
            "managed_policy_isolated": False,
            "native_session_admitted": False,
        },
        "authentication_performed": False,
        "model_calls": 0,
        "subscription_connection_verified": False,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Offline SDK/runtime checks passed; neither native session backend is admitted.")


if __name__ == "__main__":
    main()
