"""qma2: the QMX agent harness (package `qmx-agents/packages/qma-v2`, import name `qma2`).

Public surface (everything else is internal; see the import-linter contract below):

    from qma2 import Harness, HarnessOptions, Sink, ProposalSink, AgentOps
    from qma2 import ThreadSpec, TurnInput, Answer, Choice, SwitchTarget, Mode, Effort

Module map (control side unless marked):

    model.py      domain types; no I/O                     <- everyone
    money.py      the money rule + proposal exemption      <- policy, harness
    hooks.py      Claude-format hook runner                <- policy, harness
    policy.py     the one policy point (pure decide + evaluate)
    config.py     QMX config home, layers, materialisation for Claude
    router.py     pure whole-thread routing
    secrets.py    SecretStore backends; host_env / tool_env allow-lists
    store.py      harness.db, single writer
    operator.py   operator principal minting (qmx_control.server only)
    accounts.py   Claude status/login, ChatGPT PKCE, API-key accounts
    wire.py       control <-> host link messages
    harness.py    Harness facade, _ThreadActor, _RuleBook, _HostSupervisor
    host/         runs in the engine host process only
      __main__.py   entry; Adapter protocol (six verbs)
      link.py       host side of the link
      claude.py     ONLY importer of claude_agent_sdk
      openai.py     ONLY importer of agents / openai
      tools.py      Claude-shaped tool set for the OpenAI engine
      compact.py    OpenAI-engine compactor

Import contract (import-linter, added in unit U1; CI fails on violation):
    forbidden for qma2.*:          qmx_*, qma.*, langchain*, langgraph*, deepagents
    claude_agent_sdk only from:    qma2.host.claude
    agents, openai only from:      qma2.host.openai, qma2.host.tools
    qma2.host.* never imported by: qma2 control-side modules (process boundary)
    qma2.operator only from:       qmx_control.server
    qma2.store.Writer only from:   qma2.store
Allowed edges into qma2: qmx_control (and qmx_apps, for qma2.money only).
"""

from qma2.harness import AgentOps, Harness, HarnessError, HarnessOptions, ProposalSink, Sink
from qma2.model import (
    Answer,
    ApprovalView,
    Choice,
    Effort,
    Event,
    Mode,
    SwitchQuote,
    SwitchTarget,
    ThreadSpec,
    ThreadView,
    TurnAccepted,
    TurnInput,
    UsageReport,
)

__all__ = [
    "AgentOps", "Answer", "ApprovalView", "Choice", "Effort", "Event", "Harness",
    "HarnessError", "HarnessOptions", "Mode", "ProposalSink", "Sink", "SwitchQuote",
    "SwitchTarget", "ThreadSpec", "ThreadView", "TurnAccepted", "TurnInput", "UsageReport",
]
