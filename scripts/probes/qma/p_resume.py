"""S36: a plan chat with thinking resumes under OpenRouter. `p_resume.py` writes hp1-resume.log.

The plan turn runs in the ship home. The OpenRouter turn runs in a home with no login whose
`projects/` is a junction to the ship home's, so the CLI finds the session file by id. On
a wrong recall it compacts on the plan and asks again. With no OpenRouter key it stops
before any plan turn.
"""

from __future__ import annotations

import _winapi
import asyncio
import os
import secrets
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Final

from common import (
    CONFIG_DIR,
    HP1_EVIDENCE,
    SCRATCH,
    Log,
    bundled_cli,
    plan_options,
    read_key,
    require_plan_login,
    run_turns,
    scrub_process_env,
)
from p_providers import PROVIDERS, THINKING, capped_env, ledger
from spend import Ledger, guarded_turns

if TYPE_CHECKING:
    from claude_agent_sdk import Message, ResultMessage

RESUME_HOME: Final = SCRATCH / "hp1" / "resume" / "claude"


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


def recall_verdict(answer: str | None, word: str) -> str:
    return "PASS" if answer and word in answer else "FAIL"


async def recall(
    log: Log, spend: Ledger, env: dict[str, str], session: str, word: str
) -> tuple[str, str]:
    result = last_result(
        await guarded_turns(
            spend,
            log,
            "S36 recall",
            plan_options(env=env, model="sonnet", resume=session, max_turns=2),
            ["What was the codeword I gave you earlier? Reply with the codeword only."],
        )
    )
    detail = (
        f"is_error={result.is_error} status={result.api_error_status} {str(result.result)[:200]}"
    )
    return recall_verdict(result.result, word), detail


async def main_async(log: Log) -> int:
    log(f"scrubbed from this process: {scrub_process_env(os.environ)}")
    openrouter = PROVIDERS["openrouter"]
    secret = read_key(openrouter)
    if secret is None:
        log.row("S36 plan to OpenRouter resume", "keyring qmx/openrouter empty", "BLOCKED NO KEY")
        return 0
    log.redact(secret)
    spend = ledger(openrouter, secret)
    if spend is None:
        log.row("S36 plan to OpenRouter resume", "no prices pinned for the spend guard", "BLOCKED")
        return 0
    require_plan_login(log, bundled_cli())

    word = f"persimmon-{secrets.token_hex(3)}"
    start = last_result(
        await run_turns(
            log,
            plan_options(thinking=THINKING, max_turns=2),
            [f"Remember this codeword for later: {word}. Think briefly, then reply only: noted."],
        )
    )
    session = start.session_id
    log(f"plan session {session}")

    home = linked_home(RESUME_HOME, CONFIG_DIR / "projects")
    env = capped_env(openrouter, secret, home)
    verdict, detail = await recall(log, spend, env, session, word)
    log.row("S36 plan to OpenRouter resume, recall", detail, verdict)
    if verdict == "PASS":
        return 0

    compacted = last_result(
        await run_turns(log, plan_options(resume=session, max_turns=2), ["/compact"])
    )
    log(f"compact on the plan: is_error={compacted.is_error} session {compacted.session_id}")
    verdict, detail = await recall(log, spend, env, compacted.session_id, word)
    log.row("S36 plan to OpenRouter resume, recall after /compact", detail, verdict)
    return 0


def main() -> int:
    return asyncio.run(main_async(Log("hp1-resume", HP1_EVIDENCE)))


if __name__ == "__main__":
    raise SystemExit(main())
