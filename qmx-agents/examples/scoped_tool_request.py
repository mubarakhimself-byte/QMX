"""Runnable scoped tool request over a real QMA product session and read grant.

The installed text_stats handler counts characters and words in supplied text.
It registers its own example-local operation descriptor and a real read grant;
it does not invoke market/domain operations. Diagnostic mode performs no model/provider call.
Codex mode requires explicit --allow-live and an authenticated dedicated home.
"""

from __future__ import annotations

# ruff: noqa: E402 - unpacked reference example bootstraps local source imports
import argparse
import json
import socket
import sys
import threading
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Reference example works from an unpacked candidate without installation.
_CANDIDATE = Path(__file__).resolve().parents[2]
_source_paths = sorted(_CANDIDATE.glob("packages/*/src"))
_source_paths = _source_paths + sorted((_CANDIDATE / "qmx-agents/packages").glob("*/src"))
sys.path[:0] = [str(path) for path in _source_paths]

from qma.core.operations import public_operation_descriptors
from qma.core.operations.descriptor import OperationConfiguration, SupportedDoor
from qma.core.vocabulary.enums import DoorAdapter, LifecycleVerb, OutputShape
from qma.daemon import AuthoritativeJournal, PersistenceSubstrate, ProductSessionService
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.request_runtime import (
    CopilotProfile,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestRuntime,
    RequestSpec,
)
from qma.daemon.request_runtime.providers import CodexAppServerProvider, ProviderCancelled
from qma.daemon.request_runtime.tool_loop import (
    LoopLimits,
    ToolBinding,
    ToolLoopProvider,
    configured_loop_id,
)
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord
from qmf.core import is_refusal


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class DiagnosticActions:
    """Deterministic structured actions, clearly distinct from live inference."""

    capabilities = ProviderCapabilities("diagnostic-actions")

    def __init__(self) -> None:
        self.calls = 0

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        if cancellation.is_set():
            raise ProviderCancelled()
        self.calls += 1
        context = json.loads(request.prompt)
        observations = context["tool_observations"]
        if not observations:
            action = {
                "type": "tool",
                "tool": "text_stats",
                "arguments": {"text": context["user_request"]},
            }
        else:
            action = {
                "type": "final",
                "content": "DIAGNOSTIC: " + json.dumps(observations[-1]["result"], sort_keys=True),
            }
        return ProviderResult(json.dumps(action), deployment_id="diagnostic-not-model")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--provider", choices=("diagnostic", "codex"), default="diagnostic")
    parser.add_argument("--profile", choices=("reader", "summary-only"), default="reader")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--max-provider-calls", type=int, default=2)
    args = parser.parse_args(argv)
    if args.provider == "codex" and (
        not args.allow_live or not args.codex_home or not args.codex_executable
    ):
        parser.error("codex requires --allow-live, --codex-home and --codex-executable")
    provider = (
        CodexAppServerProvider(args.codex_executable, args.codex_home)
        if args.provider == "codex"
        else DiagnosticActions()
    )
    configuration = {
        "example_version": "text_stats@1",
        "underlying": provider.capabilities.provider_id,
        "max_provider_calls": str(args.max_provider_calls),
    }
    if args.provider == "codex":
        configuration["executable"] = str(args.codex_executable.resolve())
        configuration["dedicated_home"] = str(args.codex_home.resolve())
    loop_id = configured_loop_id(provider, configuration)
    boot = str(uuid.uuid4())
    opened = PersistenceSubstrate.open(
        args.root.resolve(), machine=socket.gethostname(), boot_epoch_id=boot
    )
    if is_refusal(opened):
        print(repr(opened), file=sys.stderr)
        return 1
    substrate, journal = opened.value, None
    try:
        bound = AuthoritativeJournal.bind(substrate, clock=InjectedUtcClock(boot))
        if is_refusal(bound):
            print(repr(bound), file=sys.stderr)
            return 1
        journal = bound.value
        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        restored = sessions.restore_from_journal()
        if is_refusal(restored):
            print(repr(restored), file=sys.stderr)
            return 1
        session_id = "psess:scoped-example"
        contribution = ContributionRecord("sdk.example:text-stats", "0.1.0", availability="enabled")
        instance = InstanceRecord("inst:scoped-example", 1)
        descriptor = next(
            item
            for item in public_operation_descriptors()
            if item.op_id == "qmb.analysis.project" and item.version == 1
        )
        descriptor = replace(
            descriptor,
            op_id="qma.example.text_stats",
            owner="COMP-QMA-DAEMON",
            input_schema="qma.example.text_stats.v1",
            output_shape=OutputShape.VALUE,
            configuration=OperationConfiguration({}, ("text",), ()),
            declared_operation_dependencies=(),
            documentation_refs=("examples/scoped_tool_request.py",),
            units=None,
            permission_requests=("example.text_stats.read",),
            lifecycle_verbs=(LifecycleVerb.QUERY_STATE,),
            supported_doors=(SupportedDoor(DoorAdapter.LIBRARY, "in-process"),),
        )
        session = sessions.get(session_id)
        if is_refusal(session):
            session = sessions.mint(
                product_session_id=session_id,
                profile="authoring",
                principal="operator",
                contribution={
                    "qualified_id": contribution.qualified_id,
                    "package_version": contribution.package_version,
                },
                instance_id=instance.instance_id,
                config_revision=instance.config_revision,
                as_of=utc_now(),
                granted_ops=(),
                scope_path=(),
            )
        if is_refusal(session):
            print(repr(session), file=sys.stderr)
            return 1
        grant_id = "grant:scoped-example-read"
        granted = sessions.resolve_grant(session_id, grant_id)
        if is_refusal(granted):
            granted = sessions.host_grant(
                session_id,
                grant_id=grant_id,
                op_id=descriptor.op_id,
                op_version=descriptor.version,
                effect_class="read",
                parameter_ceiling={"allow_keys": ["text"]},
                expires_at=(datetime.now(UTC) + timedelta(days=365))
                .isoformat()
                .replace("+00:00", "Z"),
            )
        if is_refusal(granted):
            print(repr(granted), file=sys.stderr)
            return 1
        callbacks: list[dict[str, object]] = []

        def analyze(arguments: Mapping[str, object]) -> Mapping[str, object]:
            text = arguments.get("text")
            if not isinstance(text, str) or len(text.encode("utf-8")) > 8192:
                raise ValueError("text_stats requires a UTF-8 string of at most 8192 bytes")
            callbacks.append(dict(arguments))
            return {
                "characters": len(text),
                "words": len(text.split()),
                "source": "request-supplied-text",
            }

        loop = ToolLoopProvider(
            provider,
            provider_id=loop_id,
            tools={
                "text_stats": ToolBinding(descriptor, contribution, instance, grant_id, analyze)
            },
            profile_tools={"reader": frozenset({"text_stats"}), "summary-only": frozenset()},
            now=utc_now,
            limits=LoopLimits(max_model_calls=args.max_provider_calls, max_tool_calls=1),
        )
        runtime = RequestRuntime(
            journal=journal, product_sessions=sessions, providers={loop_id: loop}
        )
        loop.bind_runtime(runtime)
        session = sessions.get(session_id)
        if is_refusal(session):
            print(repr(session), file=sys.stderr)
            return 1
        submitted = runtime.submit(
            RequestSpec(
                args.key,
                "operator",
                session_id,
                session.value.context_revision,
                CopilotProfile(args.profile),
                args.prompt,
                loop_id,
                model=args.model,
                timeout_seconds=args.timeout,
            )
        )
        if is_refusal(submitted):
            print(repr(submitted), file=sys.stderr)
            return 1
        result = runtime.execute(submitted.value.request_id)
        if is_refusal(result):
            print(repr(result), file=sys.stderr)
            return 1
        print(
            json.dumps(
                {
                    "request": asdict(result.value),
                    "tool_callbacks_this_process": len(callbacks),
                    "diagnostic_provider_calls_this_process": provider.calls
                    if isinstance(provider, DiagnosticActions)
                    else None,
                    "selected_live_provider": args.provider == "codex",
                    "recorded_live_provider": result.value.result is not None
                    and result.value.result.deployment_id == "codex-native",
                },
                ensure_ascii=False,
            )
        )
        return 0 if result.value.status == "completed" else 1
    finally:
        if journal is not None:
            journal.close()
        substrate.close()


if __name__ == "__main__":
    raise SystemExit(main())
