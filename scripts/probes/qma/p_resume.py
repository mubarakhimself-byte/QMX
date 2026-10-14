"""S36: a plan chat with signed thinking resumes under OpenRouter. Writes hp1-resume.log.

`p_resume.py --budget USD` runs one thinking plan turn in the ship home, then resumes the
same session id under OpenRouter from a home with no login whose `projects/` is a junction
to the ship home's, so the CLI finds the session file by id. Both checks read that session
file: the plan turn must have written a signed thinking block, or the row is UNMEASURED and
no OpenRouter turn runs, and the recall is the last reply text in it. On a wrong recall it
compacts on the plan and asks again. With no OpenRouter key it stops before any plan turn.
"""

from __future__ import annotations

import _winapi
import argparse
import asyncio
import json
import os
import secrets
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from common import (
    CONFIG_DIR,
    HP1_EVIDENCE,
    SCRATCH,
    Lockdown,
    Log,
    bundled_cli,
    plan_options,
    read_key,
    require_plan_login,
    run_turns,
    scrub_process_env,
)
from p_providers import PROVIDERS, Budget, add_budget, budget_from, capped_env, ledger
from spend import Ledger, guarded_turns

if TYPE_CHECKING:
    from claude_agent_sdk import Message, ResultMessage

RESUME_HOME: Final = SCRATCH / "hp1" / "resume" / "claude"
PLAN_THINKING: Final = {"type": "enabled", "budget_tokens": 2048}
NO_TOOLS: Final = Lockdown()


def linked_home(root: Path, projects: Path) -> Path:
    link = root / "projects"
    if link.is_junction():
        link.rmdir()
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    projects.mkdir(parents=True, exist_ok=True)
    _winapi.CreateJunction(str(projects), str(link))
    return root


def last_result(messages: list[Message]) -> ResultMessage:
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    return [m for m in messages if isinstance(m, ResultMessage)][-1]


def transcript(session: str) -> list[str]:
    paths = sorted((CONFIG_DIR / "projects").glob(f"*/{session}.jsonl"))
    return paths[0].read_text(encoding="utf-8").splitlines() if paths else []


def assistant_blocks(lines: Iterable[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for line in lines:
        try:
            entry: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "assistant":
            blocks += entry.get("message", {}).get("content", [])
    return blocks


def signed_thinking(lines: Iterable[str]) -> int:
    return sum(
        b.get("type") == "thinking" and bool(b.get("signature")) for b in assistant_blocks(lines)
    )


def final_text(lines: Iterable[str]) -> str | None:
    """The last non-blank reply text. DeepSeek can close a turn with thinking and a blank text."""
    texts = [str(b.get("text", "")) for b in assistant_blocks(lines) if b.get("type") == "text"]
    replies = [text for text in texts if text.strip()]
    return replies[-1] if replies else None


def s36_verdict(plan: list[str], after: list[str], word: str) -> str:
    """OQ9 asks about a transcript with thinking signatures, so none means unmeasured."""
    if not signed_thinking(plan):
        return "UNMEASURED"
    answer = final_text(after)
    return "PASS" if answer and word in answer else "FAIL"


async def recall(log: Log, spend: Ledger, env: dict[str, str], session: str) -> str:
    result = last_result(
        await guarded_turns(
            spend,
            log,
            "S36 recall",
            plan_options(NO_TOOLS, env=env, model="sonnet", resume=session, max_turns=2),
            ["What was the codeword I gave you earlier? Reply with the codeword only."],
        )
    )
    log(f"recall is_error={result.is_error} status={result.api_error_status}")
    return result.session_id


async def main_async(log: Log, budget: Budget) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    openrouter = PROVIDERS["openrouter"]
    secret = read_key(openrouter)
    if secret is None:
        log.row("S36 plan to OpenRouter resume", "keyring qmx/openrouter empty", "BLOCKED NO KEY")
        return 0
    log.redact(secret)
    spend = ledger(openrouter, secret, budget)
    if spend is None:
        log.row("S36 plan to OpenRouter resume", "no prices pinned for the spend guard", "BLOCKED")
        return 0
    require_plan_login(log, bundled_cli())

    word = f"persimmon-{secrets.token_hex(3)}"
    start = last_result(
        await run_turns(
            log,
            plan_options(
                NO_TOOLS, model="sonnet", thinking=PLAN_THINKING, effort="max", max_turns=1
            ),
            [
                f"Remember this codeword for later: {word}. Before you reply, work out which "
                "is larger, 37 x 43 or 39 x 41. Then reply only: noted."
            ],
        )
    )
    session = start.session_id
    plan = transcript(session)
    signed = signed_thinking(plan)
    log(f"plan session {session}: {signed} signed thinking blocks in its transcript")
    if not signed:
        log.row(
            "S36 plan to OpenRouter resume", "the plan turn wrote no signed thinking", "UNMEASURED"
        )
        return 0

    home = linked_home(RESUME_HOME, CONFIG_DIR / "projects")
    env = capped_env(openrouter, secret, home)
    after = transcript(await recall(log, spend, env, session))
    verdict = s36_verdict(plan, after, word)
    detail = (
        f"{signed} signed thinking blocks before the switch; last reply {final_text(after)!r:.200}"
    )
    log.row("S36 plan to OpenRouter resume, recall", detail, verdict)
    if verdict == "PASS":
        return 0

    compacted = last_result(
        await run_turns(
            log, plan_options(NO_TOOLS, model="sonnet", resume=session, max_turns=2), ["/compact"]
        )
    )
    log(f"compact on the plan: is_error={compacted.is_error} session {compacted.session_id}")
    after = transcript(await recall(log, spend, env, compacted.session_id))
    log.row(
        "S36 plan to OpenRouter resume, recall after /compact",
        f"last reply {final_text(after)!r:.200}",
        s36_verdict(plan, after, word),
    )
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="p_resume.py")
    add_budget(parser)
    budget = budget_from(parser, parser.parse_args(argv[1:]))
    return asyncio.run(main_async(Log("hp1-resume", HP1_EVIDENCE), budget))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
