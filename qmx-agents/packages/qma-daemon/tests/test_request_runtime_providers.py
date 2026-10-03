"""Offline process protocol tests, not native entitlement or live inference proof."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest
from qma.daemon.request_runtime.contracts import ProviderEvent, ProviderRequest
from qma.daemon.request_runtime.providers import (
    CodexAppServerProvider,
    ProviderCancelled,
    ProviderError,
)

_SERVER = """
import json, sys, time
mode = sys.argv[1]
features = {}
for i, arg in enumerate(sys.argv):
    if arg == '-c' and sys.argv[i+1].startswith('features.'):
        features[sys.argv[i+1].split('=')[0].split('.')[1]] = sys.argv[i+1].split('=')[1] == 'true'
def send(obj):
    print(json.dumps(obj), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    method, rid = request.get('method'), request.get('id')
    params = request.get('params', {})
    if method == 'initialize':
        if mode == 'malformed':
            print('not-json', flush=True)
            continue
        if mode == 'eof':
            sys.exit(0)
        if mode == 'startup_timeout':
            time.sleep(10)
            continue
        send({'id':rid,'result':{}})
    elif method == 'initialized':
        continue
    elif method == 'config/read':
        config = {'features': features, 'tools':{'view_image':False},
                  'web_search':'disabled', 'mcp_servers':{}}
        if mode == 'unsafe': config['mcp_servers']={'evil':{'command':'danger'}}
        send({'id':rid,'result':{'config':config}})
    elif method == 'account/read':
        account = None if mode == 'noauth' else {'type':'chatgpt'}
        send({'id':rid,'result':{'account':account}})
    elif method == 'thread/start':
        assert params['sandbox'] == 'read-only'
        assert params['approvalPolicy'] == 'untrusted'
        send({'id':rid,'result':{'thread':{'id':'thread-test'}}})
    elif method == 'turn/start':
        assert params['sandboxPolicy'] == {'type':'readOnly'}
        if mode == 'lost_ack': sys.exit(0)
        send({'id':rid,'result':{'turn':{'id':'turn-test'}}})
        if mode in ('cancel', 'unknown'): continue
        if mode == 'tool':
            send({'id':900,'method':'item/commandExecution/requestApproval','params':{}})
            continue
        if mode == 'violation':
            send({'method':'item/started','params':{'threadId':'thread-test','item':{'type':'commandExecution'}}})
            continue
        send({'method':'item/agentMessage/delta','params':{'threadId':'thread-test','delta':'partial'}})
        send({'method':'item/completed','params':{'threadId':'thread-test','item':{'id':'answer','type':'agentMessage','text':'complete'}}})
        terminal = {'id':'turn-test','status':'failed' if mode == 'failed' else 'completed'}
        send({'method':'turn/completed','params':{'threadId':'thread-test','turn':terminal}})
    elif rid == 900:
        assert request['result']['decision'] == 'decline'
        send({'method':'item/completed','params':{'item':{'id':'answer','type':'agentMessage','text':'denied'}}})
        send({'method':'turn/completed','params':{'turn':{'id':'turn-test','status':'completed'}}})
    elif method == 'turn/interrupt':
        if mode == 'unknown': continue
        send({'id':rid,'result':{}})
        send({'method':'turn/completed','params':{'turn':{'id':'turn-test','status':'interrupted'}}})
"""


def provider(tmp_path: Path, mode: str) -> CodexAppServerProvider:
    server = tmp_path / "fake_server.py"
    server.write_text(_SERVER, encoding="utf-8")
    home = tmp_path / "native-home"
    home.mkdir()
    return CodexAppServerProvider([sys.executable, str(server), mode], str(home))


def test_real_local_stdio_process_success(tmp_path: Path) -> None:
    adapter = provider(tmp_path, "success")
    events: list[ProviderEvent] = []
    result = adapter.execute(ProviderRequest("hello"), events.append, threading.Event())
    assert result.content == "complete"
    assert result.thread_id == "thread-test"
    assert result.turn_id == "turn-test"
    assert not adapter.capabilities.native_tools
    assert not adapter.capabilities.resume
    assert [event.name for event in events] == ["thread_started", "turn_started", "text_delta"]


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("malformed", "protocol_error"),
        ("eof", "protocol_eof"),
        ("unsafe", "unsafe_config"),
        ("noauth", "auth_required"),
        ("failed", "native_failed"),
        ("lost_ack", "outcome_unknown"),
        ("startup_timeout", "timeout"),
        ("violation", "outcome_unknown"),
    ],
)
def test_failures_are_classified(tmp_path: Path, mode: str, code: str) -> None:
    adapter = provider(tmp_path, mode)
    with pytest.raises(ProviderError) as error:
        adapter.execute(
            ProviderRequest("hello", timeout_seconds=0.3), lambda _: None, threading.Event()
        )
    assert error.value.code == code


def test_server_approval_is_declined(tmp_path: Path) -> None:
    adapter = provider(tmp_path, "tool")
    events: list[ProviderEvent] = []
    result = adapter.execute(ProviderRequest("hello"), events.append, threading.Event())
    assert result.content == "denied"
    assert any(event.name == "tool_denied" for event in events)


def test_cancellation_requires_terminal_ack(tmp_path: Path) -> None:
    adapter = provider(tmp_path, "cancel")
    cancellation = threading.Event()

    def emit(event: ProviderEvent) -> None:
        if event.name == "turn_started":
            cancellation.set()

    with pytest.raises(ProviderCancelled):
        adapter.execute(ProviderRequest("hello"), emit, cancellation)


def test_unacknowledged_cancel_is_unknown(tmp_path: Path) -> None:
    adapter = provider(tmp_path, "unknown")
    cancellation = threading.Event()

    def emit(event: ProviderEvent) -> None:
        if event.name == "turn_started":
            cancellation.set()

    with pytest.raises(ProviderError) as error:
        adapter.execute(ProviderRequest("hello"), emit, cancellation)
    assert error.value.code == "outcome_unknown"


def test_inherited_config_and_resume_are_refused(tmp_path: Path) -> None:
    adapter = provider(tmp_path, "success")
    for request in (ProviderRequest("x", thread_id="old"), ProviderRequest("x", cwd=str(tmp_path))):
        with pytest.raises(ProviderError, match="fresh"):
            adapter.execute(request, lambda _: None, threading.Event())
    (adapter.codex_home / "config.toml").write_text("mcp_servers = {}", encoding="utf-8")
    with pytest.raises(ProviderError, match="config"):
        adapter.execute(ProviderRequest("hello"), lambda _: None, threading.Event())


def test_native_environment_does_not_inherit_api_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-travel")
    # The fake script asserts its actual subprocess environment before protocol.
    adapter = provider(tmp_path, "success")
    server = tmp_path / "fake_server.py"
    server.write_text(
        "import os\nassert 'OPENAI_API_KEY' not in os.environ\n" + _SERVER, encoding="utf-8"
    )
    assert (
        adapter.execute(ProviderRequest("hello"), lambda _: None, threading.Event()).content
        == "complete"
    )
