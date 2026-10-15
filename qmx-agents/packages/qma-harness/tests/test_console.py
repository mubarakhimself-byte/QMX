from __future__ import annotations

import asyncio
import json
import subprocess
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import pytest
import test_chat
from test_chat import FakeClient, plant_transcript, run

import qma.console
import qma.harness.harness
from qma.console import Console, Send, Slash, View, parse, usage_lines
from qma.harness import Harness, NewChat, OperatorText, QmxHome
from qma.harness.chat import RewindRefused, rewind_points
from qma.harness.home import read_record, session_id
from qma.harness.routes import control_service

home = test_chat.home

CHAT = "s1"
QUOTE: dict[str, Any] = {
    "id": "q1",
    "warning": "Switching resends 41k tokens uncached.",
    "steps": ["relaunch"],
    "recomputed_tokens": 41000,
    "background_tasks": 0,
    "old": {"profile": "claude", "model": "haiku", "effort": None, "mode": "default"},
    "new": {"profile": "openrouter", "model": "haiku", "effort": None, "mode": "default"},
}
ENTRY: dict[str, Any] = {
    "session_id": CHAT,
    "title": "check 2",
    "workspace": "D:/ws",
    "started": True,
    "turn": "idle",
    "profile": "claude",
    "model": "haiku",
    "effort": None,
    "mode": "default",
    "tokens": {},
}
DOCTOR: dict[str, Any] = {
    "lines": [
        {
            "name": "plan auth method",
            "ok": True,
            "detail": "logged in True, method claude.ai, provider firstParty, subscription max",
        }
    ]
}


class Screen:
    def __init__(self, answers: list[str] | None = None) -> None:
        self.answers = list(answers or [])
        self.lines: list[str] = []
        self.partial = ""

    def ask(self, prompt: str) -> str:
        raise AssertionError(f"a question was read with type-ahead kept: {prompt!r}")

    def decide(self, prompt: str) -> str:
        self.lines.append(prompt)
        return self.answers.pop(0)

    def out(self, text: str = "", *, end: str = "\n") -> None:
        self.partial += text + end
        *done, self.partial = self.partial.split("\n")
        self.lines += done


type Handler = Callable[[httpx.Request], Any]


