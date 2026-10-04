"""Authenticated daemon admission and bounded background request ownership.

This bridge is called after paired CT-40 authentication and negotiation. Policies
come from operator configuration; renderer input never creates a provider or grant.
"""

from __future__ import annotations

import math
import queue
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.sessions.product_session import ProductSession
from qma.wire.agent_request import (
    AGENT_REQUEST_CAPABILITIES,
    AgentRequestReference,
    SubmitAgentRequest,
)
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

from .contracts import CopilotProfile, RequestRecord, RequestSpec
from .service import RequestRuntime


def _integer(value: object, maximum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 < value <= maximum


def _task_binding(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _duration(value: object, maximum: int) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 < value <= maximum
    )


@dataclass(frozen=True, slots=True)
class AgentRequestPolicy:
    profile: CopilotProfile
    authority_profile: Literal["authoring", "app-use"]
    provider_id: str
    model: str | None = None
    timeout_seconds: float = 120
    max_prompt_bytes: int = 32768
    session_app_instance_id: str | None = None
    authoring_task_id: str | None = None

    def __post_init__(self) -> None:
        if self.authority_profile not in {"authoring", "app-use"} or not self.provider_id:
            raise ValueError("explicit authority profile and configured provider are required")
        if not _duration(self.timeout_seconds, 600) or not _integer(self.max_prompt_bytes, 262144):
            raise ValueError("request policy budgets are outside supported bounds")
        if self.profile.role in {"application", "page"} and self.session_app_instance_id not in {
            None,
            self.profile.app_instance_id,
        }:
            raise ValueError("behavior and session instance bindings must agree")
        if self.authority_profile == "app-use" and not self.bound_instance:
            raise ValueError("app-use policy requires an exact host instance binding")
        if self.authoring_task_id is not None and (
            self.authority_profile != "authoring" or not _task_binding(self.authoring_task_id)
        ):
            raise ValueError("experiment authoring requires an explicit authoring Task binding")

    @property
    def bound_instance(self) -> str | None:
        return self.session_app_instance_id or self.profile.app_instance_id


def request_receipt(row: RequestRecord, *, disclose_result: bool = False) -> Mapping[str, object]:
    """Do not echo prompts, host instructions or provider credentials over CT-40."""
    body: dict[str, object] = {
        "request_id": row.request_id,
        "product_session_ref": row.spec.product_session_id,
        "status": row.status,
        "attempt": row.attempt,
        "journal_seq": row.journal_seq,
    }
    if row.error is not None:
        body["error"] = row.error
    if disclose_result and row.result is not None:
        body["content"] = row.result.content
    return body


def _conversation(spec: RequestSpec) -> tuple[str, str, CopilotProfile, str, str | None, int]:
    return (
        spec.principal,
        spec.product_session_id,
        spec.profile,
        spec.provider_id,
        spec.model,
        spec.context_revision,
    )


class AgentRequestBridge:
    """One bounded daemon worker queue using the existing journal/runtime.

    Workers are daemon threads rather than ThreadPoolExecutor's exit-joined
    threads. Shutdown waits only the configured interval, then records unknown
    ownership and freezes late provider writes before the daemon closes its store.
    """

    def __init__(
        self,
        *,
        runtime: RequestRuntime,
        policies: Mapping[str, AgentRequestPolicy],
        now: Callable[[], str],
        max_workers: int = 2,
        max_inflight: int = 16,
        shutdown_timeout_seconds: float = 2,
    ) -> None:
        if (
            not _integer(max_workers, 8)
            or not _integer(max_inflight, 64)
            or max_inflight < max_workers
        ):
            raise ValueError("background execution limits are invalid")
        if not _duration(shutdown_timeout_seconds, 10):
            raise ValueError("shutdown interval is invalid")
        if not policies or any(
            key != policy.profile.profile_id for key, policy in policies.items()
        ):
            raise ValueError("host policies must be keyed by exact profile id")
        if any(policy.provider_id not in runtime.providers for policy in policies.values()):
            raise ValueError("every policy requires an explicitly configured provider")
        restored = runtime.restore()
        if is_refusal(restored):
            raise ValueError("durable request state could not be restored")
        self.runtime = runtime
        self.policies = dict(policies)
        self.now = now
        self.max_inflight = max_inflight
        self.shutdown_timeout_seconds = shutdown_timeout_seconds
        self._condition = threading.Condition(threading.RLock())
        self._queue: queue.Queue[str] = queue.Queue(maxsize=max_inflight)
        self._jobs: set[str] = set()
        self._backlog: list[str] = []
        self._active: set[str] = set()
        self._active_conversations: set[tuple[str, str, CopilotProfile, str, str | None, int]] = (
            set()
        )
        self._closed = False
        self._ready = threading.Event()
        self._keys = {
            (
                row.spec.principal,
                row.spec.product_session_id,
                row.spec.idempotency_key,
            ): row.request_id
            for row in restored.value
        }
        self._workers = tuple(
            threading.Thread(target=self._work, name=f"qma-agent-request-{n}", daemon=True)
            for n in range(max_workers)
        )
        for row in sorted(restored.value, key=lambda item: item.journal_seq):
            if row.status != "queued":
                continue
            admitted = self._owned(
                AgentRequestReference(row.request_id, row.spec.product_session_id),
                PrincipalClass.OPERATOR,
            )
            if is_refusal(admitted):
                runtime.fail_queued_request(row.request_id)
            else:
                self._backlog.append(row.request_id)
        self._refill()
        try:
            for worker in self._workers:
                worker.start()
        except RuntimeError, OSError:
            with self._condition:
                self._closed = True
                self._ready.set()
                self._condition.notify_all()
            for worker in self._workers:
                if worker.ident is not None:
                    worker.join(timeout=0.2)
            raise ValueError("background worker startup failed") from None
        self._ready.set()

    @property
    def capabilities(self) -> Mapping[str, object]:
        return dict.fromkeys(AGENT_REQUEST_CAPABILITIES, True)

    def _refill(self) -> None:
        """Move only known undispatched journal entries into bounded execution."""
        while self._backlog and len(self._jobs) < self.max_inflight and not self._closed:
            request_id = self._backlog.pop(0)
            self._jobs.add(request_id)
            self._queue.put_nowait(request_id)

    def _session(self, session_ref: str, principal: PrincipalClass) -> Result[ProductSession]:
        if principal is not PrincipalClass.OPERATOR:
            return policy_rejection("principal_class", "agent requests require the paired operator")
        loaded = self.runtime.product_sessions.get(session_ref)
        if is_refusal(loaded):
            return loaded
        if loaded.value.principal != principal.value:
            return policy_rejection(
                "product_session", "authenticated principal does not own this session"
            )
        return loaded

    def _policy(self, session: ProductSession, profile_id: str) -> Result[AgentRequestPolicy]:
        policy = self.policies.get(profile_id)
        if policy is None:
            return policy_rejection("profile_id", "profile is not in the host catalog")
        if (
            session.profile.value != policy.authority_profile
            or session.app_instance_id != policy.bound_instance
        ):
            return policy_rejection(
                "profile_id", "host profile does not match session authority and instance"
            )
        return Ok(policy)

    def submit(
        self, params: SubmitAgentRequest, *, principal: PrincipalClass
    ) -> Result[Mapping[str, object]]:
        with self._condition:
            if self._closed:
                return policy_rejection("agent_requests", "daemon request admission is closed")
            session = self._session(params.product_session_ref, principal)
            if is_refusal(session):
                return session
            policy = self._policy(session.value, params.profile_id)
            if is_refusal(policy):
                return policy
            config = policy.value
            if len(params.prompt.encode("utf-8")) > config.max_prompt_bytes:
                return invalid_input("prompt", "prompt exceeds the host profile byte budget")
            key = principal.value, params.product_session_ref, params.idempotency_key
            prior_id = self._keys.get(key)
            if self._backlog and prior_id is None:
                return policy_rejection("agent_requests", "durable recovery backlog is draining")
            if (
                len(self._jobs) >= self.max_inflight
                and prior_id not in self._jobs
                and prior_id not in self._backlog
            ):
                if prior_id is None:
                    return policy_rejection("agent_requests", "bounded background queue is full")
                prior = self.runtime.get(prior_id)
                if is_refusal(prior):
                    return prior
                if prior.value.status == "queued":
                    return policy_rejection("agent_requests", "bounded background queue is full")
            accepted = self.runtime.submit(
                RequestSpec(
                    idempotency_key=params.idempotency_key,
                    principal=principal.value,
                    product_session_id=params.product_session_ref,
                    context_revision=session.value.context_revision,
                    profile=config.profile,
                    prompt=params.prompt,
                    provider_id=config.provider_id,
                    model=config.model,
                    timeout_seconds=config.timeout_seconds,
                    authoring_task_id=config.authoring_task_id,
                )
            )
            if is_refusal(accepted):
                return accepted
            row = accepted.value
            disclosure = self.runtime.validate_request_context(row.request_id, now=self.now())
            if is_refusal(disclosure):
                failed = self.runtime.fail_queued_request(row.request_id)
                if is_refusal(failed):
                    return disclosure
                return Ok(request_receipt(failed.value))
            self._keys[key] = row.request_id
            if (
                row.status == "queued"
                and row.request_id not in self._jobs
                and row.request_id not in self._backlog
            ):
                self._jobs.add(row.request_id)
                self._queue.put_nowait(row.request_id)
            return Ok(request_receipt(row))

    def _owned(
        self, params: AgentRequestReference, principal: PrincipalClass, *, disclosure: bool = True
    ) -> Result[RequestRecord]:
        session = self._session(params.product_session_ref, principal)
        if is_refusal(session):
            return session
        loaded = self.runtime.get(params.request_id)
        if is_refusal(loaded):
            return loaded
        row = loaded.value
        if (
            row.spec.product_session_id != params.product_session_ref
            or row.spec.principal != principal.value
        ):
            return policy_rejection(
                "request_id", "request does not belong to this principal and session"
            )
        if not disclosure:
            # Stopping owned work does not require retaining its former grants,
            # provider configuration or disclosure permission.
            return Ok(row)
        policy = self._policy(session.value, row.spec.profile.profile_id)
        if is_refusal(policy):
            return policy
        if (
            policy.value.profile,
            policy.value.provider_id,
            policy.value.model,
            policy.value.timeout_seconds,
            policy.value.authoring_task_id,
        ) != (
            row.spec.profile,
            row.spec.provider_id,
            row.spec.model,
            row.spec.timeout_seconds,
            row.spec.authoring_task_id,
        ):
            return policy_rejection(
                "request_id", "accepted host policy differs from current configuration"
            )
        return self.runtime.validate_request_context(row.request_id, now=self.now())

    def get(
        self, params: AgentRequestReference, *, principal: PrincipalClass
    ) -> Result[Mapping[str, object]]:
        owned = self._owned(params, principal, disclosure=False)
        if is_refusal(owned):
            return owned
        disclosure = self._owned(params, principal)
        if is_refusal(disclosure):
            receipt = dict(request_receipt(owned.value))
            receipt["content_withheld"] = True
            receipt["disclosure_error"] = "context_changed"
            return Ok(receipt)
        from .actor_workflow import activity_receipts  # noqa: PLC0415

        body = dict(request_receipt(disclosure.value, disclose_result=True))
        activities = activity_receipts(self.runtime, params.request_id)
        if activities:
            body["activities"] = activities
        if self.runtime.canonical_projection is not None:
            projected = self.runtime.canonical_projection(disclosure.value)
            if is_refusal(projected):
                return projected
            if projected.value is not None:
                body["canonical_join"] = projected.value
        return Ok(body)

    def cancel(
        self, params: AgentRequestReference, *, principal: PrincipalClass
    ) -> Result[Mapping[str, object]]:
        owned = self._owned(params, principal, disclosure=False)
        if is_refusal(owned):
            return owned
        if params.activity_id is not None:
            from .actor_workflow import activity_receipts  # noqa: PLC0415

            activities = activity_receipts(self.runtime, params.request_id)
            child = next(
                (item for item in activities if item["activity_id"] == params.activity_id), None
            )
            if child is None:
                return invalid_input("activity_id", "activity does not belong to this owned job")
            if child["status"] in {"completed", "cancelled", "failed", "not_started"}:
                return Ok({"activity_id": params.activity_id, "status": child["status"]})
        cancelled = self.runtime.cancel(owned.value.request_id)
        if is_refusal(cancelled):
            return cancelled
        return Ok(request_receipt(cancelled.value))

    def resume(
        self, params: AgentRequestReference, *, principal: PrincipalClass
    ) -> Result[Mapping[str, object]]:
        """Explicit retry of an owned interrupted graph, never a scope expansion."""
        with self._condition:
            if self._closed or self._backlog or len(self._jobs) >= self.max_inflight:
                return policy_rejection("agent_requests", "bounded request queue unavailable")
            owned = self._owned(params, principal)
            if is_refusal(owned):
                return owned
            active = self.runtime.validate_request_context(params.request_id, now=self.now())
            if is_refusal(active):
                return active
            queued = self.runtime.retry_interrupted(params.request_id)
            if is_refusal(queued):
                return queued
            self._jobs.add(params.request_id)
            self._queue.put_nowait(params.request_id)
            return Ok(request_receipt(queued.value))

    def _work(self) -> None:
        self._ready.wait()
        while True:
            with self._condition:
                if self._closed:
                    return
            try:
                request_id = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            with self._condition:
                if self._closed:
                    return
                loaded = self.runtime.get(request_id)
                if is_refusal(loaded):
                    self._jobs.discard(request_id)
                    self._refill()
                    self._queue.task_done()
                    continue
                conversation = _conversation(loaded.value.spec)
                older_pending = False
                for pending_id in self._jobs:
                    pending = self.runtime.get(pending_id)
                    if (
                        not is_refusal(pending)
                        and pending.value.status == "queued"
                        and pending.value.journal_seq < loaded.value.journal_seq
                        and _conversation(pending.value.spec) == conversation
                    ):
                        older_pending = True
                        break
                if conversation in self._active_conversations or older_pending:
                    # Preserve durable acceptance while an earlier turn owns
                    # this context, including queued turns rotated by workers.
                    self._queue.put_nowait(request_id)
                    self._queue.task_done()
                    self._condition.wait(timeout=0.05)
                    continue
                self._active.add(request_id)
                self._active_conversations.add(conversation)
            try:
                admitted = self.runtime.validate_request_context(request_id, now=self.now())
                if not is_refusal(admitted):
                    self.runtime.execute(request_id)
                else:
                    self.runtime.fail_queued_request(request_id)
            except Exception:
                current = self.runtime.get(request_id)
                if not is_refusal(current) and current.value.status == "queued":
                    self.runtime.fail_queued_request(request_id)
                else:
                    self.runtime.interrupt_active_request(request_id)
            finally:
                with self._condition:
                    self._active.discard(request_id)
                    self._active_conversations.discard(conversation)
                    self._jobs.discard(request_id)
                    self._refill()
                    self._condition.notify_all()
                self._queue.task_done()

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            jobs = (*self._jobs, *self._backlog)
        for request_id in jobs:
            self.runtime.cancel(request_id)
        deadline = time.monotonic() + self.shutdown_timeout_seconds
        with self._condition:
            while self._active and time.monotonic() < deadline:
                self._condition.wait(timeout=max(0, deadline - time.monotonic()))
            for request_id in tuple(self._active):
                self.runtime.interrupt_active_request(request_id)
            self._jobs.clear()
            self._backlog.clear()
