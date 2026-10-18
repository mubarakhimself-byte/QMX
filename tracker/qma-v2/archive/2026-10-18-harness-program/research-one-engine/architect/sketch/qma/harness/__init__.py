"""QMA v2 harness: Claude Code, launched by QMX, for any Anthropic-compatible provider.

Public names only. Everything else in this package is internal; an import-linter contract
fails the build when code outside `qma.harness` imports its submodules or imports
`claude_agent_sdk` at all.

Entry points import it after `qma.boot` has scrubbed the environment (see `qma.serve`).
`TestMode` is public only so check scripts under `scripts/live/` can build one; a CI grep
allows `TestMode(` nowhere else.
"""

from qma.harness.chat import (
    AllowAlways,
    AllowOnce,
    Answer,
    AnswerStatus,
    Answers,
    AskId,
    InjectedText,
    OperatorText,
    Quote,
    QuoteStale,
    Reject,
    UntrustedPrompt,
)
from qma.harness.harness import ChatTableFull, Harness, NewChat
from qma.harness.home import QmxHome
from qma.harness.launch import Background, ConfigChange, Interactive, TestMode
from qma.harness.profiles import ProfileName
from qma.harness.usage import UsagePage

__all__ = [
    "AllowAlways",
    "AllowOnce",
    "Answer",
    "AnswerStatus",
    "Answers",
    "AskId",
    "Background",
    "ChatTableFull",
    "ConfigChange",
    "Harness",
    "InjectedText",
    "Interactive",
    "NewChat",
    "OperatorText",
    "ProfileName",
    "QmxHome",
    "Quote",
    "QuoteStale",
    "Reject",
    "TestMode",
    "UntrustedPrompt",
    "UsagePage",
]
