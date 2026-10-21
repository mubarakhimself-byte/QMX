"""P-SYS (AD-62, H46, H53; SOLUTION-DESIGN 28.8 as trimmed by review 48 L10). Long system text
through `--append-system-prompt-file`, and what a relaunch by resume shows the model.

- size: a 60,000-character methodology through `--append-system-prompt-file` on Windows. The
  launch passes and the model follows a rule at the end of the file: it answers `PROBE-PING`
  with that file's probe word, exactly.
- cache: the second turn reads the text from cache. PASS when turn 2's cache read is at least
  90 % of turn 1's whole prompt (cache read plus cache write plus input).
- resume: with `snapshot: false`, change the append text, relaunch by resume, and the model
  answers with the new probe word; with `snapshot` omitted it answers with the old one. Turn 1
  never sends `PROBE-PING`, so neither word is in the history.

Every launch uses the Surface's preset: `claude_code` with `exclude_dynamic_sections: true`.

Size fail: slots keep within the command-line check and spill to skills. Resume fail: a slot
change starts a fresh chat seeded with the session recap (SURF reads this row).

    <venv>/Scripts/python.exe p_sys.py
"""

from __future__ import annotations

import asyncio
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Final

from common import (
    PLAN_MODEL,
    Case,
    Log,
    Verdict,
    fresh,
    lane_lock,
    plan_env,
    scrub_process_env,
    ship_settings_hash,
    turn,
)

METHODOLOGY_CHARS: Final = 60_000
CACHE_SHARE: Final = 0.9
SIZE_FALLBACK: Final = "slots keep within the command-line check and spill to skills"
RESUME_FALLBACK: Final = "a slot change starts a fresh chat seeded with the session recap"
PING: Final = "PROBE-PING"
"""The model is told in the append what to answer to this, so the check reads an instruction it
followed, not a request to reveal its system text (which haiku refuses)."""


def rule(codeword: str) -> str:
    return (
        f"When the user writes {PING}, reply with exactly the probe word {codeword} and "
        "nothing else.\n"
    )


def answered(reply: str, codeword: str) -> bool:
    return reply.strip().strip(".`'\"*").strip() == codeword


def methodology(codeword: str) -> str:
    step = (
        "Step {n}. Read the pod's last three backtests, compare the drawdown against the "
        "admission bar, and note in one line whether the regime tag still holds.\n"
    )
    body: list[str] = []
    n = 1
    tail = rule(codeword)
    while sum(map(len, body)) + len(tail) < METHODOLOGY_CHARS:
        body.append(step.format(n=n))
        n += 1
    text = "".join(body)
    return text[: METHODOLOGY_CHARS - len(tail)] + tail


def prompt_tokens(usage: dict[str, int]) -> int:
    return usage["cache_read"] + usage["cache_write"] + usage["input"]


def verdict(observation: dict[str, Any]) -> Verdict:
    size, resume = observation["size"], observation["resume"]
    first, second = size["turn1"], size["turn2"]
    fresh_text, kept_text = resume["snapshot_false"], resume["snapshot_omitted"]
    cases = (
        Case(
            f"a {size['chars']}-character append file launches and reaches the model",
            size["launched"] and answered(size["reply1"], size["codeword"]),
            {"launched": size["launched"], "reply": size["reply1"], "codeword": size["codeword"]},
        ),
        Case(
            "the second turn reads the text from cache",
            second["cache_read"] >= CACHE_SHARE * prompt_tokens(first),
            {"turn1": first, "turn2": second, "needed": CACHE_SHARE * prompt_tokens(first)},
        ),
        Case(
            "snapshot false: after a resume the model quotes the new append",
            answered(fresh_text["reply"], fresh_text["new"]),
            fresh_text,
        ),
        Case(
            "snapshot omitted: after a resume the model quotes the old append",
            answered(kept_text["reply"], kept_text["old"]),
            kept_text,
        ),
    )
    resume_failed = not (cases[2].ok and cases[3].ok)
    size_failed = not (cases[0].ok and cases[1].ok)
    fallback = "; ".join(
        text
        for failed, text in ((size_failed, SIZE_FALLBACK), (resume_failed, RESUME_FALLBACK))
        if failed
    )
    return Verdict("P-SYS", cases, fallback or SIZE_FALLBACK)


