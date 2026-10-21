"""The `engine` permission policy in its read-only form (AD-60, H39). Every engine chat names it,
and the harness hands it each ask of that chat in-process, so no ask waits on a poller.

It allows a declared tool that cannot write and denies everything else at once with a reason the
agent reads: a tool the node did not declare (its `policy_args["tools"]`) and every tool that can
write a file or run a command. Agent steps get their overlay and declared writes in AGW.
"""

from __future__ import annotations

from typing import Final, cast

from qma.harness import AllowOnce, Answer, PolicyCall, Reject

WRITES: Final = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "PowerShell"})
READ_ONLY: Final = (
    "{tool} is refused: steps of this workflow are read-only, so no file is written and no "
    "command runs. Answer from what you can read."
)
UNDECLARED: Final = "{tool} is refused: this step declares only {tools}. Use those."


async def engine_policy(call: PolicyCall) -> Answer:
    found = call.args.get("tools")
    declared = [str(t) for t in cast("list[object]", found)] if isinstance(found, list) else []
    if call.tool in WRITES:
        return Reject(READ_ONLY.format(tool=call.tool))
    if call.tool not in declared:
        tools = ", ".join(declared) if declared else "no tools"
        return Reject(UNDECLARED.format(tool=call.tool, tools=tools))
    return AllowOnce()
