"""Two subscription-native turns and one real host-granted metadata operation.

Default is a dry readiness report. --allow-live is for a separately authorized
human proof after native login; never performs login or reads credential files.
"""

from __future__ import annotations

# ruff: noqa: E402 - unpacked candidate example bootstraps local source imports
import argparse
import json
import socket
import sys
import uuid
from collections.abc import Mapping
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, cast

_CANDIDATE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(path) for path in sorted(_CANDIDATE.glob("packages/*/src"))]
sys.path[:0] = [str(path) for path in sorted((_CANDIDATE / "qmx-agents/packages").glob("*/src"))]

from qma.daemon import AuthoritativeJournal, PersistenceSubstrate, ProductSessionService
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.knowledge.plain_file import PlainFileLibrarySource
from qma.daemon.knowledge.service import KnowledgeService
from qma.daemon.request_runtime import CopilotProfile, RequestRuntime, RequestSpec
from qma.daemon.request_runtime.domain_tools import create_research_browse_binding
from qma.daemon.request_runtime.native_composition import compose_native_metadata_provider
from qma.daemon.request_runtime.providers import ProviderError
from qma.daemon.request_runtime.service import RequestRecord
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord
from qmf.core import Result, is_refusal


def value[T](result: Result[T]) -> T:
    if is_refusal(result):
        raise RuntimeError("Synthetic host operation refused")
    return result.value


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--native-home", type=Path, required=True)
    parser.add_argument("--empty-workspace", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, required=True, help="New synthetic host store; must not exist"
    )
    parser.add_argument("--model")
    parser.add_argument("--allow-live", action="store_true")
    parser.add_argument("--native-policy-reviewed", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_live:
        print(
            json.dumps(
                {
                    "mode": "dry",
                    "backend": args.provider,
                    "model_calls": 0,
                    "subscription_connection_verified": False,
                    "next": "Separate approval, human native login, then --allow-live",
                }
            )
        )
        return 0
    if args.provider == "claude" and not args.native_policy_reviewed:
        parser.error("Claude requires a reviewed personal unmanaged native policy")
    root = args.root.resolve()
    if root.exists():
        parser.error(
            "proof root must be new; previous/unknown proof cannot be automatically replayed"
        )
    if (
        root == args.native_home.resolve()
        or root in args.native_home.resolve().parents
        or args.native_home.resolve() in root.parents
    ):
        parser.error("proof store and native authentication home must be separate")
    root.mkdir(parents=True)
    corpus = root / "corpus"
    corpus.mkdir()
    (corpus / "proof.md").write_text(
        "Synthetic corpus for the native metadata proof.", encoding="utf-8"
    )
    boot = uuid.uuid4().hex
    substrate = value(
        PersistenceSubstrate.open(root / "store", machine=socket.gethostname(), boot_epoch_id=boot)
    )
    journal: AuthoritativeJournal | None = None
    report: dict[str, Any] = {
        "backend": args.provider,
        "subscription_connection_verified": False,
        "host_operations": 0,
        "requests": [],
    }
    try:
        journal = value(AuthoritativeJournal.bind(substrate, clock=InjectedUtcClock(boot)))
        sessions = ProductSessionService(journal=journal, sqlite=substrate.sqlite)
        contribution = ContributionRecord("analysis-backtest:qmb", "0.1.0", "enabled")
        instance = InstanceRecord("inst:native-proof", 1)
        session_id, grant_id = "psess:native-proof", "grant:native-proof-metadata"
        value(
            sessions.mint(
                product_session_id=session_id,
                profile="authoring",
                principal="operator",
                contribution={
                    "qualified_id": contribution.qualified_id,
                    "package_version": contribution.package_version,
                },
                instance_id=instance.instance_id,
                config_revision=1,
                as_of=utc_now(),
                granted_ops=(),
                scope_path=(),
            )
        )
        value(
            sessions.host_grant(
                session_id,
                grant_id=grant_id,
                op_id="qml.research.browse",
                op_version=1,
                effect_class="read",
                parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
                expires_at=(datetime.now(UTC) + timedelta(minutes=10))
                .isoformat()
                .replace("+00:00", "Z"),
            )
        )
        knowledge = KnowledgeService()
        value(knowledge.bind("native-proof", PlainFileLibrarySource(corpus, "native-proof")))
        snapshot = value(knowledge.snapshot("native-proof"))
        binding = create_research_browse_binding(
            knowledge,
            source_id="native-proof",
            snapshot_ref=snapshot.id,
            allowed_locators=("proof.md",),
            contribution=contribution,
            instance=instance,
            grant_id=grant_id,
        )
        original = binding.execute

        def metadata(arguments: Mapping[str, object]) -> Mapping[str, object]:
            if report["host_operations"] >= 1:
                raise ProviderError(
                    "tool_denied", "Exactly one host operation allowed in this proof"
                )
            result = original(arguments)
            report["host_operations"] += 1
            return result

        binding = replace(binding, execute=metadata)
        runtime = RequestRuntime(journal=journal, product_sessions=sessions, providers={})
        provider_id = f"native-proof:{args.provider}"
        runtime.providers[provider_id] = compose_native_metadata_provider(
            runtime,
            provider_id=provider_id,
            backend=cast("Literal['codex', 'claude']", args.provider),
            executable=args.executable.resolve(),
            dedicated_home=args.native_home.resolve(),
            empty_workspace=args.empty_workspace.resolve(),
            now=utc_now,
            metadata_binding=binding,
            profile_tools={"reader": frozenset({"research_browse"})},
            native_policy_reviewed=args.native_policy_reviewed,
        )
        marker = "NATIVE-PROOF-" + uuid.uuid4().hex
        prompts = [
            f"Call research_browse exactly once with snapshot_ref={json.dumps(snapshot.id)}. "
            f"Then return this marker: {marker}. Use only the supplied metadata.",
            "Resume our previous exchange. Return the exact previous proof marker. "
            "Do not call tools.",
        ]
        results: list[RequestRecord] = []
        for index, prompt in enumerate(prompts):
            request = value(
                runtime.submit(
                    RequestSpec(
                        str(index),
                        "operator",
                        session_id,
                        0,
                        CopilotProfile(
                            "reader",
                            instructions="Only the explicitly host-granted synthetic "
                            "metadata read is permitted.",
                        ),
                        prompt,
                        provider_id,
                        model=args.model,
                        timeout_seconds=60,
                    )
                )
            )
            result = value(runtime.execute(request.request_id))
            results.append(result)
            report["requests"].append(asdict(result))
            (root / "proof-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            if result.status != "completed":
                print("Native proof stopped; see proof-result.json and authoritative journal.")
                return 1
        first, second = results
        records = value(journal.read_events())
        report["effect_receipts"] = [
            {"key": event.payload["key"], "body": json.loads(str(event.payload["body"]))}
            for event in records
            if event.event == "agent_graph.record"
            and event.payload.get("kind") == "effect"
            and json.loads(str(event.payload["body"])).get("status") == "observed"
        ]
        verified = bool(
            first.result
            and second.result
            and first.result.thread_id
            and first.result.thread_id == second.result.thread_id
            and marker in second.result.content
            and report["host_operations"] == 1
            and len(report["effect_receipts"]) == 1
        )
        report["subscription_connection_verified"] = verified
        report["acceptance"] = (
            "start + retained-ID resume + one host metadata receipt" if verified else "not verified"
        )
        (root / "proof-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"verified": verified, "report": str(root / "proof-result.json")}))
        return 0 if verified else 1
    finally:
        if journal is not None:
            journal.close()
        substrate.close()


if __name__ == "__main__":
    raise SystemExit(main())
