"""Temporary console (deleted when the UI lands, R11). `python -m qma.console`.

It uses only the HTTP routes in `qma.harness.routes` and the existing SSE streams, the same
doors the UI will use, so talking to it tests the real path. It never imports `qma.harness` or
`claude_agent_sdk`. It scrubs its own environment first, because `/login` starts the bundled
CLI from this process. With no host answering on `--port`, it starts `qma.serve` for `--home`
and stops it again on exit.

Commands, mirroring Claude Code where a twin exists:
    /login chatgpt         Sign in with ChatGPT for QMA: the stored sign-in, or OpenAI's page
                           after a y/N, then the GPT probe unless a pass is stored, then a
                           y/N on letting Background and helper chats use the ChatGPT plan.
    /login                 runs the bundled CLI's own `auth login --claudeai` in this terminal,
                           with CLAUDE_CONFIG_DIR set to QMX's plan home and
                           `--settings '{"forceLoginMethod": "claudeai"}'`, so the Console
                           (API billing) choice is not offered. It signs in and exits, so no
                           Claude Code session outlives it. QMA never sees the token.
    /model <alias|id>      quote, show the cache warning, ask y/N, apply.
    /provider [name]       same flow for a provider switch; with no name, pick from a list.
    /mode <mode>           permission mode; applies at once.
    /effort <level>        quote and apply (a relaunch with resume).
    /usage  /doctor        read-only pages. `/usage refresh` reads the plan meter first,
                           `/doctor probe` runs the exposure probe.
    /status /resume /new /export /rewind /stop /help /exit
Anything else, including any other text starting with "/", is sent as text, so CLI built-ins
such as /compact and /context and QMX plugin commands work as they do in Claude Code.
Ctrl+C ends the running turn; at the prompt, Ctrl+C twice quits. An ask prints the tool, its
input and the choices (allow once, allow always, reject) and posts the answer.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import queue
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Protocol, cast

import httpx
import keyring

from qma.boot import read_keep_names, scrub_process_env

BEARER_ENTRY: Final = "qmx/control-token"
BEARER_USER: Final = "control-token"
PROMPT: Final = "> "
STATE_POLL_S: Final = 0.25
EVENT_POLL_S: Final = 0.1
FORCE_CLAUDEAI: Final = json.dumps({"forceLoginMethod": "claudeai"})


class Terminal(Protocol):
    def ask(self, prompt: str) -> str:
        """The next line, typed-ahead text included, as at Claude Code's prompt."""
        ...

    def decide(self, prompt: str) -> str:
        """A fresh answer to a question this console just asked: keys typed before the
        question existed never answer it."""
        ...

    def out(self, text: str = "", *, end: str = "\n") -> None: ...


def flush_typed_ahead() -> None:
    if not sys.stdin.isatty():
        return
    if sys.platform == "win32":
        import ctypes  # noqa: PLC0415

        kernel32 = ctypes.windll.kernel32
        kernel32.FlushConsoleInputBuffer(kernel32.GetStdHandle(-10))
    else:
        import termios  # noqa: PLC0415

        termios.tcflush(sys.stdin, termios.TCIFLUSH)


class StdTerminal:
    def ask(self, prompt: str) -> str:
        return input(prompt)

    def decide(self, prompt: str) -> str:
        flush_typed_ahead()
        return input(prompt)

    def out(self, text: str = "", *, end: str = "\n") -> None:
        sys.stdout.write(text + end)
        sys.stdout.flush()


DIM: Final = "\x1b[2m"
BOLD: Final = "\x1b[1m"
RED: Final = "\x1b[31m"
RESET: Final = "\x1b[0m"


@dataclass(frozen=True)
class Send:
    text: str


@dataclass(frozen=True)
class Slash:
    name: str
    arg: str


type Command = Send | Slash

