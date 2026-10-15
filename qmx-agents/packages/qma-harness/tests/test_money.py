from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from qma.harness import money
from qma.harness.money import (
    Ask,
    Deny,
    GateRules,
    MoneySurfaceError,
    Pass,
    check_tool_surface,
    deny_rules,
    gate,
    normalize_path,
    pre_tool_use,
)

RULES = GateRules(
    proposal_tools=frozenset({"mcp__qmx__propose_order"}),
    mandatory_asks=frozenset({"mcp__qmx__propose_order", "mcp__qmx__apps_publish"}),
    dispatch_targets=MappingProxyType({"mcp__qmx__apps_call": "tool"}),
    protected_paths=(
        "/d/qmx/home/claude",
        "/d/qmx/home/chats",
        "/d/qmx/home/control.db",
        "/d/qmx/home/settings.toml",
    ),
    secret_paths=(
        "/d/qmx/home/claude/.credentials.json",
        "/d/qmx/home/claude/.claude.json",
        "/c/Users/Op/.claude/.credentials.json",
        "/c/Users/Op/.claude.json",
    ),
    personal_homes=("/c/Users/Op/.claude",),
    keyring_names=frozenset({"qmx/ctrader", "qmx/openrouter"}),
    broker_hosts=frozenset({"ctraderapi.com"}),
    variables=MappingProxyType(
        {
            "HOME": "/c/Users/Op",
            "USERPROFILE": "/c/Users/Op",
            "CLAUDE_CONFIG_DIR": "/d/qmx/home/claude",
        }
    ),
    case_insensitive=True,
)
CWD = "C:\\Users\\Op\\Desktop\\QMX"

