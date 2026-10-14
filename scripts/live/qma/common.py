"""Shared setup for the QMA live checks: the ship home, a throwaway HOME, the evidence log in
`QMA_EVIDENCE_DIR`.

Every check runs the agents workspace Python (`qmx-agents/.venv`). No check reads the login
token; `require_login` only tests that the credentials file exists.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, cast

from claude_agent_sdk import ClaudeAgentOptions
from qma.boot import scrub_process_env

SHIP: Final = Path("D:/QMX-worktrees/qma-ship")
CONFIG_DIR: Final = SHIP / "home" / "claude"
SCRATCH: Final = Path(os.environ.get("QMA_LIVE_SCRATCH", "D:/Temp/qma-live"))
FAKE_HOME: Final = SCRATCH / "home"
FAKE_TMP: Final = SCRATCH / "tmp"
MODEL: Final = "haiku"
LAUNCHER: Final = Path(sys.executable).parent / (
    "qma-cli-launcher.exe" if os.name == "nt" else "qma-cli-launcher"
)


EVIDENCE: Final = os.environ.get("QMA_EVIDENCE_DIR")


class Log:
    """Writes `<QMA_EVIDENCE_DIR>/<slug>.log`."""

    def __init__(self, slug: str) -> None:
        evidence = EVIDENCE
        if not evidence:
            raise SystemExit("set QMA_EVIDENCE_DIR, e.g. D:/QMX-worktrees/qma-ship/evidence/<pr>")
        Path(evidence).mkdir(parents=True, exist_ok=True)
        self.path = Path(evidence) / f"{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped, flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


def boot() -> tuple[str, ...]:
    """What `qma.serve` will do first: scrub this process, then set the scratch dirs."""
    removed = scrub_process_env(os.environ)
    for folder in throwaway_env().values():
        Path(folder).mkdir(parents=True, exist_ok=True)
    os.environ |= {"TMP": str(FAKE_TMP), "TEMP": str(FAKE_TMP)}
    return removed


def throwaway_env() -> dict[str, str]:
    return {
        "HOME": str(FAKE_HOME),
        "USERPROFILE": str(FAKE_HOME),
        "APPDATA": str(FAKE_HOME / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(FAKE_HOME / "AppData" / "Local"),
        "TMP": str(FAKE_TMP),
        "TEMP": str(FAKE_TMP),
    }


def home_env() -> dict[str, str]:
    return {"CLAUDE_CONFIG_DIR": str(CONFIG_DIR)} | throwaway_env()


def chat_env(chat: str, procs_dir: Path, cap: str) -> dict[str, str]:
    return home_env() | {
        "QMA_CHAT_ID": chat,
        "QMA_PROC_DIR": str(procs_dir),
        "QMA_CAP": cap,
    }


def require_login(log: Log) -> None:
    present = (CONFIG_DIR / ".credentials.json").exists()
    log(f"ship home credentials file present: {present}")
    if not present:
        log("BLOCKED: the ship home has no plan login")
        raise SystemExit(3)


def chat_options(
    env: Mapping[str, str], cwd: Path, *, tools: list[str] | None, **overrides: Any
) -> ClaudeAgentOptions:
    mode = overrides.get("permission_mode", "bypassPermissions")
    if mode == "bypassPermissions" and tools is None:
        raise ValueError("bypassPermissions needs an explicit tools list")
    cwd.mkdir(parents=True, exist_ok=True)
    kwargs: dict[str, Any] = {
        "cli_path": str(LAUNCHER),
        "env": dict(env),
        "setting_sources": [],
        "settings": json.dumps({"forceLoginMethod": "claudeai"}),
        "strict_mcp_config": True,
        "model": MODEL,
        "cwd": str(cwd),
        "permission_mode": "bypassPermissions",
        "tools": tools,
        "max_turns": 3,
    }
    return ClaudeAgentOptions(**(kwargs | overrides))


SHIP_HOME: Final = SHIP / "home"
TURN_TIMEOUT_S: Final = 300.0


def use_fake_home() -> None:
    """Point HOME, USERPROFILE, the app data folders and TMP at the throwaway folders, so a CLI the
    harness starts in this process never reads the operator's own `~/.claude` or profile."""
    env = throwaway_env()
    for folder in env.values():
        Path(folder).mkdir(parents=True, exist_ok=True)
    os.environ |= env


