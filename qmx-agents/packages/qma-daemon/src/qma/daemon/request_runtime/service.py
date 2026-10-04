"""Single daemon owner for durable interactive requests.

Request snapshots are events on AuthoritativeJournal, not a second grant store.
Provider events are observations only; they cannot authorize effects. A restart
never replays a running turn automatically. One runtime must own a daemon journal.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import threading
import uuid
from collections.abc import Callable, Mapping
from dataclasses import asdict, replace
from typing import Any, cast

from qma.core.vocabulary.enums import GrantEvaluationMoment
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.sessions.grant_binding import BoundSessionGrant
from qma.daemon.sessions.product_session import ProductSessionService
from qma.wire.invocation_envelope import parse_invocation_envelope
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

from .contracts import (
    CopilotProfile,
    ProviderAdapter,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestRecord,
    RequestSpec,
    RequestStatus,
)


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonnegative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _duration(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _valid_optional_model(value: object) -> bool:
    return value is None or isinstance(value, str)


def _valid_profile(value: object) -> bool:
    return isinstance(value, CopilotProfile)


def _provider_result(value: object) -> ProviderResult:
    if not isinstance(value, ProviderResult):
        raise TypeError("provider returned an invalid result")
    return value


def _spec_hash(spec: RequestSpec) -> str:
    body = asdict(spec)
    body["timeout_seconds"] = str(float(spec.timeout_seconds))
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _key(spec: RequestSpec) -> tuple[str, str, str]:
    return spec.principal, spec.product_session_id, spec.idempotency_key


def _conversation(spec: RequestSpec) -> str:
    # The behavior, authority revision, provider and model must all match.
    body = asdict(spec)
    for field in ("idempotency_key", "prompt", "timeout_seconds"):
        body.pop(field)
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _journal_payload(value: object) -> object:
    """Canonical journal values omit optional fields rather than encode null."""
    if isinstance(value, dict):
        mapped = cast("dict[str, object]", value)
        return {key: _journal_payload(item) for key, item in mapped.items() if item is not None}
    if isinstance(value, list):
        return [_journal_payload(item) for item in cast("list[object]", value)]
    return value


class RequestRuntime:
    """Synchronous provider driver with durable acceptance and explicit recovery.

    submit/get/cancel are safe from other threads during execute. Adapters must
    honor timeout and cancellation. Cancellation intent never overwrites an
    observed completed outcome; accepted tool effects may finish. Provider calls
    and host tool callbacks run outside the runtime lock.
    """

    def __init__(
        self,
        *,
        journal: AuthoritativeJournal,
        product_sessions: ProductSessionService,
        providers: Mapping[str, ProviderAdapter],
        provider_workspace: str = "",
    ) -> None:
        self.journal = journal
        self.product_sessions = product_sessions
        self.providers = dict(providers)
        self.provider_workspace = provider_workspace
        self._lock = threading.RLock()
        self._records: dict[str, RequestRecord] = {}
        self._keys: dict[tuple[str, str, str], str] = {}
        self._tokens: dict[str, threading.Event] = {}
        self._active_conversations: set[str] = set()
        self._frozen_requests: set[str] = set()
        self._restored = False

    def _persist(self, record: RequestRecord) -> Result[RequestRecord]:
        body = asdict(record)
        # The canonical journal refuses binary float identity values. Store the
        # finite duration as decimal text and restore it at the adapter boundary.
        body["spec"]["timeout_seconds"] = str(float(record.spec.timeout_seconds))
        payload = cast("dict[str, object]", _journal_payload(body))
        appended = self.journal.append_event("agent_request.snapshot", payload=payload)
        if is_refusal(appended):
            return appended
        saved = replace(record, journal_seq=appended.value.record.journal_seq)
        self._records[saved.request_id] = saved
        self._keys[_key(saved.spec)] = saved.request_id
        return Ok(saved)

    def restore(self) -> Result[tuple[RequestRecord, ...]]:
        """Fold snapshots and mark lost running owners interrupted exactly once."""
        with self._lock:
            if self._tokens:
                return policy_rejection("request_runtime", "cannot restore while a turn is active")
            if self._restored:
                return Ok(tuple(self._records.values()))
            events = self.journal.read_events()
            if is_refusal(events):
                return events
            records: dict[str, RequestRecord] = {}
            try:
                for event in events.value:
                    if event.event != "agent_request.snapshot":
                        continue
                    body = dict(event.payload)
                    spec_body = dict(cast("Mapping[str, object]", body["spec"]))
                    spec_body["timeout_seconds"] = float(cast("str", spec_body["timeout_seconds"]))
                    spec_body["profile"] = CopilotProfile(**cast("Any", spec_body["profile"]))
                    body["spec"] = RequestSpec(**cast("Any", spec_body))
                    if body.get("result") is not None:
                        body["result"] = ProviderResult(**cast("Any", body["result"]))
                    body["journal_seq"] = event.journal_seq
                    record = RequestRecord(**cast("Any", body))
                    records[record.request_id] = record
            except (TypeError, ValueError, KeyError) as exc:
                return storage_failure(
                    "invalid durable request snapshot", context={"error": type(exc).__name__}
                )
            self._records = records
            self._keys = {_key(row.spec): row.request_id for row in records.values()}
            for row in tuple(records.values()):
                if row.status in {"running", "cancellation_requested"}:
                    interrupted = self._persist(
                        replace(row, status="interrupted", error="owner_lost")
                    )
                    if is_refusal(interrupted):
                        return interrupted
            self._restored = True
            return Ok(tuple(self._records.values()))

    def _ensure_restored(self) -> Result[None]:
        if self._restored:
            return Ok(None)
        restored = self.restore()
        if is_refusal(restored):
            return restored
        return Ok(None)

    def _bound(self, spec: RequestSpec, expected: str | None = None) -> Result[str]:
        loaded = self.product_sessions.get(spec.product_session_id)
        if is_refusal(loaded):
            return loaded
        session = loaded.value
        if session.principal != spec.principal or session.context_revision != spec.context_revision:
            return policy_rejection(
                "request_context", "principal or context revision does not match session"
            )
        if (
            spec.profile.role != "global"
            and session.app_instance_id != spec.profile.app_instance_id
        ):
            return policy_rejection(
                "request_profile", "profile app does not match the bound session"
            )
        hydrated = self.product_sessions.granted_records(spec.product_session_id)
        if is_refusal(hydrated):
            return hydrated
        context = {
            "context": dict(session.context.to_payload()),
            "profile": session.profile.value,
            "app_instance_id": session.app_instance_id,
            "selected_refs": [dict(ref.to_payload()) for ref in session.selected_refs],
            "granted_ops": list(session.granted_ops),
            "revoked_grants": sorted(
                {
                    revocation.grant_id
                    for revocation in self.product_sessions.ledger.revocations
                    if revocation.grant_id in session.granted_ops
                }
            ),
        }
        binding = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
        if expected is not None and binding != expected:
            return policy_rejection(
                "request_context", "bound session context changed after request acceptance"
            )
        return Ok(binding)

    def submit(self, spec: RequestSpec) -> Result[RequestRecord]:
        with self._lock:
            restored = self._ensure_restored()
            if is_refusal(restored):
                return restored
            if not all(
                _nonempty_text(v)
                for v in (
                    spec.idempotency_key,
                    spec.principal,
                    spec.product_session_id,
                    spec.prompt,
                    spec.provider_id,
                )
            ):
                return invalid_input(
                    "request", "request identity, prompt and provider must be nonempty strings"
                )
            if not _nonnegative_integer(spec.context_revision):
                return invalid_input("context_revision", "expected a nonnegative integer")
            if not _valid_profile(spec.profile) or not _valid_optional_model(spec.model):
                return invalid_input(
                    "request", "profile and optional model must match the request contract"
                )
            if not _duration(spec.timeout_seconds):
                return invalid_input("timeout_seconds", "expected a positive finite duration")
            prior_id = self._keys.get(_key(spec))
            if prior_id is not None:
                prior = self._records[prior_id]
                if _spec_hash(prior.spec) != _spec_hash(spec):
                    return policy_rejection(
                        "idempotency_key", "key already accepted with different request content"
                    )
                return Ok(prior)
            bound = self._bound(spec)
            if is_refusal(bound):
                return bound
            return self._persist(
                RequestRecord(
                    request_id="req:" + uuid.uuid4().hex, spec=spec, context_binding=bound.value
                )
            )

    def get(self, request_id: str) -> Result[RequestRecord]:
        with self._lock:
            restored = self._ensure_restored()
            if is_refusal(restored):
                return restored
            row = self._records.get(request_id)
            if row is None:
                return invalid_input("request_id", "unknown request")
            return Ok(row)

    def execute(
        self, request_id: str, *, observe: Callable[[ProviderEvent], None] | None = None
    ) -> Result[RequestRecord]:
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if row.status in {"completed", "cancelled", "failed"}:
                return Ok(row)
            if row.status != "queued":
                return policy_rejection(
                    "request_state",
                    "only queued requests execute; interrupted turns need explicit retry",
                )
            bound = self._bound(row.spec, row.context_binding)
            if is_refusal(bound):
                return bound
            provider = self.providers.get(row.spec.provider_id)
            if provider is None:
                return policy_rejection(
                    "provider", "requested provider is not configured; no fallback is automatic"
                )
            if (
                provider.capabilities.provider_id != row.spec.provider_id
                or provider.capabilities.native_tools
            ):
                return policy_rejection(
                    "provider", "provider must match identity and deny native tool execution"
                )
            conversation = _conversation(row.spec)
            if conversation in self._active_conversations:
                return policy_rejection("conversation", "another turn owns this conversation")
            # Native transcripts can retain context after a grant revocation
            # without a context_revision change. A resume capability alone does
            # not establish an authorized handoff. Every turn starts fresh until
            # the host can construct and audit that canonical handoff.
            thread_id = None
            running = self._persist(
                replace(row, status="running", attempt=row.attempt + 1, error=None)
            )
            if is_refusal(running):
                return running
            token = threading.Event()
            self._tokens[request_id] = token
            self._active_conversations.add(conversation)

        def emit(event: ProviderEvent) -> None:
            # UI observers cannot change provider outcome or grant authority.
            if observe is not None:
                with contextlib.suppress(Exception):
                    observe(event)

        result: ProviderResult | None = None
        error: str | None = None
        status: RequestStatus = "completed"
        try:
            result = provider.execute(
                ProviderRequest(
                    prompt=row.spec.prompt,
                    model=row.spec.model,
                    cwd=self.provider_workspace,
                    thread_id=thread_id,
                    timeout_seconds=row.spec.timeout_seconds,
                    instructions=row.spec.profile.instructions,
                    request_id=request_id,
                ),
                emit,
                token,
            )
            result = _provider_result(result)
        except Exception as exc:
            code = getattr(exc, "code", None)
            status = (
                "interrupted"
                if code in {"outcome_unknown", "scope_interrupt"}
                else "cancelled"
                if code == "cancelled"
                else "failed"
            )
            error = code if isinstance(code, str) else type(exc).__name__
        with self._lock:
            try:
                current = self._records[request_id]
                if request_id in self._frozen_requests:
                    # The daemon already recorded lost ownership before closing
                    # its journal. A late provider return cannot write afterward.
                    return Ok(current)
                return self._persist(replace(current, status=status, result=result, error=error))
            finally:
                self._tokens.pop(request_id, None)
                self._active_conversations.discard(conversation)

    def validate_active_request(
        self, request_id: str, *, now: object = None
    ) -> Result[RequestRecord]:
        """Admit each model continuation before sending prompt or observations.

        A fresh native thread alone cannot protect data from an earlier tool
        after authority narrows. The caller must validate immediately before
        every model dispatch and stop on refusal. Already-dispatched work may
        finish; this seam admits no new dispatch after cancellation or retarget.
        """
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            token = self._tokens.get(request_id)
            if row.status != "running" or token is None or token.is_set():
                return policy_rejection(
                    "request_state", "model continuation requires an active uncancelled turn"
                )
            return self.validate_request_context(request_id, now=now)

    def validate_request_context(
        self, request_id: str, *, now: object = None
    ) -> Result[RequestRecord]:
        """Revalidate retained disclosure against current session authority."""
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            bound = self._bound(row.spec, row.context_binding)
            if is_refusal(bound):
                return bound
            session = self.product_sessions.get(row.spec.product_session_id)
            if is_refusal(session):
                return session
            if session.value.granted_ops and now is None:
                return invalid_input(
                    "now", "continuation of granted context requires the host clock"
                )
            for grant_id in session.value.granted_ops:
                # A continuation is new disclosure, even when a previous tool
                # was accepted. It receives no already-accepted-work exemption.
                evaluated = self.product_sessions.ledger.evaluate(
                    grant_id=grant_id, moment=GrantEvaluationMoment.DISPATCH, now=now
                )
                if is_refusal(evaluated):
                    return evaluated
            return Ok(row)

    def interrupt_active_request(self, request_id: str) -> Result[RequestRecord]:
        """Host shutdown boundary: stop new effects and freeze late completions.

        This records unknown outcome rather than asserting cancellation. Call it
        before closing the journal when a cooperative provider did not stop.
        """
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            token = self._tokens.get(request_id)
            if token is not None:
                token.set()
            self._frozen_requests.add(request_id)
            if row.status in {"running", "cancellation_requested"}:
                return self._persist(replace(row, status="interrupted", error="daemon_shutdown"))
            return Ok(row)

    def fail_queued_request(self, request_id: str) -> Result[RequestRecord]:
        """Host admission failure before dispatch is a known terminal outcome."""
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if row.status != "queued":
                return policy_rejection(
                    "request_state", "only an undispatched request can fail admission"
                )
            return self._persist(replace(row, status="failed", error="context_changed"))

    def cancel(self, request_id: str) -> Result[RequestRecord]:
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if row.status in {"completed", "failed", "cancelled", "interrupted"}:
                return Ok(row)
            status: RequestStatus = (
                "cancelled" if row.status == "queued" else "cancellation_requested"
            )
            saved = self._persist(replace(row, status=status))
            if not is_refusal(saved) and request_id in self._tokens:
                self._tokens[request_id].set()
            return saved

    def retry_interrupted(self, request_id: str) -> Result[RequestRecord]:
        """Explicit consent to a new turn; unknown prior execution may incur cost."""
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if row.status != "interrupted":
                return policy_rejection(
                    "request_state", "only interrupted turns use explicit retry"
                )
            bound = self._bound(row.spec, row.context_binding)
            if is_refusal(bound):
                return bound
            return self._persist(replace(row, status="queued", result=None, error=None))

    def dispatch_tool(self, request_id: str, **kwargs: object) -> Result[BoundSessionGrant]:
        """Host-only seam: grants/envelopes remain owned by ProductSessionService.

        The bounded ToolLoopProvider resolves model tool intents through this
        host seam. It cannot supply another session or bypass the established
        grant evaluator. Native provider tools remain disabled.
        """
        with self._lock:
            loaded = self.get(request_id)
            if is_refusal(loaded):
                return loaded
            row = loaded.value
            if row.status != "running":
                return policy_rejection("request_state", "tool dispatch requires an active turn")
            token = self._tokens.get(request_id)
            if token is None or token.is_set():
                return policy_rejection(
                    "request_state", "cancelled or ownerless turn cannot dispatch a tool"
                )
            bound = self._bound(row.spec, row.context_binding)
            if is_refusal(bound):
                return bound
            if any(
                name in kwargs
                for name in (
                    "product_session_id",
                    "caller_product_session_id",
                    "parent_permissions",
                    "union_grants",
                )
            ):
                return policy_rejection("tool_scope", "request cannot retarget or widen authority")
            envelope = parse_invocation_envelope(kwargs.get("envelope"))
            if is_refusal(envelope):
                return envelope
            if (
                envelope.value.caller_session_ref is not None
                or envelope.value.callee_session_ref is not None
            ):
                return policy_rejection("tool_scope", "cross-session tool dispatch is not enabled")
            dispatch = cast(
                "Callable[..., Result[BoundSessionGrant]]",
                self.product_sessions.dispatch_public_call,
            )
            session_id = row.spec.product_session_id
        # Grant acceptance is the existing dispatcher's boundary. Work accepted
        # there may finish even if cancellation intent arrives during execution.
        # Keep the request lock free so that cancel/query remain responsive.
        return dispatch(session_id, **kwargs)
