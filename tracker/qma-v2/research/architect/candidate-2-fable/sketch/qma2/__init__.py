"""qma2: the QMA v2 agent harness. Public surface = `Harness` plus `qma2.types`.

Import rules (enforced by the import-linter contract in packet 0):
- qma2 imports no `qmx_*` and no `qma.*` package. qmx_control imports qma2, not the reverse.
- Only `qma2.engines.claude` imports `claude_agent_sdk`; only `qma2.engines.openai` imports
  `agents` (openai-agents) and `openai`.
- Nothing outside `qma2.session` imports `qma2.engines`.
- Allowed third-party at the root: pydantic, keyring, httpx, platformdirs. No LangChain.

What qmx_control injects, so qma2 stays free of its types:
- `BlockSink`: how blocks reach the UI (today `ControlService.sessions_create/append`).
- `Launcher`: how child processes start (same user by default; low-rights user optional).

Caller's view (README):

    from qma2 import Harness, BlockSink
    from qma2.types import TurnInput, ApprovalAnswer, Answer

    harness = Harness.open(home=Path("~/.qmx").expanduser(), sink=my_sink)
    await harness.start()                         # convergent: adopts threads, expires dead approvals

    thread = await harness.thread_create("Fix the README", cwd=repo)      # router picks the account
    turn = await harness.turn_start(thread.id, TurnInput("list the files and summarise README"))
    # blocks stream to the UI through `sink`; approvals show up on harness.approvals_pending()

    proof = harness.operator.verify(session_token)          # None unless the operator paired
    await harness.approval_answer(approval_id, ApprovalAnswer(Answer.ALLOW_ONCE), proof)

    preview = await harness.thread_switch(thread.id, model=openrouter_model)   # SwitchPreview
    await harness.thread_switch(thread.id, model=openrouter_model, confirm=True)

    summary = await harness.usage()                         # the usage page
    bundle = await harness.export(thread.id, out_dir)       # one action: transcript + logs
"""

from qma2.harness import BlockSink, Harness, Launcher

__all__ = ["BlockSink", "Harness", "Launcher"]
