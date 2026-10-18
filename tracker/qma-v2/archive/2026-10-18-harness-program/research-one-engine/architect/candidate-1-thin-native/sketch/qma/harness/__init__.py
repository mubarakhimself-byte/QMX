"""QMA v2 harness: Claude Code, launched by QMX, for any Anthropic-compatible provider.

Public names only. Everything else in this package is internal; an import-linter contract
fails the build when code outside `qma.harness` imports its submodules or imports
`claude_agent_sdk` at all.
"""

from qma.harness.chat import AllowAlways, AllowOnce, Answer, AnswerStatus, Answers, AskId, Quote, QuoteStale, Reject
from qma.harness.harness import Harness, NewChat
from qma.harness.home import QmxHome
from qma.harness.launch import Background, ConfigChange, Interactive
from qma.harness.profiles import ProfileName

__all__ = [
    "AllowAlways",
    "AllowOnce",
    "Answer",
    "AnswerStatus",
    "Answers",
    "AskId",
    "Background",
    "ConfigChange",
    "Harness",
    "Interactive",
    "NewChat",
    "ProfileName",
    "QmxHome",
    "Quote",
    "QuoteStale",
    "Reject",
]