HELP: Final[dict[str, str]] = {
    "login": "sign in to your Claude plan (claude.ai only); /login chatgpt for GPT",
    "status": "this chat, its model and the plan sign-in",
    "model": "/model <alias or id>: switch model, after a warning",
    "provider": "/provider [name]: switch provider, after a warning",
    "mode": "/mode <default|acceptEdits|plan|bypassPermissions>",
    "effort": "/effort <low|medium|high|xhigh|max>",
    "usage": "plan windows, tokens, background cap; /usage refresh reads the plan meter",
    "doctor": "setup checks; /doctor probe also runs the exposure probe",
    "resume": "pick an earlier chat",
    "new": "start a new chat on the next message",
    "export": "write this chat's redacted transcript, asks and usage to a folder",
    "rewind": "put files back as they were before one of your messages",
    "stop": "interrupt the running turn",
    "help": "this list",
    "exit": "quit (also /quit, or Ctrl+C twice)",
}
ALIASES: Final = {"quit": "exit"}


def parse(line: str) -> Command:
    """A known `/name` is a console command; every other line, slash or not, is chat text."""
    if line.startswith("/"):
        name, _, arg = line[1:].partition(" ")
        name = ALIASES.get(name, name)
        if name in HELP:
            return Slash(name, arg.strip())
    return Send(line)


def tool_label(name: str) -> str:
    if name.startswith("mcp__"):
        _, server, tool = name.split("__", 2)
        return f"{server}:{tool}"
    return name


SUMMARY_KEYS: Final = (
    "command",
    "file_path",
    "notebook_path",
    "pattern",
    "path",
    "url",
    "query",
    "description",
    "prompt",
)


def one_line(text: str, width: int = 100) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 3] + "..."


def tool_summary(arguments: dict[str, Any]) -> str:
    for key in SUMMARY_KEYS:
        value = arguments.get(key)
        if isinstance(value, str) and value:
            return one_line(value)
    return one_line(json.dumps(arguments, ensure_ascii=False)) if arguments else ""


def result_lines(result: str, *, error: bool, keep: int = 3) -> list[str]:
    lines = [line.rstrip() for line in result.strip().splitlines()] or ["(no output)"]
    shown = [one_line(line, 160) for line in lines[: keep + 1 if error else keep]]
    if error:
        shown[0] = f"Error: {shown[0]}"
    hidden = len(lines) - len(shown)
    return [*shown, f"... +{hidden} lines"] if hidden > 0 else shown