def options(slug: str, cwd: Path, append_file: Path, *, snapshot: bool | None, **more: Any) -> Any:
    from claude_agent_sdk import ClaudeAgentOptions  # noqa: PLC0415

    system: dict[str, Any] = {
        "type": "preset",
        "preset": "claude_code",
        "exclude_dynamic_sections": True,
    }
    if snapshot is not None:
        system["snapshot"] = snapshot
    return ClaudeAgentOptions(
        env=plan_env(slug),
        cwd=str(cwd),
        model=PLAN_MODEL,
        setting_sources=[],
        strict_mcp_config=True,
        tools=[],
        system_prompt=system,  # type: ignore[arg-type]
        extra_args={"append-system-prompt-file": append_file.as_posix()},
        **more,
    )


def usage_of(seen: Any) -> dict[str, int]:
    return {
        "cache_read": int(seen.usage.get("cache_read_input_tokens") or 0),
        "cache_write": int(seen.usage.get("cache_creation_input_tokens") or 0),
        "input": int(seen.usage.get("input_tokens") or 0),
        "model_turns": int(seen.num_turns),
    }


async def size_case(say: Log) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    root = fresh("sys-size")
    codeword = f"SIZE-{secrets.token_hex(4).upper()}"
    append = root / "methodology.md"
    append.write_text(methodology(codeword), encoding="utf-8")
    chars = len(append.read_text(encoding="utf-8"))
    say(f"[size] {chars} characters in {append}, codeword {codeword}")
    found: dict[str, Any] = {"chars": chars, "codeword": codeword, "launched": False}
    async with ClaudeSDKClient(options("sys-size", root, append, snapshot=False)) as client:
        found["launched"] = True
        one = await turn(client, PING, say)
        two = await turn(client, "Reply with the single word OK.", say)
    found |= {"reply1": one.text(), "turn1": usage_of(one), "turn2": usage_of(two)}
    say(f"[size] {found}")
    return found


async def resume_case(say: Log, *, snapshot: bool | None) -> dict[str, Any]:
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    label = "snapshot_false" if snapshot is False else "snapshot_omitted"
    root = fresh(f"sys-{label}")
    old, new = f"OLD-{secrets.token_hex(3).upper()}", f"NEW-{secrets.token_hex(3).upper()}"
    append = root / "slot.md"
    append.write_text(rule(old), encoding="utf-8")
    async with ClaudeSDKClient(options(f"sys-{label}", root, append, snapshot=snapshot)) as client:
        first = await turn(client, "Reply with the single word OK.", say)
    append.write_text(rule(new), encoding="utf-8")
    resumed = options(f"sys-{label}", root, append, snapshot=snapshot, resume=first.session_id)
    async with ClaudeSDKClient(resumed) as client:
        second = await turn(client, PING, say)
    found = {
        "old": old,
        "new": new,
        "reply": second.text(),
        "session": first.session_id,
        "resumed_session": second.session_id,
        "model_turns": first.num_turns + second.num_turns,
    }
    say(f"[resume {label}] {found}")
    return found


async def run(say: Log) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "size": await size_case(say),
        "resume": {
            "snapshot_false": await resume_case(say, snapshot=False),
            "snapshot_omitted": await resume_case(say, snapshot=None),
        },
    }
    observation["plan_turns"] = (
        observation["size"]["turn1"]["model_turns"]
        + observation["size"]["turn2"]["model_turns"]
        + sum(row["model_turns"] for row in observation["resume"].values())
    )
    return observation


def main() -> int:
    removed = scrub_process_env(os.environ)
    say = Log("prb-h-sys")
    say(f"scrubbed {len(removed)} names from the process env (names only)")
    before = ship_settings_hash()
    say(f"ship settings.toml sha256 before {before}")
    with lane_lock(say):
        say("lane lock taken")
        observation = asyncio.run(run(say))
    after = ship_settings_hash()
    say(f"ship settings.toml sha256 after {after}, unchanged={before == after}")
    say(f"haiku plan model turns: {observation['plan_turns']}")
    say.save(observation)
    return say.verdict(verdict(observation))


if __name__ == "__main__":
    sys.exit(main())