def host(
    seen: list[tuple[str, str, Any]], events: list[dict[str, Any]] | None = None
) -> httpx.Client:
    """A host that answers each route the console uses and records what it was asked."""
    pending = list(events or [])

    def reply(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        path = request.url.path
        if path.endswith("/events"):
            after = int(request.url.params["after"])
            page = [event for event in pending if event["id"] > after]
            return httpx.Response(200, json=page)
        seen.append((request.method, path, body))
        routes: dict[tuple[str, str], Any] = {
            ("GET", "/api/usage"): {"readings": {}, "tokens": {}, "money": {}},
            ("POST", "/api/usage/meter"): {"readings": {}, "tokens": {}, "money": {}},
            ("GET", "/api/doctor"): DOCTOR,
            ("POST", "/api/doctor/probe"): DOCTOR,
            ("GET", f"/api/chats/{CHAT}"): ENTRY,
            ("GET", "/api/chats"): [ENTRY],
            ("POST", f"/api/sessions/{CHAT}/quote"): QUOTE,
            ("POST", f"/api/sessions/{CHAT}/apply"): QUOTE,
            ("POST", f"/api/sessions/{CHAT}/export"): {"folder": "D:/x", "files": ["chat.json"]},
            ("GET", f"/api/sessions/{CHAT}/rewind"): [{"message_id": "u1", "text": "make it"}],
            ("POST", f"/api/sessions/{CHAT}/rewind"): {"status": "rewound"},
            ("POST", f"/api/sessions/{CHAT}/interrupt"): {"status": "interrupted"},
            ("POST", f"/api/sessions/{CHAT}/turns"): {"status": "sent"},
            ("GET", "/api/settings/providers"): {
                "openrouter": {"base_url": "https://openrouter.ai/api"},
                "delegate_targets": [],
            },
            ("POST", "/api/chats"): {"session_id": CHAT},
        }
        if path.startswith("/api/approvals/"):
            return httpx.Response(200, json={"status": "resolved"})
        return httpx.Response(200, json=routes[(request.method, path)])

    return httpx.Client(base_url="http://host", transport=httpx.MockTransport(reply))


def console(
    seen: list[tuple[str, str, Any]],
    screen: Screen,
    events: list[dict[str, Any]] | None = None,
    *,
    chat: str | None = CHAT,
) -> Console:
    found = Console(host(seen, events), screen, Path("D:/qmx"), Path("D:/ws"))
    found.chat = chat
    return found


@pytest.mark.parametrize(
    ("line", "answers", "requests"),
    [
        ("/usage", [], [("GET", "/api/usage", None), ("GET", f"/api/chats/{CHAT}", None)]),
        (
            "/usage refresh",
            [],
            [("POST", "/api/usage/meter", None), ("GET", f"/api/chats/{CHAT}", None)],
        ),
        ("/doctor", [], [("GET", "/api/doctor", None)]),
        ("/doctor probe", [], [("POST", "/api/doctor/probe", None)]),
        (
            "/model sonnet",
            ["y"],
            [
                ("POST", f"/api/sessions/{CHAT}/quote", {"model": "sonnet"}),
                ("POST", f"/api/sessions/{CHAT}/apply", {"quote_id": "q1"}),
            ],
        ),
        ("/model sonnet", ["n"], [("POST", f"/api/sessions/{CHAT}/quote", {"model": "sonnet"})]),
        (
            "/provider openrouter",
            ["y"],
            [
                ("POST", f"/api/sessions/{CHAT}/quote", {"profile": "openrouter"}),
                ("POST", f"/api/sessions/{CHAT}/apply", {"quote_id": "q1"}),
            ],
        ),
        (
            "/provider",
            ["2", "y"],
            [
                ("GET", "/api/settings/providers", None),
                ("POST", f"/api/sessions/{CHAT}/quote", {"profile": "openrouter"}),
                ("POST", f"/api/sessions/{CHAT}/apply", {"quote_id": "q1"}),
            ],
        ),
        (
            "/mode plan",
            [],
            [
                ("POST", f"/api/sessions/{CHAT}/quote", {"mode": "plan"}),
                ("POST", f"/api/sessions/{CHAT}/apply", {"quote_id": "q1"}),
            ],
        ),
        (
            "/effort high",
            [],
            [
                ("POST", f"/api/sessions/{CHAT}/quote", {"effort": "high"}),
                ("POST", f"/api/sessions/{CHAT}/apply", {"quote_id": "q1"}),
            ],
        ),
        ("/resume", ["1"], [("GET", "/api/chats", None)]),
        ("/export", [], [("POST", f"/api/sessions/{CHAT}/export", None)]),
        (
            "/rewind",
            ["1"],
            [
                ("GET", f"/api/sessions/{CHAT}/rewind", None),
                ("POST", f"/api/sessions/{CHAT}/rewind", {"message_id": "u1"}),
            ],
        ),
        ("/stop", [], [("POST", f"/api/sessions/{CHAT}/interrupt", None)]),
        ("/status", [], [("GET", f"/api/chats/{CHAT}", None), ("GET", "/api/doctor", None)]),
        ("/new", [], []),
        ("/help", [], []),
    ],
)
def test_each_slash_command_maps_to_its_route(
    line: str, answers: list[str], requests: list[tuple[str, str, Any]]
) -> None:
    seen: list[tuple[str, str, Any]] = []
    screen = Screen(answers)
    assert console(seen, screen).handle(line) is True
    assert seen == requests
    assert screen.answers == []


def test_an_unknown_slash_text_is_sent_as_text() -> None:
    seen: list[tuple[str, str, Any]] = []
    assert console(seen, Screen()).handle("/compact keep the plan") is True
    assert seen[0] == ("POST", f"/api/sessions/{CHAT}/turns", {"text": "/compact keep the plan"})
    assert parse("/compact") == Send("/compact")
    assert parse("/model  sonnet") == Slash("model", "sonnet")
    assert parse("/quit") == Slash("exit", "")
    assert parse("What is in this folder?") == Send("What is in this folder?")


def test_exit_quits_and_a_first_message_starts_a_chat_in_the_folder() -> None:
    seen: list[tuple[str, str, Any]] = []
    found = console(seen, Screen(), chat=None)
    assert found.handle("/exit") is False
    found.handle("What is in this folder?")
    assert seen[0] == (
        "POST",
        "/api/chats",
        {"title": "What is in this folder?", "workspace": str(Path("D:/ws"))},
    )
    assert found.chat == CHAT


def block(event: int, seq: int, kind: str, content: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event,
        "data": {"type": "block", "block": {"seq": seq, "type": kind, "content": content}},
    }


TURN: list[dict[str, Any]] = [
    block(1, 1, "user", {"text": "What is in this folder?"}),
    block(2, 2, "tool", {"id": "t1", "name": "Bash", "arguments": {"command": "ls"}, "state": "started"}),
    block(3, 3, "tool", {"id": "t1", "state": "finished", "result": "README.md\nhello.py"}),
    block(4, 4, "tool", {"id": "t2", "name": "Read", "arguments": {"file_path": "README.md"}, "state": "started"}),
    block(5, 5, "tool", {"id": "t2", "state": "finished", "result": "# Demo\nline 2\nline 3\nline 4\nline 5"}),
    block(6, 6, "text", {"text": "Two files. The README describes a demo."}),
]  # fmt: skip


def test_a_turn_prints_each_tool_step_and_then_the_answer() -> None:
    seen: list[tuple[str, str, Any]] = []
    screen = Screen()
    console(seen, screen, TURN).handle("What is in this folder?")
    assert screen.lines == [
        "* Bash(ls)",
        "  L README.md",
        "    hello.py",
        "* Read(README.md)",
        "  L # Demo",
        "    line 2",
        "    line 3",
        "    ... +2 lines",
        "* Two files. The README describes a demo.",
    ]


def test_a_money_denial_shows_the_rule_from_the_tool_error() -> None:
    denied = "PreToolUse:Bash hook error: money rule: agents cannot place orders"
    events = [
        block(1, 1, "tool", {"id": "t1", "name": "Bash", "arguments": {"command": "curl -X POST"}, "state": "started"}),
        block(2, 2, "tool", {"id": "t1", "state": "error", "result": denied}),
    ]  # fmt: skip
    screen = Screen()
    console([], screen, events).handle("Use the terminal to place that order directly.")
    assert screen.lines == ["* Bash(curl -X POST)", f"  L Error: {denied}"]


@pytest.mark.parametrize(
    ("reply", "always", "body"),
    [
        ("y", [], {"decision": "allow_once"}),
        ("", [], {"decision": "reject", "message": "The operator said no."}),
        ("a", ["Bash(rm:*)"], {"decision": "allow_always"}),
        ("a", [], {"decision": "reject", "message": "The operator said no."}),
    ],
)
def test_an_ask_posts_the_operators_answer(
    reply: str, always: list[str], body: dict[str, Any]
) -> None:
    content: dict[str, Any] = {
        "tool": "Bash",
        "input": {"command": "rm hello.txt"},
        "state": "asking",
    }
    if always:
        content["always"] = always
    seen: list[tuple[str, str, Any]] = []
    screen = Screen([reply])
    console(seen, screen, [block(1, 7, "permission", content)]).handle("Delete hello.txt")
    assert ("POST", f"/api/approvals/{CHAT}.7", body) in seen
    assert screen.lines[0] == "? Bash wants to run: rm hello.txt"


def test_streamed_text_is_printed_once_when_its_block_lands() -> None:
    screen = Screen()
    view = View(screen)
    view.delta({"kind": "text", "text": "Hel", "tool_use_id": None})
    view.delta({"kind": "text", "text": "lo", "tool_use_id": None})
    view.delta({"kind": "thinking", "text": "hmm", "tool_use_id": None})
    view.block("text", {"text": "Hello"})
    view.block(
        "tool", {"id": "t", "name": "Read", "arguments": {"file_path": "a"}, "state": "started"}
    )
    view.block("text", {"text": "Done"})
    assert screen.lines == ["* Hello", "* Read(a)", "* Done"]


def test_a_stored_text_that_overtakes_its_deltas_is_printed_once() -> None:
    screen = Screen()
    view = View(screen)
    view.block("text", {"text": "Refused."})
    view.delta({"kind": "text", "text": "Refu", "tool_use_id": None})
    view.delta({"kind": "text", "text": "sed.", "tool_use_id": None})
    view.new_turn()
    view.delta({"kind": "text", "text": "Next", "tool_use_id": None})
    view.block("text", {"text": "Next"})
    view.line("done")
    assert screen.lines == ["* Refused.", "* Next", "done"]


def test_helper_cards_show_start_and_finish() -> None:
    screen = Screen()
    view = View(screen)
    view.block(
        "agents",
        {"tool_use_id": "a", "name": "general-purpose", "description": "count", "state": "working"},
    )
    view.block(
        "agents",
        {"task_id": "k", "tool_use_id": "a", "description": "Count files", "state": "working"},
    )
    view.block("agents", {"tool_use_id": "a", "session_id": "child"})
    view.block("agents", {"task_id": "k", "state": "completed"})
    view.block(
        "agents", {"task_id": "k", "tool_use_id": "a", "state": "completed", "summary": "7 files"}
    )
    assert screen.lines == ["  helper started: Count files", "  helper completed: 7 files"]


def test_usage_lines_name_the_window_the_tokens_and_the_cap() -> None:
    page: dict[str, Any] = {
        "readings": {
            "claude": [
                {
                    "window": "five_hour",
                    "utilization": 0.31,
                    "resets_at": "2026-10-15T18:20:00+00:00",
                    "as_of": "2026-10-15T14:02:00+00:00",
                    "source": "rate_limit_event",
                }
            ]
        },
        "tokens": {"claude": {"input_tokens": 9, "output_tokens": 2, "cache_read_tokens": 300, "cache_write_tokens": 4, "calls": 1}},
        "background_cap": 0.5,
        "background_cap_note": "Background chats stop at 50%.",
        "hard_stop": None,
        "money": {"posture": "SPEED_BUMP", "note": "no proof"},
    }  # fmt: skip
    chat = {"openrouter": {"input_tokens": 5, "output_tokens": 1, "cache_read_tokens": 0, "cache_write_tokens": 0, "calls": 2}}  # fmt: skip
    assert usage_lines(page, chat) == [
        "  Claude plan 5-hour window: 31% used, resets 2026-10-15 18:20 UTC (read 2026-10-15 14:02 UTC, rate_limit_event)",
        "  Claude plan 7-day window: no reading yet (try /usage refresh)",
        "  tokens, this chat, openrouter: in 5  out 1  cache read 0  cache write 0  (2 calls)",
        "  tokens, all chats, claude: in 9  out 2  cache read 300  cache write 4  (1 calls)",
        "  background cap 50%: Background chats stop at 50%.",
        "  money posture SPEED_BUMP: no proof",
    ]  # fmt: skip


def test_login_signs_in_with_the_bundled_cli_in_the_plan_home_and_starts_no_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qma.console.os, "environ", {"PATH": "C:/bin"})
    started: list[tuple[list[str], dict[str, str]]] = []

    class Child:
        def __init__(self, argv: list[str], env: dict[str, str]) -> None:
            started.append((argv, env))

        def wait(self) -> int:
            return 0

    monkeypatch.setattr(subprocess, "Popen", Child)
    console([], Screen()).handle("/login")
    [(argv, env)] = started
    assert Path(argv[0]).parent.name == "_bundled"
    assert argv[1:] == [
        "--settings",
        '{"forceLoginMethod": "claudeai"}',
        "auth",
        "login",
        "--claudeai",
    ]
    assert env == {"PATH": "C:/bin", "CLAUDE_CONFIG_DIR": str(Path("D:/qmx") / "claude")}


