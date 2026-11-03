"""The `engine` permission policy in its AGW form (AD-60, H39, probe P-PERM). Every engine chat
names it, and the harness hands it each ask of that chat in-process, so no ask waits on a poller.

A tool the node did not declare (its `policy_args["tools"]`) is denied at once with a reason the
agent reads. An external MCP tool passes: the harness gives an engine chat only the external
servers its node names as `mcp:` toolsets (C-36). A step that declares a write tool is born in
its attempt overlay, which `policy_args["overlay"]` names: its file writes are allowed only under
that folder, and a declared
`Bash` or `PowerShell` runs, because a shell's writes cannot be bounded by path (AD-60's honest
boundary; only declared outputs ever leave the overlay). A chat with no overlay is read-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, cast

from qma.harness import AllowOnce, Answer, PolicyCall, Reject

FILE_WRITES: Final = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
SHELLS: Final = frozenset({"Bash", "PowerShell"})
WRITES: Final = FILE_WRITES | SHELLS
PATH_KEYS: Final = ("file_path", "notebook_path")
READ_ONLY: Final = (
    "{tool} is refused: steps of this workflow are read-only, so no file is written and no "
    "command runs. Answer from what you can read."
)
UNDECLARED: Final = "{tool} is refused: this step declares only {tools}. Use those."
OUTSIDE: Final = "{tool} is refused: this step writes only under its attempt folder {overlay}."


def inside(tool_input: dict[str, object], overlay: Path) -> bool:
    """Whether the path a file write names resolves under the overlay. A relative path is read
    against the overlay, the chat's working folder."""
    found = next((tool_input[key] for key in PATH_KEYS if key in tool_input), None)
    if not isinstance(found, str) or not found:
        return False
    return (overlay / found).resolve().is_relative_to(overlay.resolve())


async def engine_policy(call: PolicyCall) -> Answer:
    found = call.args.get("tools")
    declared = [str(t) for t in cast("list[object]", found)] if isinstance(found, list) else []
    overlay = call.args.get("overlay")
    external = call.tool.startswith("mcp__") and not call.tool.startswith("mcp__qmx_")
    if call.tool not in declared and not external:
        tools = ", ".join(declared) if declared else "no tools"
        return Reject(UNDECLARED.format(tool=call.tool, tools=tools))
    if call.tool in WRITES and not isinstance(overlay, str):
        return Reject(READ_ONLY.format(tool=call.tool))
    if call.tool in FILE_WRITES and not inside(call.input, Path(str(overlay))):
        return Reject(OUTSIDE.format(tool=call.tool, overlay=overlay))
    return AllowOnce()