VERDICTS: list[tuple[str, dict[str, Any], str, str]] = [
    (
        "Bash",
        {"command": "python -c \"import keyring; keyring.get_password('QMX/ctrader','ctrader')\""},
        "deny",
        "credential store (keyring)",
    ),
    ("Bash", {"command": "cmdkey /list"}, "deny", "credential store (cmdkey)"),
    (
        "PowerShell",
        {"command": "Get-StoredCredential -Target x"},
        "deny",
        "credential store (get-storedcredential)",
    ),
    ("Bash", {"command": "vaultcmd /listcreds:x"}, "deny", "credential store (vaultcmd)"),
    ("Bash", {"command": "echo QMX/CTRADER"}, "deny", "QMX credential (qmx/ctrader)"),
    ("Bash", {"command": "cat ~/.claude/settings.json"}, "deny", "own Claude home"),
    ("Bash", {"command": "cat $HOME/.claude/agents/a.md"}, "deny", "own Claude home"),
    ("Bash", {"command": "cat ${HOME}/.Claude/a.md"}, "deny", "own Claude home"),
    (
        "PowerShell",
        {"command": "Get-Content $env:USERPROFILE\\.claude\\CLAUDE.md"},
        "deny",
        "own Claude home",
    ),
    ("Bash", {"command": "type %USERPROFILE%\\.claude\\a.md"}, "deny", "own Claude home"),
    (
        "Bash",
        {"command": 'cat "$CLAUDE_CONFIG_DIR/.credentials.json"'},
        "deny",
        "Claude login or its home (.credentials)",
    ),
    ("Bash", {"command": "ls $CLAUDE_CONFIG_DIR"}, "deny", "(claude_config_dir)"),
    (
        "Bash",
        {"command": "cat ../../../../../d/qmx/home/claude/.claude.json"},
        "deny",
        "login file (/d/qmx/home/claude/.claude.json)",
    ),
    ("Bash", {"command": "cat D:/QMX/HOME/claude/.CLAUDE.json"}, "deny", "login file"),
    (
        "Monitor",
        {"command": "curl -N https://live.ctraderapi.com:5035"},
        "deny",
        "reach a broker (ctraderapi.com)",
    ),
    ("Bash", {"command": "ls"}, "pass", ""),
    ("Bash", {"command": "git status", "description": "check .credentials"}, "pass", ""),
    ("Bash", {"command": "ls ~"}, "pass", ""),
    ("Bash", {"command": "find / -name .claude"}, "deny", "agents cannot"),
    ("Bash", {"command": "find . -name .claude.json"}, "deny", "Claude homes or login files"),
    ("Bash", {"command": "find / -maxdepth 4 -type d"}, "deny", "sweep a drive root"),
    (
        "Bash",
        {"command": "grep -r token ~"},
        "deny",
        "sweep a drive root or a user home (/c/users/op)",
    ),
    ("Bash", {"command": "dir /s C:\\"}, "deny", "sweep a drive root"),
    ("Bash", {"command": "echo x > D:/qmx/home/settings.toml"}, "deny", "QMX state from a shell"),
    ("Edit", {"file_path": "d:\\QMX\\Home\\settings.toml"}, "deny", "write QMX state"),
    ("Write", {"file_path": "D:/qmx/home/chats/a.json"}, "deny", "write QMX state"),
    ("Read", {"file_path": "D:/qmx/home/settings.toml"}, "pass", ""),
    ("Read", {"file_path": "D:/elsewhere/.credentials.json"}, "deny", "login file"),
    ("Read", {"file_path": ".credentials.json"}, "deny", "login file"),
    ("Read", {"file_path": "~/.claude/settings.json"}, "deny", "own Claude home"),
    ("Grep", {"pattern": "x", "path": "C:/Users/Op"}, "deny", "holds a login file"),
    ("Grep", {"pattern": "x"}, "pass", ""),
    ("Glob", {"pattern": "**/.credentials.json"}, "deny", "search for login files"),
    ("Glob", {"pattern": "C:/Users/Op/.claude/**"}, "deny", "own Claude home"),
    ("Edit", {"file_path": "src/a.py"}, "pass", ""),
    ("Read", {"file_path": r"\\?\C:\Users\Op\.claude\settings.json"}, "deny", "network"),
    ("Read", {"file_path": r"\\.\C:\Users\Op\.claude\a.md"}, "deny", "device or network"),
    ("Read", {"file_path": r"\\localhost\c$\Users\Op\a.md"}, "deny", "device or network"),
    ("Read", {"file_path": "//localhost/c$/Users/Op/a.md"}, "deny", "device or network"),
    ("Read", {"file_path": "C:/Users/Op/.claude/.credentials.json::$DATA"}, "deny", "stream"),
    ("Read", {"file_path": ".credentials.json:x"}, "deny", "stream"),
    ("Read", {"file_path": "C:/Users/Op/CLAUDE~1/CREDEN~1.JSO"}, "deny", "8.3 short name"),
    ("Grep", {"pattern": "x", "path": "C:/Users/Op/CLAUDE~1"}, "deny", "8.3 short name"),
    ("Glob", {"pattern": "C:/Users/Op/CLAUDE~1/*"}, "deny", "8.3 short name"),
    ("Read", {"file_path": "C:/Users/Op/.claude./settings.json"}, "deny", "dot or a space"),
    ("Read", {"file_path": "C:/Users/Op/.claude /settings.json"}, "deny", "dot or a space"),
    ("Edit", {"file_path": "D:/qmx/home/settings.toml."}, "deny", "dot or a space"),
    ("Read", {"file_path": "../a/./b.py"}, "pass", ""),
    ("Bash", {"command": r"cat '\\?\C:\Users\Op\a.md'"}, "deny", "device or network"),
    ("PowerShell", {"command": r"gc \\localhost\c$\Users\Op\a.md"}, "deny", "device or network"),
    ("Bash", {"command": "cat C:/Users/Op/a.md:x"}, "deny", "stream"),
    ("Bash", {"command": "git show HEAD~1:src/a.py"}, "pass", ""),
    ("Bash", {"command": "git commit -m 'Fix src/a.py.'"}, "pass", ""),
    ("mcp__broker__placeOrder", {}, "deny", "is submit_order"),
    ("mcp__x__close_position2", {}, "deny", "is close_position"),
    ("mcp__broker__cancel_all_orders", {}, "deny", "is cancel_order"),
    ("mcp__broker__OrderSend", {}, "deny", "is send_order"),
    ("mcp__ctrader__ProtoOANewOrderReq", {}, "deny", "is new_order"),
    ("mcp__broker__buy_market", {}, "deny", "is buy"),
    ("mcp__broker__list_orders", {}, "pass", ""),
    ("mcp__qmx__apps_call", {"app_id": "a", "tool": "OrderSend"}, "deny", "target OrderSend"),
    ("mcp__qmx__apps_call", {"app_id": "a", "tool": "get_quote"}, "pass", ""),
    ("mcp__qmx__propose_order", {}, "ask", "order proposal always asks"),
    ("mcp__qmx__apps_publish", {}, "ask", "always asks"),
    ("mcp__qmx__read_bars", {}, "pass", ""),
    ("ExitPlanMode", {}, "pass", ""),
    ("WebFetch", {"url": "https://demo.ctraderapi.com/x"}, "deny", "reach a broker"),
    ("WebFetch", {"url": "https://docs.python.org"}, "pass", ""),
]