def transcript_lines(*rows: dict[str, Any]) -> str:
    return "".join(json.dumps(row) + "\n" for row in rows)


def test_rewind_points_are_prompts_with_a_file_checkpoint(tmp_path: Path) -> None:
    path = tmp_path / "chat.jsonl"
    path.write_text(
        transcript_lines(
            {"type": "user", "uuid": "u1", "message": {"content": "Make hello.txt"}},
            {"type": "file-history-snapshot", "messageId": "u1"},
            {"type": "user", "uuid": "u2", "message": {"content": [{"type": "tool_result"}]}},
            {"type": "file-history-snapshot", "messageId": "u2"},
            {"type": "user", "uuid": "u3", "isMeta": True, "message": {"content": "meta"}},
            {"type": "user", "uuid": "u4", "message": {"content": "<command-name>/effort</command-name>"}},
            {"type": "user", "uuid": "u5", "message": {"content": [{"type": "text", "text": "Now goodbye"}]}},
            {"type": "file-history-snapshot", "messageId": "u5"},
            {"type": "user", "uuid": "u6", "message": {"content": "no checkpoint"}},
        ),
        encoding="utf-8",
    )  # fmt: skip
    assert [(point.message_id, point.text) for point in rewind_points(path)] == [
        ("u1", "Make hello.txt"),
        ("u5", "Now goodbye"),
    ]
    assert rewind_points(None) == []


