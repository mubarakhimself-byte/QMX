"""Operator-door proof without credentials, network traffic or native execution."""

from __future__ import annotations

import json
import signal
import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest
from qma.daemon.journal.authoritative import AuthoritativeJournal, JournalAppendReceipt
from qma.daemon.request_runtime import __main__ as cli
from qma.daemon.request_runtime.contracts import (
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestRecord,
)
from qma.daemon.request_runtime.providers import ProviderCancelled
from qma.daemon.request_runtime.service import RequestRuntime
from qmf.core import Instant, Result


def output(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return cast("dict[str, object]", json.loads(captured.out))


class NativeSpy:
    capabilities = ProviderCapabilities("codex-native")

    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        self.requests.append(request)
        return ProviderResult("offline native spy", deployment_id="test")


def test_native_alias_uses_canonical_provider_and_empty_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spy = NativeSpy()
    constructed: list[tuple[Path, Path]] = []
    executable = tmp_path / "never-executed.exe"
    home = tmp_path / "dedicated-home"

    def make_native(*, executable: Path, codex_home: Path) -> NativeSpy:
        constructed.append((executable, codex_home))
        return spy

    monkeypatch.setattr(cli, "CodexAppServerProvider", make_native)
    assert (
        cli.main(
            [
                "--root",
                str(tmp_path / "state"),
                "--provider",
                "codex",
                "--allow-live",
                "--codex-executable",
                str(executable),
                "--codex-home",
                str(home),
                "run",
                "--prompt",
                "hello",
                "--key",
                "native-key",
            ]
        )
        == 0
    )
    row = output(capsys)
    assert cast("dict[str, object]", row["spec"])["provider_id"] == "codex-native"
    assert row["status"] == "completed"
    assert constructed == [(executable, home)]
    assert len(spy.requests) == 1
    assert spy.requests[0].cwd == ""
    assert spy.requests[0].thread_id is None
    assert not executable.exists()
    assert not home.exists()


@pytest.mark.parametrize("missing", ["consent", "executable", "home"])
def test_native_gating_prevents_construction_and_state_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    def forbidden_native(**kwargs: object) -> NativeSpy:
        pytest.fail("native provider must not be constructed before explicit configuration")

    monkeypatch.setattr(cli, "CodexAppServerProvider", forbidden_native)
    root = tmp_path / "unopened-state"
    args = ["--root", str(root), "--provider", "codex"]
    if missing != "consent":
        args.append("--allow-live")
    if missing != "executable":
        args += ["--codex-executable", str(tmp_path / "codex.exe")]
    if missing != "home":
        args += ["--codex-home", str(tmp_path / "dedicated-home")]
    args += ["run", "--prompt", "hello", "--key", "must-not-run"]
    with pytest.raises(SystemExit) as exit_info:
        cli.main(args)
    assert exit_info.value.code == 2
    assert not root.exists()


def test_diagnostic_exact_key_replays_and_fresh_show_reads_durable_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = ["--root", str(tmp_path / "state"), "run", "--prompt", "persist me", "--key", "stable"]
    assert cli.main(args) == 0
    original = output(capsys)
    request_id = original["request_id"]
    assert isinstance(request_id, str)
    assert original["status"] == "completed"
    assert cast("dict[str, object]", original["result"])["content"] == "DIAGNOSTIC ONLY: persist me"

    def forbidden_reexecution(
        self: cli.DiagnosticProvider,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        pytest.fail("exact-key replay must use the durable result without a provider call")

    monkeypatch.setattr(cli.DiagnosticProvider, "execute", forbidden_reexecution)
    # Each main invocation opens a fresh substrate, session service and runtime.
    assert cli.main(args) == 0
    assert output(capsys) == original
    assert cli.main(["--root", str(tmp_path / "state"), "show", request_id]) == 0
    assert output(capsys) == original
    assert (
        cli.main(
            [
                "--root",
                str(tmp_path / "state"),
                "run",
                "--prompt",
                "different",
                "--key",
                "stable",
            ]
        )
        == 1
    )
    failed = capsys.readouterr()
    assert failed.out == ""
    assert "idempotency_key" in failed.err


def test_interrupt_handler_defers_durable_cancel_to_coordinator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handlers: dict[int, object] = {int(signal.SIGINT): signal.SIG_DFL}
    cancel_threads: list[threading.Thread] = []
    signalled = False
    original_append = AuthoritativeJournal.append_event
    original_cancel = RequestRuntime.cancel

    def fake_signal(signum: int, handler: object) -> object:
        previous = handlers.get(signum)
        handlers[signum] = handler
        return previous

    def fake_getsignal(signum: int) -> object:
        return handlers[signum]

    def recorded_cancel(self: RequestRuntime, request_id: str) -> Result[RequestRecord]:
        current = threading.current_thread()
        # Synchronous cancellation here could re-enter an interrupted journal
        # append. The handler must return before a separate thread mutates state.
        assert current is not threading.main_thread()
        cancel_threads.append(current)
        return original_cancel(self, request_id)

    def interrupted_append(
        self: AuthoritativeJournal,
        event: object,
        *,
        scope_path: object = (),
        payload: Mapping[str, object] | None = None,
        occurred_at: Instant | int | None = None,
        worker_authored_timestamp: object = None,
    ) -> Result[JournalAppendReceipt]:
        nonlocal signalled
        if event == "agent_request.snapshot" and payload and payload.get("status") == "running":
            handler = cast("Callable[[int, object], None]", handlers[int(signal.SIGINT)])
            handler(int(signal.SIGINT), None)
            signalled = True
        return original_append(
            self,
            event,
            scope_path=scope_path,
            payload=payload,
            occurred_at=occurred_at,
            worker_authored_timestamp=worker_authored_timestamp,
        )

    def cancellable_diagnostic(
        self: cli.DiagnosticProvider,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        assert cancellation.wait(3), "interrupt coordinator did not deliver cancellation"
        raise ProviderCancelled()

    monkeypatch.setattr(cli.signal, "signal", fake_signal)
    monkeypatch.setattr(cli.signal, "getsignal", fake_getsignal)
    monkeypatch.setattr(AuthoritativeJournal, "append_event", interrupted_append)
    monkeypatch.setattr(RequestRuntime, "cancel", recorded_cancel)
    monkeypatch.setattr(cli.DiagnosticProvider, "execute", cancellable_diagnostic)
    assert (
        cli.main(
            [
                "--root",
                str(tmp_path / "state"),
                "run",
                "--prompt",
                "interrupt me",
                "--key",
                "cancel-key",
            ]
        )
        == 0
    )
    assert output(capsys)["status"] == "cancelled"
    assert signalled
    assert len(cancel_threads) == 1
    assert handlers[int(signal.SIGINT)] == signal.SIG_DFL
