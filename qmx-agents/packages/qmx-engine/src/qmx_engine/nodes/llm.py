"""The `llm` node (AD-13, SOLUTION-DESIGN 2.3): one turn on a tool-less brief in a harness
Background chat, its final text validated against the node's JSON schema.

The runner resolves the candidate at dispatch and passes it as `NodeJob.resolved_model`. The brief
puts the static prompt first and the input last, so a second chat with the same prompt can reuse
its cache (EP0 FINDINGS). An answer that fails the schema gets one repair turn in the same chat,
then the attempt fails `bad_output`, retryable, with a message that does not quote the answer, so
two failures in a row share a signature and reach the doctor. Tokens, cache reads and cache writes
come from the chat's journal rows and land on the ending event, which the span reads.

An `llm` node has no run timeout (AD-40). While its turn runs a model request is in flight, which
the stuck detector counts as progress; a request that never yields a first token is the router's
to end (AD-50).

A provider's failure text can carry a key, so every message from the harness is redacted before
it reaches the ledger or the inbox.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final

from jsonschema.validators import validator_for
from pydantic import JsonValue

from qmx_engine.admission import Admission
from qmx_engine.definition.lint import redact
from qmx_engine.nodes.base import EffectState, Failed, Look, NodeJob, NodeResult, Ok
from qmx_engine.nodes.script import failed
from qmx_engine.ports.harness_adapter import HarnessPort, Refusal, Turn
from qmx_engine.prompts import Prompt, payload, static
from qmx_engine.roles import Candidate

BAD_OUTPUT: Final = "the answer did not match the node's schema after one repair turn"
TOOL_LESS: Final = "This task has no tools. Do not call any tool; answer from this message alone."
AUTH_WORDS: Final = ("401", "unauthorized", "authentication", "invalid api key")

type JsonObject = dict[str, JsonValue]


def candidate_of(resolved: JsonObject | None) -> Candidate | str:
    """The candidate the runner resolved for this attempt, or why there is none."""
    if resolved is None:
        return "no candidate was resolved for this attempt"
    profile, model, effort = resolved.get("profile"), resolved.get("model"), resolved.get("effort")
    if not isinstance(profile, str) or not isinstance(model, str):
        why = resolved.get("unresolved")
        return why if isinstance(why, str) else "no candidate was resolved for this attempt"
    window = resolved.get("context_window")
    return Candidate(
        profile,
        model,
        effort if isinstance(effort, str) else None,
        window if isinstance(window, int) else 0,
        resolved.get("test_only") is True,
    )


def brief(prompt: str, schema: JsonObject, inputs: JsonValue, hint: str | None = None) -> str:
    return Prompt(static(prompt, [TOOL_LESS], schema), payload(inputs, hint=hint)).text


def answer(text: str | None, schema: JsonObject) -> tuple[JsonValue, str | None]:
    """The document in `text`, and None when it matches `schema`, else the first reason it does
    not."""
    if text is None:
        return None, "the turn wrote no text"
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
        body = body.rsplit("```", 1)[0]
    try:
        document: JsonValue = json.loads(body)
    except ValueError:
        return None, "the answer is not one JSON document"
    error = next(iter(validator_for(schema)(schema).iter_errors(document)), None)
    if error is not None:
        where = "/".join(str(p) for p in error.absolute_path) or "the document"
        return document, f"{where}: {error.message}"
    return document, None


@dataclass
class Usage:
    chat: str | None = None
    turns: int = 0
    tokens: dict[str, int] = field(default_factory=dict[str, int])
    cost: float | None = None
    asks_rejected: int = 0

    def add(self, turn: Turn) -> None:
        self.turns += 1
        for name, count in turn.tokens.items():
            self.tokens[name] = self.tokens.get(name, 0) + count
        if turn.cost_usd is not None:
            self.cost = (self.cost or 0.0) + turn.cost_usd
        self.asks_rejected += turn.asks_rejected

    def span(self) -> JsonObject:
        found: JsonObject = {
            "chat": self.chat,
            "turns": self.turns,
            "tokens": dict[str, JsonValue](self.tokens),
            "asks_rejected": self.asks_rejected,
        }
        if self.cost is not None:
            found["cost_estimate_usd"] = round(self.cost, 6)
        return found


def ended_badly(turn: Turn, usage: Usage) -> NodeResult | None:
    """The result of a turn that did not end with an answer, or None when it did."""
    if turn.timed_out:
        return with_span(
            failed("timeout", "the model turn ran past its time limit", retryable=True),
            usage,
            "unknown",
        )
    if turn.needs_you is None:
        return None
    reason = redact(turn.needs_you)
    if any(word in reason.lower() for word in AUTH_WORDS):
        return with_span(failed("auth", reason, retryable=False), usage)
    return with_span(failed("chat_failed", reason, retryable=True), usage)


def with_span(result: Failed, usage: Usage, effect_state: EffectState = "before") -> Failed:
    return replace(result, effect_state=effect_state, span=usage.span())


async def call(
    harness: HarnessPort,
    admission: Admission,
    candidate: Candidate,
    *,
    title: str,
    text: str,
    schema: JsonObject,
    workspace: Path,
    run_seconds: float | None = None,
    priority: int = 0,
) -> NodeResult:
    """One answer from a fresh Background chat on `candidate`, with one repair turn.
    `run_seconds` bounds only the engine's own doctor call. `priority` orders the chat's sends
    among those waiting for a harness slot."""
    held = await admission.check(candidate)
    if held is not None:
        return held
    try:
        chat = await harness.start_chat(
            title=title,
            profile=candidate.profile,
            model=candidate.model,
            effort=candidate.effort,
            workspace=workspace,
        )
    except Refusal as refusal:
        return failed("unavailable", redact(str(refusal)), retryable=False)
    return await turns(harness, admission, candidate, chat, text, schema, run_seconds, priority)


async def turns(
    harness: HarnessPort,
    admission: Admission,
    candidate: Candidate,
    chat: str,
    text: str,
    schema: JsonObject,
    run_seconds: float | None,
    priority: int,
) -> NodeResult:
    usage = Usage(chat)
    prompt = text
    for _ in range(2):
        try:
            await harness.send(chat, prompt, priority=priority)
        except Refusal as refusal:
            return await admission.refused(candidate, redact(str(refusal)))
        turn = await harness.wait_turn(chat, timeout=run_seconds)
        usage.add(turn)
        bad = ended_badly(turn, usage)
        if bad is not None:
            return bad
        document, problem = answer(turn.text, schema)
        if problem is None:
            return Ok({"main": document}, span=usage.span() | {"repaired": usage.turns > 1})
        prompt = repair(problem)
    return with_span(failed("bad_output", BAD_OUTPUT, retryable=True), usage)


def repair(problem: str) -> str:
    return (
        f"That answer does not match the JSON schema ({problem}). Reply with only the corrected "
        "JSON document."
    )


def read_ref(root: Path, parameters: JsonObject, name: str) -> str | None:
    ref = parameters.get(name)
    if not isinstance(ref, str):
        return None
    path = (root / ref).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def node_schema(root: Path, parameters: JsonObject, name: str = "schema_ref") -> JsonObject | None:
    text = read_ref(root, parameters, name)
    try:
        found: JsonValue = json.loads(text) if text is not None else None
    except ValueError:
        return None
    return found if isinstance(found, dict) else None


class Llm:
    def __init__(
        self, root: Path, harness: HarnessPort, admission: Admission, workspace: Path
    ) -> None:
        self.root = root.resolve()
        self.harness = harness
        self.admission = admission
        self.workspace = workspace
        self.running: set[str] = set()

    def look(self, key: str) -> Look:
        return Look(0, in_flight=key in self.running)

    async def run(self, job: NodeJob) -> NodeResult:
        self.running.add(job.idempotency_key)
        try:
            return await self.answer(job)
        finally:
            self.running.discard(job.idempotency_key)

    async def answer(self, job: NodeJob) -> NodeResult:
        candidate = candidate_of(job.resolved_model)
        if isinstance(candidate, str):
            return failed("unavailable", candidate, retryable=False)
        found = job.node_definition.get("parameters")
        parameters: JsonObject = found if isinstance(found, dict) else {}
        prompt = read_ref(self.root, parameters, "prompt_ref")
        schema = node_schema(self.root, parameters)
        if prompt is None or schema is None:
            message = "an llm node needs a readable prompt_ref and a JSON schema_ref"
            return failed("bad_definition", message, retryable=False)
        hint = (job.resolved_model or {}).get("hint")
        return await call(
            self.harness,
            self.admission,
            candidate,
            title=job.idempotency_key,
            text=brief(prompt, schema, job.inputs, hint if isinstance(hint, str) else None),
            schema=schema,
            workspace=self.workspace,
            priority=job.priority,
        )


class Unavailable:
    """The `llm` executor of an engine opened without a harness."""

    def run(self, job: NodeJob) -> NodeResult:
        return failed(
            "unavailable", "this engine has no harness to run model nodes", retryable=False
        )
