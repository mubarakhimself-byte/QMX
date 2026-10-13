"""New file qmx_control/agent_ops.py: the harness's OPERATIONS rows and the ports qma2 needs.

Boundary discipline: each route method parses its body into qma2 domain types and calls
exactly one Harness method. No harness logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict

from qma2 import Answer, ApprovalView, Harness, SwitchQuote, ThreadView, TurnAccepted, UsageReport
from qma2.harness import AgentOps, ProposalSink, Sink
from qma2.model import AgentPath, Block, JsonValue, OperatorProof, ThreadId
from qma2.money import OrderProposal

from .server_changes import Op, Who

HARNESS_OPERATIONS: tuple[Op, ...] = (
    # threads
    Op("threads_create", "POST", "/api/threads", False),
    Op("threads_list", "GET", "/api/threads", False),
    Op("threads_get", "GET", "/api/threads/{thread_id}", False),
    Op("threads_send", "POST", "/api/threads/{thread_id}/turns", True),
    Op("threads_steer", "POST", "/api/threads/{thread_id}/steer", True),
    Op("threads_interrupt", "POST", "/api/threads/{thread_id}/interrupt", True),
    Op("threads_compact", "POST", "/api/threads/{thread_id}/compact", False),
    Op("threads_fork", "POST", "/api/threads/{thread_id}/fork", False),
    Op("threads_archive", "POST", "/api/threads/{thread_id}/archive", True),
    Op("threads_export", "POST", "/api/threads/{thread_id}/export", False, Who.OPERATOR),
    Op("threads_set_mode", "PUT", "/api/threads/{thread_id}/mode", True, Who.OPERATOR),
    Op("threads_quote_switch", "POST", "/api/threads/{thread_id}/switch/quote", False, Who.OPERATOR),
    Op("threads_switch", "POST", "/api/threads/{thread_id}/switch", True, Who.OPERATOR),
    # approvals
    Op("approvals_list", "GET", "/api/approvals", False),
    Op("approvals_answer", "POST", "/api/approvals/{approval_id}", True, Who.OPERATOR),
    # accounts and usage
    Op("accounts_list", "GET", "/api/accounts", False),
    Op("accounts_claude_status", "GET", "/api/accounts/claude", False),
    Op("accounts_put_api_key", "PUT", "/api/accounts/api-key", True, Who.OPERATOR),
    Op("accounts_chatgpt_begin", "POST", "/api/accounts/chatgpt", True, Who.OPERATOR),
    Op("accounts_disable", "POST", "/api/accounts/{account_id}/disable", True, Who.OPERATOR),
    Op("usage_report", "GET", "/api/usage", False),
    Op("rules_list", "GET", "/api/rules", False),
    Op("rules_delete", "DELETE", "/api/rules/{rule_id}", True, Who.OPERATOR),
)


class SendBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    client_turn_id: str


class AnswerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    choice: str
    message: str | None = None
    edited_input: dict[str, JsonValue] | None = None
    rule_text: str | None = None
    answers: dict[str, JsonValue] | None = None

    def to_answer(self) -> Answer:
        raise NotImplementedError


class AgentOpsRoutes:
    """Bound by create_app exactly like ControlService methods (method name == op name)."""

    def __init__(self, harness: Harness) -> None:
        self.harness = harness

    async def threads_send(self, thread_id: str, body: SendBody) -> TurnAccepted:
        raise NotImplementedError

    async def approvals_answer(self, approval_id: str, body: AnswerBody, proof: OperatorProof) -> ApprovalView:
        raise NotImplementedError

    async def threads_quote_switch(self, thread_id: str, body: Mapping[str, JsonValue], proof: OperatorProof) -> SwitchQuote:
        raise NotImplementedError

    async def threads_switch(self, thread_id: str, body: Mapping[str, JsonValue], proof: OperatorProof) -> ThreadView:
        """body carries the quote id; the harness re-validates epoch and expiry."""
        raise NotImplementedError

    async def usage_report(self) -> UsageReport:
        raise NotImplementedError

    # ... one method per HARNESS_OPERATIONS row, each a parse + one harness call


class ControlSink(Sink):
    """qma2.Sink over ControlService. Sync SQLite calls run in asyncio.to_thread so the
    event loop never blocks (fixes the copilot's sync-in-async trap)."""

    async def create_session(self, title: str, origin: str, parent: ThreadId | None) -> ThreadId:
        raise NotImplementedError

    async def block(self, session: ThreadId, block: Block) -> None:
        raise NotImplementedError

    async def topic(self, topic: str, subject: str, data: Mapping[str, JsonValue]) -> None:
        raise NotImplementedError


class BrokerProposals(ProposalSink):
    """Writes an unsigned proposal through qmx_broker (portfolio_proposals shows it).
    Signing stays the operator's, through Portfolio; nothing here can send an order."""

    async def propose(self, proposal: OrderProposal, thread: ThreadId, agent_path: AgentPath) -> Mapping[str, JsonValue]:
        raise NotImplementedError


class ControlAgentOps(AgentOps):
    """QMX ops as agent tools: rows with who=ANY, minus sessions_append of the reserved
    `permission` kind (the console renders approvals only from the approvals table, so a
    forged permission block is inert, but agents have no reason to write one)."""

    def catalog(self) -> Sequence[Mapping[str, JsonValue]]:
        raise NotImplementedError

    async def call(self, name: str, args: Mapping[str, JsonValue], thread: ThreadId, agent_path: AgentPath) -> JsonValue:
        raise NotImplementedError