def kind(verdict: money.Verdict) -> tuple[str, str]:
    match verdict:
        case Pass():
            return "pass", ""
        case Ask(reason=reason):
            return "ask", reason
        case Deny(reason=reason):
            return "deny", reason


@pytest.mark.parametrize(("tool", "tool_input", "expected", "reason"), VERDICTS)
def test_gate_verdict_table(
    tool: str, tool_input: dict[str, Any], expected: str, reason: str
) -> None:
    seen, why = kind(gate(tool, tool_input, RULES, cwd=CWD, agent_id=None))
    assert seen == expected
    assert reason in why
    if expected == "deny":
        assert why.startswith("money rule: ")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("C:\\Users\\Op\\.claude", "/c/users/op/.claude"),
        ("~/.claude", "/c/users/op/.claude"),
        ("%USERPROFILE%\\a", "/c/users/op/a"),
        ("$env:HOME/a", "/c/users/op/a"),
        ("../x/./y", "/c/users/op/desktop/x/y"),
        ("//c/Users//Op", "/c/users/op"),
        ("$CLAUDE_CONFIG_DIR/.credentials.json", "/d/qmx/home/claude/.credentials.json"),
        ("$UNKNOWN/a", "/c/users/op/desktop/qmx/$unknown/a"),
    ],
)
def test_normalize_path(raw: str, expected: str) -> None:
    found = normalize_path(
        raw, cwd=CWD, home="/c/Users/Op", case_insensitive=True, variables=RULES.variables
    )
    assert found == expected


def test_normalize_path_keeps_case_for_rules() -> None:
    assert (
        normalize_path("C:\\Users\\Op\\.claude", cwd="/", home="/", case_insensitive=False)
        == "/c/Users/Op/.claude"
    )


def test_deny_rules_are_rendered_in_the_double_slash_form() -> None:
    assert deny_rules(RULES) == [
        "Read(//d/qmx/home/claude/.credentials.json)",
        "Edit(//d/qmx/home/claude/.credentials.json)",
        "Write(//d/qmx/home/claude/.credentials.json)",
        "Read(//d/qmx/home/claude/.claude.json)",
        "Edit(//d/qmx/home/claude/.claude.json)",
        "Write(//d/qmx/home/claude/.claude.json)",
        "Read(//c/Users/Op/.claude/.credentials.json)",
        "Edit(//c/Users/Op/.claude/.credentials.json)",
        "Write(//c/Users/Op/.claude/.credentials.json)",
        "Read(//c/Users/Op/.claude.json)",
        "Edit(//c/Users/Op/.claude.json)",
        "Write(//c/Users/Op/.claude.json)",
        "Read(//**/.credentials.json)",
        "Edit(//**/.credentials.json)",
        "Write(//**/.credentials.json)",
        "Read(//c/Users/Op/.claude/**)",
        "Edit(//c/Users/Op/.claude/**)",
        "Write(//c/Users/Op/.claude/**)",
        "NotebookEdit(//c/Users/Op/.claude/**)",
        "Edit(//d/qmx/home/claude)",
        "Write(//d/qmx/home/claude)",
        "NotebookEdit(//d/qmx/home/claude)",
        "Edit(//d/qmx/home/claude/**)",
        "Write(//d/qmx/home/claude/**)",
        "NotebookEdit(//d/qmx/home/claude/**)",
        "Edit(//d/qmx/home/chats)",
        "Write(//d/qmx/home/chats)",
        "NotebookEdit(//d/qmx/home/chats)",
        "Edit(//d/qmx/home/chats/**)",
        "Write(//d/qmx/home/chats/**)",
        "NotebookEdit(//d/qmx/home/chats/**)",
        "Edit(//d/qmx/home/control.db)",
        "Write(//d/qmx/home/control.db)",
        "NotebookEdit(//d/qmx/home/control.db)",
        "Edit(//d/qmx/home/control.db/**)",
        "Write(//d/qmx/home/control.db/**)",
        "NotebookEdit(//d/qmx/home/control.db/**)",
        "Edit(//d/qmx/home/settings.toml)",
        "Write(//d/qmx/home/settings.toml)",
        "NotebookEdit(//d/qmx/home/settings.toml)",
        "Edit(//d/qmx/home/settings.toml/**)",
        "Write(//d/qmx/home/settings.toml/**)",
        "NotebookEdit(//d/qmx/home/settings.toml/**)",
    ]