def session_blocks(control: Any, chat: str, after: int = 0) -> list[dict[str, Any]]:
    """Every block of a session after event id `after`, oldest first, with its event id."""
    found: list[dict[str, Any]] = []
    while True:
        page = control.events("sessions", after, chat, 1000)
        for event in page:
            data = event["data"]
            if data.get("type") == "block":
                found.append({"event": event["id"], **data["block"]})
        if len(page) < 1000:
            return found
        after = page[-1]["id"]


def last_event(control: Any, chat: str) -> int:
    events = control.events("sessions", 0, chat, 1000)
    while len(events) == 1000:
        events = control.events("sessions", events[-1]["id"], chat, 1000)
    return events[-1]["id"] if events else 0


def show(log: Log, block: dict[str, Any]) -> None:
    content = dict(block["content"])
    for key in ("result", "text"):
        if isinstance(content.get(key), str) and len(content[key]) > 300:
            content[key] = content[key][:300] + "..."
    log(f"  [{block['type']}] {json.dumps(content, ensure_ascii=False)}")


async def wait_turn(home: Any, chat: str, seconds: float = TURN_TIMEOUT_S) -> Any:
    """The chat record once its turn is "idle" again, or the running record at the timeout."""
    import asyncio  # noqa: PLC0415

    from qma.harness.home import read_record, session_id  # noqa: PLC0415

    deadline = time.monotonic() + seconds
    while True:
        record = read_record(home, session_id(chat))
        if record is None or record.turn == "idle" or time.monotonic() > deadline:
            return record
        await asyncio.sleep(0.2)


def chat_args(doc: str | None) -> Any:
    import argparse  # noqa: PLC0415

    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument("--home", type=Path, default=SHIP_HOME, help="the QMX home")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--workspace", type=Path, default=SCRATCH / "workspace")
    return parser


class Session:
    """One harness opened in this process and one chat in it."""

    def __init__(self, harness: Any, home: Any, control: Any, chat: str) -> None:
        self.harness, self.home, self.control, self.chat = harness, home, control, chat

    @classmethod
    async def start(
        cls,
        root: Path,
        *,
        model: str,
        workspace: Path,
        title: str,
        test: Any = None,
        profile: str = "claude",
        mode: str = "default",
    ) -> Session:
        from qma.harness import Harness, NewChat, QmxHome  # noqa: PLC0415
        from qma.harness.routes import control_service  # noqa: PLC0415

        home = QmxHome(root)
        control = control_service(home)
        harness = await Harness.open(home, control=control, test=test)
        workspace.mkdir(parents=True, exist_ok=True)
        spec = NewChat(
            title=title, model=model, workspace=workspace, profile=profile, mode=cast(Any, mode)
        )
        chat = await harness.start_chat(spec)
        return cls(harness, home, control, chat)

    @property
    def relay(self) -> Any:
        return self.harness._deps.relay

    def transcript(self) -> str:
        from qma.harness.chat import transcript  # noqa: PLC0415

        path = transcript(self.home, self.chat)
        return path.read_text(encoding="utf-8") if path else ""

    def journal(self) -> list[dict[str, Any]]:
        path = self.home.root / "runs" / self.chat / "journal.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    async def turn(self, log: Log, text: str) -> tuple[Any, list[dict[str, Any]]]:
        """Send operator text, wait for the turn to end, and log the blocks it wrote."""
        from qma.harness import OperatorText  # noqa: PLC0415

        mark = last_event(self.control, self.chat)
        log(f"turn: {text}")
        await self.harness.send(self.chat, OperatorText(text))
        record = await wait_turn(self.home, self.chat)
        found = session_blocks(self.control, self.chat, mark)
        for block in found:
            show(log, block)
        log(f"record turn={record.turn} started={record.started}")
        return record, found