@dataclass
class View:
    """Turns blocks and deltas into screen lines, Claude Code style: each tool step, then the
    answer. Text arrives twice, as live deltas and as a stored block, on two channels that can
    overtake each other; whichever shows a text first, the other copy is dropped."""

    term: Terminal
    color: bool = False
    run_open: bool = False
    """A streamed answer is being printed and no other line has come since."""
    unmatched: int = 0
    """Streamed answers whose stored text block has not arrived yet."""
    ahead: str = ""
    """Stored text shown before its deltas arrived; those deltas are dropped."""
    mid_line: bool = False
    progress: str = ""

    def new_turn(self) -> None:
        self.run_open, self.unmatched, self.ahead, self.mid_line = False, 0, "", False

    def paint(self, style: str, text: str) -> str:
        return f"{style}{text}{RESET}" if self.color else text

    def line(self, text: str = "") -> None:
        self.break_line()
        self.run_open = False
        self.term.out(text)

    def break_line(self) -> None:
        if self.mid_line:
            self.term.out()
            self.mid_line = False

    def delta(self, data: dict[str, Any]) -> None:
        kind, text = data.get("kind"), str(data.get("text", ""))
        if data.get("tool_use_id"):
            if kind == "tool_progress" and text != self.progress:
                self.progress = text
                self.line(self.paint(DIM, f"  helper: {one_line(text)}"))
            return
        if kind != "text" or not text:
            return
        if self.ahead.startswith(text):
            self.ahead = self.ahead[len(text) :]
            return
        self.ahead = ""
        if not self.run_open:
            self.break_line()
            self.term.out("* ", end="")
            self.run_open = True
            self.unmatched += 1
        self.term.out(text, end="")
        self.mid_line = not text.endswith("\n")

    def block(self, kind: str, content: dict[str, Any]) -> None:
        match kind:
            case "text":
                if self.unmatched:
                    self.unmatched -= 1
                    return
                text = str(content.get("text", ""))
                self.line(f"* {text}")
                self.ahead += text
            case "tool":
                self.tool(content)
            case "agents":
                self.agents(content)
            case "plan":
                self.plan(content)
            case "needs_you":
                self.line(self.paint(RED, f"  ! {content.get('reason', '')}"))
            case "changed":
                self.changed(content)
            case "permission" | "question" if content.get("state") == "expired":
                self.line(self.paint(DIM, "  (the ask expired before an answer)"))
            case _:
                pass

    def tool(self, content: dict[str, Any]) -> None:
        state = content.get("state")
        if state == "started":
            name = tool_label(str(content.get("name", "?")))
            arguments = cast("dict[str, Any]", content.get("arguments") or {})
            self.line(f"{self.paint(BOLD, f'* {name}')}({tool_summary(arguments)})")
            return
        lines = result_lines(str(content.get("result", "")), error=state == "error")
        style = RED if state == "error" else DIM
        for number, text in enumerate(lines):
            lead = "  L " if number == 0 else "    "
            self.line(self.paint(style, f"{lead}{text}"))

    def agents(self, content: dict[str, Any]) -> None:
        state = content.get("state")
        if "task_id" not in content or state is None:
            return
        if state == "working" and content.get("description"):
            self.line(f"  helper started: {one_line(str(content['description']))}")
        elif state != "working" and "summary" in content:
            summary = one_line(str(content.get("summary") or ""))
            self.line(f"  helper {state}: {summary}".rstrip())

    def plan(self, content: dict[str, Any]) -> None:
        marks = {"completed": "[x]", "in_progress": "[~]"}
        for todo in cast("list[dict[str, Any]]", content.get("todos") or []):
            mark = marks.get(str(todo.get("status")), "[ ]")
            self.line(self.paint(DIM, f"  {mark} {one_line(str(todo.get('content', '')))}"))

    def changed(self, content: dict[str, Any]) -> None:
        match content.get("kind"):
            case "config":
                to = cast("dict[str, Any]", content.get("to") or {})
                self.line(self.paint(DIM, f"  now {describe(to)}"))
            case "compacted":
                self.line(self.paint(DIM, "  conversation compacted"))
            case "rewind":
                self.line(self.paint(DIM, "  files rewound"))
            case _:
                pass


def describe(config: dict[str, Any]) -> str:
    effort = config.get("effort") or "default effort"
    return f"{config.get('profile')} / {config.get('model')} / {config.get('mode')} / {effort}"


def percent(value: object) -> str:
    return f"{float(value) * 100:.0f}%" if isinstance(value, int | float) else "?"


def clock(value: object) -> str:
    if not isinstance(value, str):
        return "unknown"
    return value.replace("T", " ")[:16] + " UTC"


def usage_lines(page: dict[str, Any], chat: dict[str, Any] | None = None) -> list[str]:
    """The usage page, plus `chat`'s token sums per profile when a chat is open."""
    readings: dict[str, dict[str, Any]] = {}
    for reading in cast("list[dict[str, Any]]", page.get("readings", {}).get("claude", [])):
        readings[str(reading.get("window"))] = reading
    lines: list[str] = []
    labels = {"five_hour": "5-hour window", "seven_day": "7-day window"}
    for window, label in labels.items():
        reading = readings.get(window)
        if reading is None:
            lines.append(f"  Claude plan {label}: no reading yet (try /usage refresh)")
            continue
        resets = reading.get("resets_at")
        lines.append(
            f"  Claude plan {label}: {percent(reading.get('utilization'))} used"
            + (f", resets {clock(resets)}" if resets else "")
            + f" (read {clock(reading.get('as_of'))}, {reading.get('source')})"
        )
    for scope, tokens in (("this chat", chat), ("all chats", page.get("tokens"))):
        for profile, sums in cast("dict[str, dict[str, int]]", tokens or {}).items():
            lines.append(
                f"  tokens, {scope}, {profile}: in {sums.get('input_tokens', 0)}  "
                f"out {sums.get('output_tokens', 0)}  "
                f"cache read {sums.get('cache_read_tokens', 0)}  "
                f"cache write {sums.get('cache_write_tokens', 0)}  ({sums.get('calls', 0)} calls)"
            )
            if profile == "gpt":
                lines.append(
                    "    counted by QMA's translator; ChatGPT Settings > Usage has the plan's meter"
                )
    lines.append(
        f"  background cap {percent(page.get('background_cap'))}: "
        f"{page.get('background_cap_note', '')}"
    )
    if page.get("hard_stop"):
        lines.append(f"  ! plan use stopped: {page['hard_stop']}")
    money = cast("dict[str, Any]", page.get("money") or {})
    lines.append(f"  money posture {money.get('posture')}: {money.get('note', '')}")
    return lines