async def started_chat(harness: Harness) -> str:
    chat = await harness.start_chat(NewChat(title="rewind", model="haiku"))
    await harness.send(chat, OperatorText("go"))
    FakeClient.made[-1].go.set()
    for _ in range(500):
        record = read_record(harness.home, session_id(chat))
        if record is not None and record.turn == "idle" and record.started:
            return chat
        await asyncio.sleep(0.01)
    raise AssertionError("the turn never ended")


def test_rewind_calls_the_sdk_file_rewind_only_for_a_checkpointed_prompt_while_idle(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    rewound: list[str] = []

    async def rewind_files(_: FakeClient, message_id: str) -> None:
        rewound.append(message_id)

    monkeypatch.setattr(FakeClient, "rewind_files", rewind_files, raising=False)

    async def body(harness: Harness) -> None:
        chat = session_id(await started_chat(harness))
        plant_transcript(home, chat).write_text(
            transcript_lines(
                {"type": "user", "uuid": "u1", "message": {"content": "go"}},
                {"type": "file-history-snapshot", "messageId": "u1"},
            ),
            encoding="utf-8",
        )
        with pytest.raises(RewindRefused, match="no file checkpoint"):
            await harness.rewind(chat, "u9")
        live = harness._chats[chat]  # pyright: ignore[reportPrivateUsage]
        idle = live.record
        live.record = replace(idle, turn="running")
        with pytest.raises(RewindRefused, match="a turn is running"):
            await harness.rewind(chat, "u1")
        live.record = idle
        await harness.rewind(chat, "u1")
        assert rewound == ["u1"]
        assert [p.message_id for p in await harness.rewind_points(chat)] == ["u1"]

    run(body, home)


CANARY_REF = "qmx/hp15-canary"


def test_export_bundles_the_chat_with_claude_tokens_and_provider_keys_redacted(
    home: QmxHome, monkeypatch: pytest.MonkeyPatch
) -> None:
    key_value = "qmx-canary-provider-" + "k" * 24
    claude_value = "sk-ant-" + "oat01-" + "Q" * 40
    monkeypatch.setattr(qma.harness.harness, "keyring_secret", lambda _ref: key_value)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
    row = test_chat.ROUTER_ROW | {"credential_ref": CANARY_REF}
    control_service(home).settings_put("providers", {"canary": row})
    found: dict[str, str] = {}

    async def body(harness: Harness) -> None:
        chat = session_id(await started_chat(harness))
        path = plant_transcript(home, chat)
        path.write_text(
            transcript_lines(
                {"type": "user", "message": {"content": f"{claude_value} {key_value}"}}
            ),
            encoding="utf-8",
        )
        helper = path.with_suffix("") / "subagents" / "agent-a1.jsonl"
        helper.parent.mkdir(parents=True)
        helper.write_text(f"{key_value}\n", encoding="utf-8")
        folder = await harness.export(chat)
        found.update(
            {
                file.relative_to(folder).as_posix(): file.read_text(encoding="utf-8")
                for file in folder.rglob("*.*")
            }
        )

    run(body, home)
    assert sorted(found) == [
        "approvals.jsonl",
        "chat.json",
        "subagents/agent-a1.jsonl",
        "transcript.jsonl",
    ]
    assert json.loads(found["transcript.jsonl"])["message"]["content"] == (
        f"[redacted sk-ant token] [redacted {CANARY_REF}]"
    )
    assert found["subagents/agent-a1.jsonl"] == f"[redacted {CANARY_REF}]\n"
    assert all(key_value not in text and "sk-ant-oat01" not in text for text in found.values())
