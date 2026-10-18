from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from qma.gpt import translate
from qma.gpt.probe import (
    PROBE_FILE,
    ProbeFailed,
    ProbePassed,
    ProbeRun,
    read_cli_stream,
    run_probe,
    stored_result,
    translator_version,
)
from qma.gpt.siwc import Record, SiwcSession

AT = datetime(2026, 10, 15, 18, 0, tzinfo=UTC)


def test_probe_passed_refuses_construction_outside_probe_py() -> None:
    with pytest.raises(TypeError) as refused:
        ProbePassed(AT, translator_version(), "gpt-6.1-sol")
    assert str(refused.value) == "a ProbePassed is built only by qma.gpt.probe"


def test_probe_run_refuses_construction_outside_probe_py() -> None:
    with pytest.raises(TypeError) as refused:
        ProbeRun("run-1")
    assert str(refused.value) == "a ProbeRun is minted only by qma.gpt.probe.run_probe"


def test_the_version_is_the_hash_of_translate_py_read_at_each_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy = tmp_path / "translate.py"
    copy.write_bytes(b"x")
    monkeypatch.setattr(translate, "__file__", str(copy))
    assert translator_version() == "2d711642b726b044"
    copy.write_bytes(b"xy")
    assert translator_version() == "769a4e6d0003189c"
    copy.write_bytes(b"a\r\nb\r\n")
    crlf = translator_version()
    copy.write_bytes(b"a\nb\n")
    assert translator_version() == crlf


def write(state: Path, **document: object) -> None:
    state.mkdir(parents=True, exist_ok=True)
    (state / PROBE_FILE).write_text(json.dumps(document), encoding="utf-8")


def test_a_stored_pass_reads_back_for_its_own_translator_version_only(tmp_path: Path) -> None:
    version = translator_version()
    write(
        tmp_path,
        at=AT.isoformat(),
        outcome="passed",
        translator_version=version,
        model="gpt-6.1-sol",
    )
    found = stored_result(tmp_path, version)
    assert isinstance(found, ProbePassed)
    assert (found.at, found.translator_version, found.model) == (AT, version, "gpt-6.1-sol")
    assert stored_result(tmp_path, "0000000000000000") is None


def test_a_stored_failure_and_a_missing_or_broken_file(tmp_path: Path) -> None:
    assert stored_result(tmp_path, "v1") is None
    write(
        tmp_path,
        at=AT.isoformat(),
        outcome="failed",
        translator_version="v1",
        step="P6",
        detail="no Bash",
    )
    assert stored_result(tmp_path, "v1") == ProbeFailed(AT, "P6", "no Bash")
    (tmp_path / PROBE_FILE).write_text("{", encoding="utf-8")
    assert stored_result(tmp_path, "v1") is None


CLI_LINES = [
    json.dumps({"type": "system", "subtype": "init", "tools": ["Bash"]}),
    json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "c1",
                        "name": "Bash",
                        "input": {"command": "echo hello"},
                    }
                ]
            },
        }
    ),
    json.dumps(
        {
            "type": "user",
            "message": {
                "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "hello"}]
            },
        }
    ),
    "not json",
    json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done"}),
]


def test_the_cli_stream_verdict() -> None:
    turn = read_cli_stream(CLI_LINES)
    assert (turn.bash_calls, turn.hello_seen, turn.ok, turn.detail) == (1, True, True, "done")


def test_an_error_result_fails_the_cli_verdict() -> None:
    error = json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True})
    turn = read_cli_stream([*CLI_LINES[:3], error])
    assert (turn.ok, turn.detail) == (False, "error_during_execution")


class MemoryVault:
    def __init__(self) -> None:
        self.value: str | None = None

    def get(self) -> str | None:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class NoDoor:
    opened = 0

    async def open(self, run: ProbeRun) -> Mapping[str, str]:
        self.opened += 1
        return {}

    async def close(self, run: ProbeRun) -> None:
        return None


def openai(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/oauth/token"):
        return httpx.Response(200, json={"access_token": "access-1", "expires_in": 3600})
    return httpx.Response(200, json={"models": [{"slug": "gpt-6-luna", "visibility": "list"}]})


def session(scopes: tuple[str, ...]) -> SiwcSession:
    record = Record("oaiapp_1", "urn:uuid:1", "refresh-1", scopes)
    return SiwcSession(record, MemoryVault(), transport=httpx.MockTransport(openai))


@pytest.mark.parametrize(
    ("scopes", "failed"),
    [
        (("openid",), ProbeFailed(AT, "P0", "the stored grant lacks chatgpt.tokens.use.direct")),
        (
            ("chatgpt.tokens.use.direct",),
            ProbeFailed(AT, "P1", "gpt-6.1-sol is not among the listed models ['gpt-6-luna']"),
        ),
    ],
)
def test_a_failed_step_is_stored_and_never_opens_the_door(
    tmp_path: Path, scopes: tuple[str, ...], failed: ProbeFailed
) -> None:
    door, said = NoDoor(), list[str]()
    result = asyncio.run(
        run_probe(
            session(scopes),
            door,
            model="gpt-6.1-sol",
            state_dir=tmp_path,
            workspace=tmp_path / "w",
            say=said.append,
        )
    )
    assert isinstance(result, ProbeFailed)
    assert (result.step, result.detail) == (failed.step, failed.detail)
    assert door.opened == 0
    assert said == [*said[:-1], f"{failed.step} FAIL {failed.detail}"]
    stored = stored_result(tmp_path, translator_version())
    assert isinstance(stored, ProbeFailed)
    assert (stored.step, stored.detail) == (failed.step, failed.detail)