def bundled_cli() -> Path:
    """The CLI the SDK ships, found without importing the SDK."""
    spec = importlib.util.find_spec("claude_agent_sdk")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("claude-agent-sdk is not installed")
    name = "claude.exe" if os.name == "nt" else "claude"
    return Path(next(iter(spec.submodule_search_locations))) / "_bundled" / name


class HttpError(RuntimeError):
    pass


@dataclass
class Console:
    """One operator, one current chat. `client` talks to the host; `stream` opens the live SSE
    channel in a thread of its own."""

    client: httpx.Client
    term: Terminal
    home: Path
    workspace: Path
    model: str | None = None
    timing: bool = False
    color: bool = False
    stream: Callable[[str], Iterator[str]] | None = None
    chat: str | None = None
    after: int = 0
    view: View = field(init=False)
    deltas: queue.Queue[tuple[str, dict[str, Any]]] = field(
        default_factory=queue.Queue[tuple[str, dict[str, Any]]]
    )
    listening: str | None = None

    def __post_init__(self) -> None:
        self.view = View(self.term, self.color)

    def call(self, method: str, path: str, body: Any = None, *, wait: bool = False) -> Any:
        """`wait` lifts the read timeout, for a call that can take minutes."""
        timeout = httpx.Timeout(10.0, read=None) if wait else httpx.USE_CLIENT_DEFAULT
        response = self.client.request(method, path, json=body, timeout=timeout)
        if response.status_code >= 400:
            try:
                error = response.json().get("error", {})
                message = error.get("message") or response.text
            except ValueError:
                message = response.text
            raise HttpError(f"{method} {path} -> {response.status_code}: {message}")
        return response.json() if response.content else None

    def say(self, text: str) -> None:
        self.view.line(text)

    def handle(self, line: str) -> bool:
        """Run one line. False means quit."""
        command = parse(line)
        try:
            match command:
                case Send(text=text):
                    self.turn(text)
                case Slash(name="exit"):
                    return False
                case Slash(name=name, arg=arg):
                    getattr(self, f"do_{name}")(arg)
        except HttpError as error:
            self.say(self.view.paint(RED, f"  ! {error}"))
        return True

    def ensure_chat(self, title: str) -> str:
        if self.chat is None:
            body: dict[str, Any] = {"title": one_line(title, 60), "workspace": str(self.workspace)}
            if self.model:
                body["model"] = self.model
            self.select(str(self.call("POST", "/api/chats", body)["session_id"]))
        return cast("str", self.chat)

    def select(self, chat: str) -> None:
        self.chat = chat
        self.after = 0
        for _ in self.events():
            pass
        self.listen(chat)

    def events(self) -> Iterator[dict[str, Any]]:
        while True:
            page = cast(
                "list[dict[str, Any]]",
                self.call("GET", f"/api/sessions/{self.chat}/events?after={self.after}&limit=1000"),
            )
            for event in page:
                self.after = int(event["id"])
                yield event
            if len(page) < 1000:
                return

    def listen(self, chat: str) -> None:
        if self.stream is None or self.listening == chat:
            return
        self.listening = chat
        ready = threading.Event()
        stream = self.stream

        def run() -> None:
            try:
                for line in stream(chat):
                    ready.set()
                    if self.listening != chat:
                        return
                    if line.startswith("data:"):
                        self.deltas.put((chat, json.loads(line[5:])))
            except Exception:
                ready.set()

        threading.Thread(target=run, daemon=True).start()
        ready.wait(5)

    def turn(self, text: str) -> None:
        chat = self.ensure_chat(text)
        self.view.new_turn()
        started = time.monotonic()
        self.call("POST", f"/api/sessions/{chat}/turns", {"text": text})
        first: list[float] = []
        try:
            self.follow(chat, first)
        except KeyboardInterrupt:
            self.view.break_line()
            self.say(self.view.paint(RED, "  Interrupted. Waiting for the turn to end..."))
            self.call("POST", f"/api/sessions/{chat}/interrupt")
            try:
                self.follow(chat, first, answer_asks=False)
            except KeyboardInterrupt:
                self.say("  Stopped waiting; the turn may still be ending.")
        self.view.break_line()
        if self.timing:
            seen = f"{first[0] - started:.2f} s" if first else "none"
            self.say(self.view.paint(DIM, f"  (first delta after {seen})"))

    def follow(self, chat: str, first: list[float], *, answer_asks: bool = True) -> None:
        """Print deltas and blocks until the chat's record says the turn is idle, then print
        what was stored before that."""
        last_state = 0.0
        while True:
            self.drain(chat, first, wait=EVENT_POLL_S, answer_asks=answer_asks)
            self.read_blocks(answer_asks=answer_asks)
            now = time.monotonic()
            if now - last_state < STATE_POLL_S:
                continue
            last_state = now
            if self.call("GET", f"/api/chats/{chat}")["turn"] == "idle":
                self.drain(chat, first, wait=0, answer_asks=answer_asks)
                self.read_blocks(answer_asks=answer_asks)
                return

    def drain(self, chat: str, first: list[float], *, wait: float, answer_asks: bool) -> None:
        """Print the queued deltas. A new answer run first prints the blocks stored before it,
        because the host stores a tool's result before the next reply streams."""
        try:
            item = self.deltas.get(timeout=wait) if wait else self.deltas.get_nowait()
        except queue.Empty:
            return
        while True:
            owner, data = item
            if owner == chat:
                text = data.get("kind") == "text" and not data.get("tool_use_id")
                if text and not self.view.run_open:
                    self.read_blocks(answer_asks=answer_asks)
                self.view.delta(data)
                if text and not first:
                    first.append(time.monotonic())
            try:
                item = self.deltas.get_nowait()
            except queue.Empty:
                return

    def read_blocks(self, *, answer_asks: bool) -> None:
        for event in list(self.events()):
            block = cast("dict[str, Any]", event["data"].get("block") or {})
            kind, content = str(block.get("type")), cast("dict[str, Any]", block.get("content"))
            if kind in {"permission", "question"} and content.get("state") == "asking":
                self.ask(int(block["seq"]), kind, content, answer=answer_asks)
            else:
                self.view.block(kind, content or {})

    def ask(self, seq: int, kind: str, content: dict[str, Any], *, answer: bool) -> None:
        tool = tool_label(str(content.get("tool", "?")))
        tool_input = cast("dict[str, Any]", content.get("input") or {})
        if kind == "question":
            body = self.questions(tool_input) if answer else {"decision": "reject"}
        else:
            self.say(
                f"{self.view.paint(BOLD, f'? {tool}')} wants to run: {tool_summary(tool_input)}"
            )
            if content.get("reason"):
                self.say(self.view.paint(DIM, f"  reason: {one_line(str(content['reason']))}"))
            always = cast("list[str]", content.get("always") or [])
            body = {"decision": "reject"}
            if answer:
                body = self.permission(always)
        status = self.call("POST", f"/api/approvals/{self.chat}.{seq}", body)["status"]
        choice = {"allow_once": "allowed once", "allow_always": "allowed always"}
        shown = choice.get(body["decision"], body["decision"].replace("_", " "))
        self.say(self.view.paint(DIM, f"  {shown} ({status})"))

    def permission(self, always: list[str]) -> dict[str, Any]:
        offer = f"  [a] always ({', '.join(always)})" if always else ""
        try:
            reply = self.term.decide(f"  Allow? [y] yes once{offer}  [N] no > ").strip().lower()
        except KeyboardInterrupt:
            reply = "n"
        if reply in {"y", "yes"}:
            return {"decision": "allow_once"}
        if always and reply in {"a", "always"}:
            return {"decision": "allow_always"}
        return {"decision": "reject", "message": "The operator said no."}

    def questions(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        answers: dict[str, str] = {}
        for item in cast("list[dict[str, Any]]", tool_input.get("questions") or []):
            question = str(item.get("question", ""))
            options = [
                str(o.get("label")) for o in cast("list[dict[str, Any]]", item.get("options") or [])
            ]
            self.say(f"? {question}")
            for number, label in enumerate(options, start=1):
                self.say(f"  {number}. {label}")
            reply = self.term.decide("  answer > ").strip()
            pick = int(reply) - 1 if reply.isdigit() else -1
            answers[question] = options[pick] if 0 <= pick < len(options) else reply
        return {"decision": "answers", "answers": answers}

    def change(self, change: dict[str, Any], *, confirm: bool) -> None:
        if self.chat is None:
            self.say("  Send a message first; a change applies to a chat.")
            return
        quote = self.call("POST", f"/api/sessions/{self.chat}/quote", change)
        old, new = describe(quote["old"]), describe(quote["new"])
        if quote.get("warning"):
            self.say(self.view.paint(RED, f"  ! {quote['warning']}"))
        if confirm:
            reply = self.term.decide(f"  Switch {old} -> {new}? [y/N] > ").strip().lower()
            if reply not in {"y", "yes"}:
                self.say("  Kept the current settings.")
                return
        applied = self.call("POST", f"/api/sessions/{self.chat}/apply", {"quote_id": quote["id"]})
        self.say(f"  Now {describe(applied['new'])}.")

    def do_model(self, arg: str) -> None:
        if not arg:
            self.say("  Usage: /model <alias or id>, for example /model sonnet")
            return
        self.change({"model": arg}, confirm=True)

    def do_provider(self, arg: str) -> None:
        if not arg:
            rows = cast("dict[str, Any]", self.call("GET", "/api/settings/providers"))
            names = ["claude", *(name for name, row in rows.items() if isinstance(row, dict))]
            for number, name in enumerate(names, start=1):
                self.say(f"  {number}. {name}")
            reply = self.term.decide("  provider > ").strip()
            arg = (
                names[int(reply) - 1] if reply.isdigit() and 0 < int(reply) <= len(names) else reply
            )
            if not arg:
                return
        self.change({"profile": arg}, confirm=True)

    def do_mode(self, arg: str) -> None:
        self.change({"mode": arg}, confirm=False)

    def do_effort(self, arg: str) -> None:
        self.change({"effort": arg}, confirm=False)

    def do_usage(self, arg: str) -> None:
        if arg == "refresh":
            self.say(self.view.paint(DIM, "  reading the plan meter..."))
            page = self.call("POST", "/api/usage/meter")
        else:
            page = self.call("GET", "/api/usage")
        chat = None if self.chat is None else self.call("GET", f"/api/chats/{self.chat}")["tokens"]
        for line in usage_lines(page, chat):
            self.say(line)

    def do_doctor(self, arg: str) -> None:
        if arg == "probe":
            found = self.call("POST", "/api/doctor/probe")
        else:
            found = self.call("GET", "/api/doctor")
        for item in cast("list[dict[str, Any]]", found["lines"]):
            mark = "ok" if item.get("ok") else "!!"
            self.say(f"  [{mark}] {item.get('name')}: {one_line(str(item.get('detail')), 160)}")

    def sign_in(self) -> str:
        lines = cast("list[dict[str, Any]]", self.call("GET", "/api/doctor")["lines"])
        auth = next((item for item in lines if item.get("name") == "plan auth method"), None)
        if auth is None:
            return "Plan sign-in: unknown"
        detail = str(auth.get("detail"))
        if not auth.get("ok"):
            return f"Not signed in to a Claude plan ({detail}). Type /login."
        plan = detail.rsplit("subscription ", 1)[-1].strip().title()
        return f"Signed in to Claude {plan} (claude.ai)"

    def do_status(self, _: str) -> None:
        if self.chat is None:
            self.say(f"  No chat yet; the next message starts one in {self.workspace}.")
        else:
            entry = self.call("GET", f"/api/chats/{self.chat}")
            self.say(f"  chat {self.chat} in {entry['workspace']}")
            self.say(f"  {describe(entry)}, turn {entry['turn']}")
        self.say(f"  {self.sign_in()}")

    def do_resume(self, arg: str) -> None:
        chats = cast("list[dict[str, Any]]", self.call("GET", "/api/chats"))[:20]
        if not chats:
            self.say("  No earlier chats.")
            return
        if not arg:
            for number, entry in enumerate(chats, start=1):
                self.say(f"  {number}. {entry['title']}  ({describe(entry)}, {entry['workspace']})")
            arg = self.term.decide("  resume which? > ").strip()
        pick = next(
            (
                entry
                for number, entry in enumerate(chats, start=1)
                if arg == str(number) or (arg and entry["session_id"].startswith(arg))
            ),
            None,
        )
        if pick is None:
            self.say("  Kept the current chat.")
            return
        self.select(pick["session_id"])
        self.say(f"  Resumed: {pick['title']}")

    def do_new(self, _: str) -> None:
        self.chat = None
        self.say("  The next message starts a new chat.")

    def do_export(self, _: str) -> None:
        if self.chat is None:
            self.say("  No chat to export yet.")
            return
        found = self.call("POST", f"/api/sessions/{self.chat}/export")
        self.say(f"  Exported to {found['folder']}")
        for name in found["files"]:
            self.say(f"    {name}")

    def do_rewind(self, _: str) -> None:
        if self.chat is None:
            self.say("  No chat to rewind yet.")
            return
        points = cast("list[dict[str, str]]", self.call("GET", f"/api/sessions/{self.chat}/rewind"))
        if not points:
            self.say("  No message of this chat has a file checkpoint.")
            return
        shown = points[-10:]
        for number, point in enumerate(shown, start=1):
            self.say(f"  {number}. {one_line(point['text'], 80)}")
        reply = self.term.decide("  restore files to before which message? > ").strip()
        if not (reply.isdigit() and 0 < int(reply) <= len(shown)):
            self.say("  Nothing rewound.")
            return
        point = shown[int(reply) - 1]
        self.call("POST", f"/api/sessions/{self.chat}/rewind", {"message_id": point["message_id"]})
        self.say(f"  Files restored to before: {one_line(point['text'], 80)}")
        self.say(
            "  Only changes made with Write and Edit come back; shell commands are not tracked."
        )

    def do_stop(self, _: str) -> None:
        if self.chat is not None:
            self.call("POST", f"/api/sessions/{self.chat}/interrupt")
            self.say("  Asked the turn to stop.")

    def login_chatgpt(self) -> None:
        self.say("  Signing in to ChatGPT for QMA; the GPT probe may take a few minutes.")
        status = self.call("POST", "/api/gpt/login", {"sign_in": False}, wait=True)
        for line in status["lines"]:
            self.say(f"  {line}")
        if status["needs_sign_in"]:
            reply = self.term.decide("  Open OpenAI's sign-in page to approve QMA? y/N > ")
            if reply.strip().lower() not in ("y", "yes"):
                self.say("  Not signed in to ChatGPT.")
                return
            self.say("  Approve QMA on OpenAI's page; this console carries on when it is done.")
            status = self.call("POST", "/api/gpt/login", {"sign_in": True}, wait=True)
            for line in status["lines"]:
                self.say(f"  {line}")
        if status["lane"] and not status["consent"]:
            reply = self.term.decide(
                "  Let Background and helper chats use your ChatGPT plan unattended? y/N > "
            )
            consent = reply.strip().lower() in ("y", "yes")
            for line in self.call("POST", "/api/gpt/consent", {"consent": consent})["lines"]:
                self.say(f"  {line}")

    def do_login(self, arg: str) -> None:
        if arg == "chatgpt":
            self.login_chatgpt()
            return
        cli = bundled_cli()
        env = dict(os.environ) | {"CLAUDE_CONFIG_DIR": str(self.home / "claude")}
        self.say("  Starting Claude Code's own sign-in in QMX's plan home (claude.ai accounts).")
        self.say("  Finish sign-in on Anthropic's page; this console carries on when it is done.")
        login = [str(cli), "--settings", FORCE_CLAUDEAI, "auth", "login", "--claudeai"]
        child = subprocess.Popen(login, env=env)
        while True:
            try:
                child.wait()
                break
            except KeyboardInterrupt:
                continue
        self.say(f"  {self.sign_in()}")

    def do_help(self, _: str) -> None:
        for name, text in HELP.items():
            self.say(f"  /{name:<9} {text}")
        self.say("  Any other text, /compact and /context included, goes to the agent.")


def control_token() -> str | None:
    return keyring.get_password(BEARER_ENTRY, BEARER_USER)


def host_up(port: int, token: str | None) -> bool:
    if token is None:
        return False
    try:
        answer = httpx.get(
            f"http://127.0.0.1:{port}/api/health",
            headers={"Authorization": f"Bearer {token}"},
            timeout=2,
        )
    except httpx.HTTPError:
        return False
    return answer.status_code == 200


def serve(command: str, home: Path, port: int) -> int:
    argv = [sys.executable, "-m", "qma.serve", command, "--home", str(home), "--port", str(port)]
    return subprocess.run(argv, check=False).returncode


def prepare_terminal() -> bool:
    """Turn Ctrl+C on, since a parent may have started this process with it ignored, and turn
    colors on. True when the terminal shows colors."""
    if sys.platform != "win32":
        return sys.stdout.isatty()
    import ctypes  # noqa: PLC0415

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCtrlHandler(None, False)
    if not sys.stdout.isatty():
        return False
    handle = kernel32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qma.console", description="Talk to the QMA harness.")
    parser.add_argument("--home", type=Path, default=Path.home() / ".qmx")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--model", help="model for new chats; the host's default otherwise")
    parser.add_argument("--resume", help="a session id to continue")
    parser.add_argument("--timing", action="store_true", help="print the first-delta delay")
    args = parser.parse_args(argv)
    home: Path = args.home.resolve()
    scrub_process_env(os.environ, read_keep_names(home / "settings.toml"))
    stdout: Any = sys.stdout
    if isinstance(stdout, io.TextIOWrapper):
        cast("io.TextIOWrapper[Any]", stdout).reconfigure(encoding="utf-8", errors="replace")

    color = prepare_terminal()
    term = StdTerminal()
    started_host = False
    if not host_up(args.port, control_token()):
        term.out(f"Starting the QMA host for {home} on port {args.port}...")
        if serve("start", home, args.port) != 0:
            serve("stop", home, args.port)
            if serve("start", home, args.port) != 0:
                term.out("The host did not start; see control.log in the home.")
                return 1
        started_host = True
    token = control_token()
    if token is None:
        term.out("No qmx/control-token in the keyring.")
        return 1
    base = f"http://127.0.0.1:{args.port}"
    headers = {"Authorization": f"Bearer {token}"}

    def stream(chat: str) -> Iterator[str]:
        timeout = httpx.Timeout(5, read=None)
        with (
            httpx.Client(base_url=base, headers=headers, timeout=timeout) as live,
            live.stream("GET", f"/api/sessions/{chat}/live") as reply,
        ):
            yield ""
            yield from reply.iter_lines()

    try:
        with httpx.Client(base_url=base, headers=headers, timeout=120) as client:
            console = Console(
                client,
                term,
                home,
                args.workspace.resolve(),
                model=args.model,
                timing=args.timing,
                color=color,
                stream=stream,
            )
            run(console, args.resume)
    finally:
        if started_host:
            serve("stop", home, args.port)
    return 0


def run(console: Console, resume: str | None) -> None:
    term = console.term
    term.out(f"QMA console (temporary). Home {console.home}, folder {console.workspace}")
    try:
        term.out(console.sign_in())
    except HttpError as error:
        term.out(f"Plan sign-in unknown: {error}")
    if resume:
        console.select(resume)
    term.out("/help lists commands. Ctrl+C stops a reply; Ctrl+C twice at the prompt quits.")
    armed = 0.0
    while True:
        try:
            line = term.ask(PROMPT).strip()
        except EOFError:
            return
        except KeyboardInterrupt:
            if time.monotonic() - armed < 2:
                term.out()
                return
            armed = time.monotonic()
            term.out("\n  Press Ctrl+C again to quit.")
            continue
        try:
            if line and not console.handle(line):
                return
        except KeyboardInterrupt:
            term.out("\n  Cancelled.")


if __name__ == "__main__":
    raise SystemExit(main())
