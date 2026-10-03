"""Local operator door for the bounded SDK request runtime.

No listener, credential reader or automatic paid fallback is opened here.
"""

from __future__ import annotations

import argparse
import json
import signal
import socket
import sys
import threading
import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.sessions.product_session import ProductSessionService
from qmf.core import is_refusal

from .contracts import (
    CopilotProfile,
    ProviderAdapter,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestSpec,
)
from .providers import CodexAppServerProvider
from .service import RequestRuntime


class DiagnosticProvider:
    """Explicit deterministic diagnostic; never claims to be a model call."""

    capabilities = ProviderCapabilities(provider_id="diagnostic")

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        emit(ProviderEvent("diagnostic.executed", {"live_provider": False}))
        if cancellation.is_set():
            raise RuntimeError("cancelled")
        return ProviderResult(
            content=f"DIAGNOSTIC ONLY: {request.prompt}", deployment_id="diagnostic"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="isolated local state directory")
    parser.add_argument("--session", default="psess:sdk-local")
    parser.add_argument("--provider", choices=("diagnostic", "codex"), default="diagnostic")
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument(
        "--allow-live", action="store_true", help="explicit subscription test consent"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--prompt", required=True)
    run.add_argument("--key", required=True)
    run.add_argument("--model")
    run.add_argument("--timeout", type=float, default=120)
    for name in ("show", "cancel", "retry"):
        command = sub.add_parser(name)
        command.add_argument("request_id")
    args = parser.parse_args(argv)

    providers: dict[str, ProviderAdapter] = {"diagnostic": DiagnosticProvider()}
    if args.provider == "codex":
        if not args.allow_live or not args.codex_executable or not args.codex_home:
            parser.error(
                "codex requires --allow-live, --codex-executable and dedicated --codex-home"
            )
        providers["codex-native"] = CodexAppServerProvider(
            executable=args.codex_executable, codex_home=args.codex_home
        )

    state_root = args.root.resolve()
    workspace = state_root / "provider-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    boot = str(uuid.uuid4())
    opened = PersistenceSubstrate.open(state_root, machine=socket.gethostname(), boot_epoch_id=boot)
    if is_refusal(opened):
        print(repr(opened), file=sys.stderr)
        return 1
    substrate = opened.value
    journal: AuthoritativeJournal | None = None
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
        runtime = RequestRuntime(
            journal=journal,
            product_sessions=sessions,
            providers=providers,
            provider_workspace="",
        )
        if args.command == "run":
            session = sessions.get(args.session)
            if is_refusal(session):
                session = sessions.mint(
                    product_session_id=args.session,
                    profile="authoring",
                    principal="operator",
                    contribution={"qualified_id": "qma.sdk.local", "package_version": "0.1.0"},
                    instance_id=None,
                    config_revision=0,
                    as_of=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    granted_ops=(),
                    selected_refs=(),
                    scope_path=(),
                )
            if is_refusal(session):
                print(repr(session), file=sys.stderr)
                return 1
            submitted = runtime.submit(
                RequestSpec(
                    idempotency_key=args.key,
                    principal="operator",
                    product_session_id=args.session,
                    context_revision=session.value.context_revision,
                    profile=CopilotProfile("global-default"),
                    prompt=args.prompt,
                    provider_id="codex-native" if args.provider == "codex" else args.provider,
                    model=args.model,
                    timeout_seconds=args.timeout,
                )
            )
            if is_refusal(submitted):
                result = submitted
            else:
                request_id = submitted.value.request_id
                previous_handler = None
                cancel_pending = [False]
                stop_coordinator = threading.Event()

                def request_cancel(_signum: int, _frame: object) -> None:
                    # Signal handlers must not re-enter the journal append lock.
                    cancel_pending[0] = True

                def coordinate_cancel() -> None:
                    while not stop_coordinator.wait(0.05):
                        if cancel_pending[0]:
                            runtime.cancel(request_id)
                            cancel_pending[0] = False

                coordinator: threading.Thread | None = None
                if threading.current_thread() is threading.main_thread():
                    previous_handler = signal.getsignal(signal.SIGINT)
                    signal.signal(signal.SIGINT, request_cancel)
                    coordinator = threading.Thread(target=coordinate_cancel, daemon=True)
                    coordinator.start()
                try:
                    result = runtime.execute(request_id)
                finally:
                    stop_coordinator.set()
                    if coordinator is not None:
                        coordinator.join()
                    if previous_handler is not None:
                        signal.signal(signal.SIGINT, previous_handler)
        elif args.command == "show":
            result = runtime.get(args.request_id)
        elif args.command == "cancel":
            result = runtime.cancel(args.request_id)
        else:
            result = runtime.retry_interrupted(args.request_id)
        if is_refusal(result):
            print(repr(result), file=sys.stderr)
            return 1
        print(json.dumps(asdict(result.value), ensure_ascii=False))
        return 0 if result.value.status in {"completed", "cancelled", "queued"} else 1
    finally:
        if journal is not None:
            journal.close()
        substrate.close()


if __name__ == "__main__":
    raise SystemExit(main())