def hook(tool: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    callback = pre_tool_use(RULES)
    data: Any = {"tool_name": tool, "tool_input": tool_input, "cwd": CWD}
    return dict(asyncio.run(callback(data, None, {"signal": None})))


def test_the_hook_denies_with_the_reason() -> None:
    assert hook("Bash", {"command": "cmdkey /list"}) == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "money rule: agents cannot read the OS credential "
            "store (cmdkey)",
        }
    }
    assert hook("Bash", {"command": "ls"}) == {}
    assert hook("mcp__qmx__apps_publish", {})["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_an_exception_inside_the_gate_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*args: object, **kwargs: object) -> money.Verdict:
        raise KeyError("boom")

    monkeypatch.setattr(money, "gate", broken)
    assert hook("Bash", {"command": "ls"}) == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "money rule: the gate failed (KeyError), so the call "
            "is blocked",
        }
    }


def test_a_hook_input_without_a_tool_name_denies() -> None:
    callback = pre_tool_use(RULES)
    data: Any = {"cwd": CWD}
    found = asyncio.run(callback(data, None, {"signal": None}))
    assert found["hookSpecificOutput"]["permissionDecision"] == "deny"  # pyright: ignore[reportTypedDictNotRequiredAccess, reportGeneralTypeIssues]


def test_the_surface_check_refuses_money_names_and_metadata_but_honours_the_exemption() -> None:
    with pytest.raises(MoneySurfaceError, match="Money-path act refused: placeOrder"):
        check_tool_surface(["read_bars", "placeOrder"], {}, frozenset())
    with pytest.raises(MoneySurfaceError, match="Money-path tool refused: get_x"):
        check_tool_surface(["get_x"], {"get_x": {"_meta": {"money_path": True}}}, frozenset())
    check_tool_surface(
        ["propose_order"],
        {"propose_order": {"_meta": {"money_path": True}}},
        frozenset({"propose_order"}),
    )


def short_path(path: Path) -> str:
    import ctypes

    buffer = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, 1024)  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    return buffer.value


def short_names_dir(tmp_path: Path) -> Path:
    """A folder on a volume that makes 8.3 names. TMP may sit on a volume with them off, so
    QMA_TEST_SHORT_NAMES_DIR can name one elsewhere."""
    for base in (tmp_path, os.environ.get("QMA_TEST_SHORT_NAMES_DIR")):
        if base:
            folder = Path(tempfile.mkdtemp(dir=base))
            (folder / "LongDirectoryName").mkdir()
            if "~" in short_path(folder / "LongDirectoryName"):
                return folder
    pytest.skip("no volume here makes 8.3 names; set QMA_TEST_SHORT_NAMES_DIR")


@pytest.mark.skipif(sys.platform != "win32", reason="8.3 names are a Windows form")
def test_real_short_names_read_as_the_long_path(tmp_path: Path) -> None:
    base = short_names_dir(tmp_path)
    login = base / ".claudehome" / ".credentials.json"
    login.parent.mkdir()
    login.write_text("{}", encoding="utf-8")
    state = base / "qmxstate"
    state.mkdir()

    def posix(path: Path) -> str:
        return normalize_path(str(path), cwd="/", home="/", case_insensitive=False)

    rules = replace(RULES, secret_paths=(posix(login),), protected_paths=(posix(state),))
    short_login, short_state = short_path(login), short_path(state)
    assert "~" in short_login
    assert "~" in short_state
    calls: list[tuple[str, dict[str, Any]]] = [
        ("Bash", {"command": f'cat "{short_login}"'}),
        ("Bash", {"command": f"cat {short_login.replace(chr(92), '/')}"}),
        ("Bash", {"command": f'echo x > "{short_state}/new.txt"'}),
        ("Read", {"file_path": short_login}),
        ("Write", {"file_path": f"{short_state}/new.txt"}),
    ]
    found = [kind(gate(tool, args, rules, cwd=str(base), agent_id=None)) for tool, args in calls]
    assert [verdict for verdict, _ in found] == ["deny"] * 5
    assert "login file" in found[0][1]
    assert "login file" in found[1][1]
    assert "QMX state" in found[2][1]
