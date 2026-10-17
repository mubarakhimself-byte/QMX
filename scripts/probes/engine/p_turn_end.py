"""EP0 p_turn_end. Five Background turns of three lengths on the plan profile, each timed by three
turn-end detectors against the true end, the moment the SDK yields the turn's `ResultMessage`.

    record   the chat record's `turn` reads idle (`QmxHome.chats_dir / f"{sid}.json"`)
    block    a `text` block of this turn is in the ControlService session log
    journal  a new `model_call` row is in the chat's run journal

A detector catches a turn when it fires within the timeout and what it fired on was final: the
record and journal detectors must not fire before the true end, and the block detector's text
block must be the turn's last block. Lag is fire time minus true end; negative means early.
PASS when one detector catches 5 of 5 and its worst lag is recorded.

    p_turn_end.py
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from common import (
    TRIAGE_PLAN_MODEL,
    TURN_TIMEOUT_S,
    boot,
    log,
    plan_harness,
    result_stamps,
    run,
    workspace,
)

POLL_S = 0.05
NOTES = " ".join(
    f"Note {n}: the ledger keeps one row per event, the writer is a single thread, and replay "
    "reads the rows back in order to rebuild the run without calling any model again."
    for n in range(1, 9)
)
SHORT = ("short", "Reply with the single word OK.")
MEDIUM = ("medium", "In three short sentences, say what a run ledger is for.")
LONG = (
    "long",
    "Use the Read tool to read notes.txt in your working directory, then summarise it in about "
    "150 words.",
)
TURNS = (SHORT, MEDIUM, LONG, MEDIUM, LONG)
DETECTORS = ("record", "journal", "block")
"""In pick order: the first that catches every turn is the one EP10 should use. The block
detector is last because a text block can be followed by a tool call in the same turn."""


@dataclass
class Turn:
    label: str
    fired: dict[str, float] = field(default_factory=dict)
    fired_block: int | None = None
    last_block: int | None = None
    block_types: list[str] = field(default_factory=list)
    end: float | None = None

    def caught(self, detector: str) -> bool:
        at = self.fired.get(detector)
        if at is None or self.end is None:
            return False
        if detector == "block":
            return self.fired_block is not None and self.fired_block == self.last_block
        return at >= self.end

    def lag(self, detector: str) -> float | None:
        at = self.fired.get(detector)
        return None if at is None or self.end is None else at - self.end


async def main() -> int:
    say = log("ep0-turn-end")
    boot()
    stamps = result_stamps()
    ws = workspace("turn-end")
    (ws / "notes.txt").write_text(NOTES, encoding="utf-8")
    turns: list[Turn] = []
    async with plan_harness(say) as h:
        chat = await h.background("ep0 turn end", ws, model=TRIAGE_PLAN_MODEL)
        for label, prompt in TURNS:
            turn = Turn(label)
            mark = h.mark(chat)
            calls = len(h.journal(chat))
            ends = len(stamps)
            say(f"turn {len(turns) + 1} ({label}): {prompt}")
            await h.inject(chat, prompt)
            deadline = time.monotonic() + TURN_TIMEOUT_S
            while time.monotonic() < deadline and len(turn.fired) < len(DETECTORS):
                now = time.perf_counter()
                record = h.record(chat)
                if "record" not in turn.fired and record is not None and record.turn == "idle":
                    turn.fired["record"] = now
                if "block" not in turn.fired:
                    texts = [b for b in h.blocks(chat, mark) if b["type"] == "text"]
                    if texts:
                        turn.fired["block"] = now
                        turn.fired_block = int(texts[0]["seq"])
                if "journal" not in turn.fired and len(h.journal(chat)) > calls:
                    turn.fired["journal"] = now
                await asyncio.sleep(POLL_S)
            await h.wait_idle(chat)
            blocks = h.blocks(chat, mark)
            turn.block_types = [str(b["type"]) for b in blocks]
            turn.last_block = int(blocks[-1]["seq"]) if blocks else None
            mine = [at for sid, at in stamps[ends:] if sid == chat]
            turn.end = mine[0] if mine else None
            say(f"  blocks {turn.block_types}; true end seen: {turn.end is not None}")
            for name in DETECTORS:
                lag = turn.lag(name)
                shown = "never" if lag is None else f"{lag:+.3f} s"
                say(f"  {name}: lag {shown}, caught {turn.caught(name)}")
            turns.append(turn)
    say("summary per detector:")
    best: tuple[str, float] | None = None
    for name in DETECTORS:
        caught = sum(t.caught(name) for t in turns)
        lags = [lag for t in turns if (lag := t.lag(name)) is not None]
        worst = max(lags) if lags else None
        misses = [t.label for t in turns if not t.caught(name)]
        shown = "none" if worst is None else f"{worst:.3f} s"
        say(f"  {name}: caught {caught}/{len(turns)}, misses {misses}, worst lag {shown}")
        if best is None and caught == len(turns) and worst is not None:
            best = (name, worst)
    say.check(
        "one detector catches 5 of 5 turn ends, worst lag recorded",
        best is not None and len(turns) == len(TURNS),
        best,
    )
    if best is not None:
        say(f"PERF worst lag of the {best[0]} detector: {best[1]:.3f} s (risk for EP10 above 5 s)")
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
