"""EP0 p_background. One Background chat on the plan profile, on the `triage` role's first plan
model, with `Background` imported from `qma.harness.launch` (EP0 runs before HG1 exports it).
One `InjectedText` turn. PASS when the reply arrives and the chat record's kind is background.

    p_background.py
"""

from __future__ import annotations

import json

from common import TRIAGE_PLAN_MODEL, boot, log, plan_harness, run, text_of, workspace


async def main() -> int:
    say = log("ep0-background")
    boot()
    async with plan_harness(say) as h:
        chat = await h.background(
            "ep0 background", workspace("background"), model=TRIAGE_PLAN_MODEL
        )
        mark = h.mark(chat)
        await h.inject(chat, "Reply with the single word PONG.")
        record = await h.wait_idle(chat)
        replies = text_of(h.blocks(chat, mark))
        say(f"reply text blocks: {replies}")
        raw = json.loads((h.home.chats_dir / f"{chat}.json").read_text(encoding="utf-8"))
        kind = raw["config"]["kind"]
        say(f"record file {h.home.chats_dir / f'{chat}.json'} kind={kind} turn={record.turn}")
        say.check("the reply arrived", any("PONG" in t for t in replies), replies)
        say.check("the record's kind is background", kind == {"type": "background"}, kind)
        calls = h.journal(chat)
        say(f"model_call rows: {calls}")
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
