"""Compaction for the OpenAI engine (H11). The Claude engine compacts natively.

Remote where the route offers it (OpenAI API key: responses.compact; ChatGPT route
UNVERIFIED, probed in U8), otherwise local: Codex's SUMMARIZATION_PROMPT and
SUMMARY_PREFIX, keep recent user messages, then re-inject what Claude re-injects after a
compaction (project context, memory head, recently read files, invoked skills, each
skill capped at 5,000 tokens).

The host computes the summary; the control side commits it (Store.archive_items in one
transaction: older items inactive, summary item inserted). Pre/PostCompact hooks fire
through the link. Running a compaction twice is safe: the second sees nothing above the
threshold and returns without a model call.
"""

from __future__ import annotations

from dataclasses import dataclass

from qma2.host.link import Link


@dataclass(frozen=True, slots=True)
class CompactPlan:
    upto_seq: int
    keep_user_messages: int
    focus: str | None
    trigger: str  # manual | auto


class Compactor:
    def __init__(self, link: Link, threshold: float, window_tokens: int) -> None:
        raise NotImplementedError

    async def maybe_compact(self, last_input_tokens: int) -> bool:
        """Auto trigger at threshold x window, checked before each run (never mid-request)."""
        raise NotImplementedError

    async def compact(self, plan: CompactPlan) -> None:
        """# TODO pseudocode
        # out = await link.hook(Compact(phase="pre", trigger, focus)); honour block
        # summary = remote_compact() if supported else local_summary(items, focus)
        # await link.emit("compacted", data={upto_seq, summary, reinjected})   # control commits
        # PostCompact fires on the control side when it sees `compacted`
        """
        raise NotImplementedError