def throwaway_home(slug: str) -> Path:
    """A fresh QMX home under the scratch folder. Fake-model and key checks never need the plan
    login, so they never touch the ship home."""
    import shutil  # noqa: PLC0415

    root = SCRATCH / "homes" / slug
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


CANARY: Final = "sk-ant-oat01-QMXCANARY" + "Zq7Xw2Lp9V" * 4
"""A fake login of the real token shape. Never a real credential."""


def plant_canary_login(root: Path) -> None:
    """A fake plan login in a throwaway QMX home, so a check can grep for it."""
    if root.resolve() == SHIP_HOME.resolve():
        raise SystemExit("refusing to plant a canary in the ship home")
    plan = root / "claude"
    plan.mkdir(parents=True, exist_ok=True)
    (plan / ".credentials.json").write_text(
        json.dumps({"claudeAiOauth": {"accessToken": CANARY}}), encoding="utf-8"
    )


def put_providers(root: Path, rows: Mapping[str, Any]) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    control_service(QmxHome(root)).settings_put("providers", dict(rows))


def put_claude(root: Path, values: Mapping[str, Any]) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    control_service(QmxHome(root)).settings_put("claude", dict(values))


def fake_row(url: str, model: str = "fake-model") -> dict[str, Any]:
    from fake_model import FAKE_REF  # noqa: PLC0415

    return {
        "base_url": url,
        "credential_ref": FAKE_REF,
        "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), model),
    }


def use_fake_key() -> None:
    """The relay reads `qmx/hp7-fake` as the fake model's key; every other reference still goes
    to the OS keyring. Nothing is written to the keyring."""
    import qma.harness.harness as harness_module  # noqa: PLC0415
    from fake_model import FAKE_KEY, FAKE_REF  # noqa: PLC0415

    real = harness_module.keyring_secret

    def lookup(reference: str) -> str:
        return FAKE_KEY if reference == FAKE_REF else real(reference)

    harness_module.keyring_secret = lookup


def capture_grants() -> list[Any]:
    """Every grant the relay mints from now on, so a check can grep for its secret."""
    from qma.harness.relay import Relay  # noqa: PLC0415

    minted: list[Any] = []
    original = Relay.grant

    def grant(self: Relay, *args: Any, **kwargs: Any) -> Any:
        found = original(self, *args, **kwargs)
        minted.append(found)
        return found

    Relay.grant = grant  # type: ignore[method-assign]
    return minted


def capture_launches() -> list[Any]:
    """The `ClaudeAgentOptions` of every chat launch from now on, and each CLI's messages."""
    import qma.harness.chat as chat_module  # noqa: PLC0415

    launched: list[Any] = []
    base = chat_module.ClaudeSDKClient

    class Tap(base):  # type: ignore[valid-type, misc]
        def __init__(self, options: Any) -> None:
            super().__init__(options)
            self.seen: list[Any] = []
            launched.append(self)

        async def receive_messages(self) -> Any:
            async for message in super().receive_messages():
                self.seen.append(message)
                yield message

    chat_module.ClaudeSDKClient = Tap
    return launched


def files_holding(roots: list[Path], needle: str) -> list[Path]:
    """Every file under `roots` whose bytes hold `needle`. Prints nothing of the needle."""
    data = needle.encode()
    found: list[Path] = []
    for root in roots:
        for path in [root] if root.is_file() else root.rglob("*"):
            if path.is_file():
                try:
                    if data in path.read_bytes():
                        found.append(path)
                except OSError:
                    continue
    return found
