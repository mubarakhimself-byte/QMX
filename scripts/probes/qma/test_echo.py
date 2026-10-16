# ruff: noqa: S101, S310
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from p_echo import (
    CANARY,
    FAKE_KEY,
    Request,
    ToolCall,
    canary_home,
    serve,
    with_token_verdict,
    without_token_verdict,
)


def post(url: str, headers: dict[str, str], body: dict[str, object]) -> bytes:
    request = urllib.request.Request(
        f"{url}/v1/messages?beta=true",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"} | headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as reply:
        return reply.read()


def test_echo_records_which_credential_arrived_without_keeping_its_value() -> None:
    with serve() as (url, echo):
        streamed = post(
            url, {"Authorization": f"Bearer {FAKE_KEY}"}, {"model": "m1", "stream": True}
        )
        post(url, {"x-api-key": "some-real-looking-key"}, {"model": "m1"})
        post(url, {"Authorization": f"Bearer {CANARY}"}, {"model": "m1"})
        post(url, {}, {"model": "m1", "messages": [{"role": "user", "content": CANARY}]})
    assert echo.requests == [
        Request("POST", "/v1/messages?beta=true", {"authorization": "fake-key"}, False),
        Request("POST", "/v1/messages?beta=true", {"x-api-key": "other"}, False),
        Request("POST", "/v1/messages?beta=true", {"authorization": "canary"}, True),
        Request("POST", "/v1/messages?beta=true", {}, True),
    ]
    events = [
        json.loads(line.removeprefix(b"data: "))["type"]
        for line in streamed.splitlines()
        if line.startswith(b"data: ")
    ]
    assert events == [
        "message_start",
        "content_block_start",
        "content_block_delta",
        "content_block_stop",
        "message_delta",
        "message_stop",
    ]


def test_with_token_passes_only_when_every_credential_is_the_fake_key() -> None:
    fake = Request("POST", "/v1/messages", {"authorization": "fake-key"}, False)
    canary = Request("POST", "/v1/messages", {"authorization": "canary"}, True)
    unknown = Request("POST", "/v1/messages", {"x-api-key": "other"}, False)
    assert with_token_verdict([fake, fake]) == "PASS"
    assert with_token_verdict([fake, canary]) == "FAIL"
    assert with_token_verdict([fake, unknown]) == "FAIL"
    assert with_token_verdict([]) == "FAIL"


def test_without_token_says_leak_no_leak_or_that_no_model_request_came() -> None:
    hello = Request("HEAD", "/api/hello", {}, False)
    model = Request("POST", "/v1/messages?beta=true", {}, False)
    canary = Request("POST", "/v1/messages?beta=true", {"authorization": "canary"}, True)
    assert without_token_verdict([hello, canary]) == "LEAK"
    assert without_token_verdict([hello, model]) == "NO LEAK"
    assert without_token_verdict([hello]) == "NO MODEL REQUEST"


def test_canary_home_holds_only_the_canary_login(tmp_path: Path) -> None:
    root = tmp_path / "claude"
    root.mkdir()
    (root / "stale.json").write_text("{}", encoding="utf-8")
    canary_home(root)
    assert sorted(p.name for p in root.iterdir()) == [".credentials.json"]
    login = json.loads((root / ".credentials.json").read_text(encoding="utf-8"))
    assert login["claudeAiOauth"]["accessToken"] == "sk-ant-oat01-QMXCANARY"


def test_echo_answers_its_scripted_tool_calls_to_requests_that_offer_tools_then_ok() -> None:
    call = ToolCall("Bash", {"command": "echo hp1"})
    with serve([call]) as (url, echo):
        side = post(url, {}, {"model": "m1", "stream": True})
        first = post(url, {}, {"model": "m1", "stream": True, "tools": [{"name": "Bash"}]})
        second = post(url, {}, {"model": "m1", "stream": True, "tools": [{"name": "Bash"}]})
    assert [deltas(reply) for reply in (side, first, second)] == [
        ["text_delta ok"],
        ['input_json_delta {"command": "echo hp1"}'],
        ["text_delta ok"],
    ]
    assert len(echo.bodies) == 3


def deltas(reply: bytes) -> list[str]:
    events = [
        json.loads(line.removeprefix(b"data: "))
        for line in reply.splitlines()
        if line.startswith(b"data: ")
    ]
    return [
        f"{d['type']} {d.get('text', d.get('partial_json'))}"
        for e in events
        if e["type"] == "content_block_delta"
        for d in [e["delta"]]
    ]
