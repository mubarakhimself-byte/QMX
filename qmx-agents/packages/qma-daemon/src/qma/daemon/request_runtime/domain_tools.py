"""Host-bound real read operations over retained knowledge snapshots.

The model can select a locator within an explicit host allowlist. It cannot
select a source, live filesystem root, session, grant or invocation target.
This first binding browses existing CorpusSnapshot metadata, not citation
creation or arbitrary file retrieval.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import cast

from qma.core.operations import public_operation_descriptors
from qma.daemon.knowledge.service import KnowledgeService
from qma.wire.invocation_envelope import ContributionRecord, InstanceRecord
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input

from .contracts import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
)
from .providers import ProviderError
from .service import RequestRuntime
from .tool_loop import LoopLimits, ToolBinding, ToolLoopProvider


def create_research_browse_binding(
    knowledge: KnowledgeService,
    *,
    source_id: str,
    snapshot_ref: str,
    allowed_locators: tuple[str, ...],
    contribution: ContributionRecord,
    instance: InstanceRecord,
    grant_id: str,
) -> ToolBinding:
    """Pin existing source bytes and fail closed on any host manifest mismatch.

    ``snapshot_ref`` must come from trusted configuration, not the requesting
    model. Restart over a changed corpus fails rather than silently retargeting
    a persisted request. Contribution/instance/grant are resolved per session
    by the host before installation, then independently checked at dispatch.
    """
    if not source_id.strip() or not snapshot_ref.strip() or not allowed_locators:
        raise ValueError("research browse requires explicit source, snapshot and locators")
    if len(set(allowed_locators)) != len(allowed_locators) or len(allowed_locators) > 64:
        raise ValueError("research browse locator list must be unique and bounded")
    snapped = knowledge.snapshot(source_id)
    if is_refusal(snapped) or snapped.value.id != snapshot_ref:
        raise ValueError("configured research snapshot is unavailable or changed")
    snapshot = snapped.value
    if any(locator not in snapshot.file_digests for locator in allowed_locators):
        raise ValueError("configured locator is outside the pinned snapshot")
    descriptor = next(
        item
        for item in public_operation_descriptors()
        if item.op_id == "qml.research.browse" and item.version == 1
    )
    permitted = frozenset(allowed_locators)

    def browse(arguments: Mapping[str, object]) -> Mapping[str, object]:
        if arguments.get("snapshot_ref") != snapshot.id:
            raise ProviderError("tool_denied", "Research browse snapshot is outside host scope")
        locator = arguments.get("locator")
        if locator is not None and (not isinstance(locator, str) or locator not in permitted):
            raise ProviderError("tool_denied", "Research browse locator is outside host scope")
        chain = knowledge.supersedes_chain(source_id)
        if is_refusal(chain) or snapshot.id not in chain.value:
            raise ProviderError("tool_denied", "Pinned research snapshot is unavailable")
        selected = (locator,) if isinstance(locator, str) else tuple(sorted(permitted))
        return {
            "source_id": source_id,
            "snapshot_ref": snapshot.id,
            "items": [
                {"locator": path, "content_fp1": snapshot.file_digests[path]} for path in selected
            ],
        }

    return ToolBinding(
        descriptor,
        contribution,
        instance,
        grant_id,
        browse,
        (("snapshot_ref", snapshot.id), ("locator", tuple(sorted(permitted)))),
    )


# The daemon supplies current target metadata; grants are never an availability
# source. This resolver is called for every execution, not cached globally.
TargetResolver = Callable[[str], Result[tuple[ContributionRecord, InstanceRecord]]]


class _SessionScopedTools:
    def __init__(
        self,
        runtime: RequestRuntime,
        provider: ProviderAdapter,
        profile_tools: Mapping[str, frozenset[str]],
        knowledge: KnowledgeService,
        source_id: str,
        snapshot_ref: str,
        allowed_locators: tuple[str, ...],
        target_resolver: TargetResolver,
        now: Callable[[], str],
    ) -> None:
        self.runtime = runtime
        self.provider = provider
        self.profile_tools = dict(profile_tools)
        self.knowledge = knowledge
        self.source_id = source_id
        self.snapshot_ref = snapshot_ref
        self.allowed_locators = allowed_locators
        self.target_resolver = target_resolver
        self.now = now
        self.capabilities = ProviderCapabilities(provider.capabilities.provider_id)

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        loaded = self.runtime.get(request.request_id)
        if is_refusal(loaded):
            raise ProviderError("tool_denied", "Request is not bound to host authority")
        spec = loaded.value.spec
        if not self.profile_tools.get(spec.profile.profile_id):
            active = self.runtime.validate_active_request(request.request_id, now=self.now())
            if is_refusal(active):
                raise ProviderError("context_changed", "Active request scope forbids disclosure")
            return self.provider.execute(request, emit, cancellation)
        target = self.target_resolver(spec.product_session_id)
        records = self.runtime.product_sessions.granted_records(spec.product_session_id)
        if is_refusal(target) or is_refusal(records):
            raise ProviderError("tool_denied", "Current operation target is unavailable")
        contribution, instance = target.value
        grants = [
            grant
            for grant in records.value
            if grant.op_id == "qml.research.browse"
            and grant.op_version == 1
            and grant.contribution.qualified_id == contribution.qualified_id
            and grant.contribution.package_version == contribution.package_version
            and grant.instance_id == instance.instance_id
            and grant.config_revision == instance.config_revision
        ]
        if len(grants) != 1:
            raise ProviderError("tool_denied", "Exactly one matching session grant is required")
        try:
            binding = create_research_browse_binding(
                self.knowledge,
                source_id=self.source_id,
                snapshot_ref=self.snapshot_ref,
                allowed_locators=self.allowed_locators,
                contribution=contribution,
                instance=instance,
                grant_id=grants[0].grant_id,
            )
        except ValueError as exc:
            raise ProviderError("tool_denied", "Configured corpus pin is unavailable") from exc
        original_execute = binding.execute

        def current_read(arguments: Mapping[str, object]) -> Mapping[str, object]:
            current = self.target_resolver(spec.product_session_id)
            if is_refusal(current) or current.value != target.value:
                raise ProviderError("tool_denied", "Current target changed before dispatch")
            return original_execute(arguments)

        binding = replace(binding, execute=current_read)
        loop = ToolLoopProvider(
            self.provider,
            provider_id=self.capabilities.provider_id,
            tools={"research_browse": binding},
            profile_tools=self.profile_tools,
            now=self.now,
            limits=LoopLimits(max_model_calls=2, max_tool_calls=1),
        )
        loop.bind_runtime(self.runtime)
        return loop.execute(request, emit, cancellation)


def bind_daemon_tool_providers(
    runtime: RequestRuntime,
    providers: Mapping[str, ProviderAdapter],
    profile_tools: Mapping[str, frozenset[str]],
    research_browse: Mapping[str, object],
    knowledge: KnowledgeService,
    *,
    target_resolver: TargetResolver,
    now: Callable[[], str],
) -> Result[Mapping[str, ProviderAdapter]]:
    """Install one trusted operation family while retaining configured identities.

    The provider identity must already hash this host manifest at configuration
    loading. No mutable global grant is captured: each active request selects its
    own existing session grant and current independently resolved target.
    """
    if any(names - {"research_browse"} for names in profile_tools.values()):
        return invalid_input("tools", "only installed research_browse is supported")
    if any(
        provider.capabilities.native_tools or provider.capabilities.resume
        for provider in providers.values()
    ):
        return invalid_input("providers", "daemon tools require text-only fresh-turn providers")
    if not any(profile_tools.values()):
        return Ok(
            {
                name: _SessionScopedTools(
                    runtime, provider, profile_tools, knowledge, "", "", (), target_resolver, now
                )
                for name, provider in providers.items()
            }
        )
    source = research_browse.get("source_id")
    snapshot = research_browse.get("snapshot_ref")
    locators = research_browse.get("allowed_locators")
    if (
        not isinstance(source, str)
        or not isinstance(snapshot, str)
        or not isinstance(locators, (list, tuple))
    ):
        return invalid_input(
            "research_browse", "explicit source, snapshot and locator list required"
        )
    raw = cast("Sequence[object]", locators)
    if any(not isinstance(item, str) for item in raw):
        return invalid_input("allowed_locators", "locators must be strings")
    allowed = tuple(cast("str", item) for item in raw)
    if not source.strip() or not snapshot.strip() or not allowed:
        return invalid_input("research_browse", "empty corpus scope is forbidden")
    return Ok(
        {
            name: _SessionScopedTools(
                runtime,
                provider,
                profile_tools,
                knowledge,
                source,
                snapshot,
                allowed,
                target_resolver,
                now,
            )
            for name, provider in providers.items()
        }
    )
