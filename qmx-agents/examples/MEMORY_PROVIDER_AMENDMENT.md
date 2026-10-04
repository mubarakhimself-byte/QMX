# Bounded pluggable memory projection: authorized amendment candidate

Status: implemented local increment and documentation draft for parent composition.
Authorization: the current 2026-10-04 delegation explicitly requests the Hermes-style
pluggable provider/configuration pattern. It does not select a hosted service or
admit credentials, paid calls, transcript transmission, background synchronization,
UI changes, deployment or trading. Canonical Task/Job identity remains the other
lane's contract; this increment defines no new actor/cardinality join.

## AMEND-MEMORY-2026-10-04

This scoped amendment resolves the older CT-43 / QMA AD-18 / DEC-0317 / DEC-0342
NoMemoryProvider/deferred-backend wording against the already present
JournalMemoryProvider and first-party ResearchDeskMemory implementations. Older
wording remains evidence of the earlier admission gate, not proof those concrete
adapters had production provider adoption. Under this new authorization, the
existing journal adapter is retained as the QMA authority projection for admitted
revisions and retirement evidence, and an explicitly selected registered CT-43
provider may suggest recall results through the bounded typed projection below.
This is an incremental exception for composition/verification; it does not adopt a
named external backend, ratify an in-house semantic engine or remove GAP-0072's
external-service admission gate. Parent documentation owners should reconcile this
named amendment into CT-43/decision records through their documentation process.
The legacy external-backend refusal helpers and no-provider gate behavior remain.

Memory admission confidence remains daemon-computed. The existing before-memory-
write gate controls journal admissions. Proposals cannot supply admission
confidence or grant authority. History/tombstones remain retained evidence;
retirement is not privacy erasure. Ranked recall cannot replace exact get/history,
change a canonical head, revive superseded/invalidated/expired records, disclose
foreign scope, widen grants or automatically promote global memory. Existing
seven-field namespace recipes are unchanged, including actor role/workflow pins
and research principal/application/profile/authority/source/snapshot/locators.
Request/thread IDs remain provenance, not memory grants.

## Host selection and typed boundary

An optional host-owned `memory-providers.json` file, read at agent request startup,
selects one already-loaded `register_memory_provider(desk, provider)` contribution
per desk. Nothing imports arbitrary paths, discovers/installs packages, probes the
network or chooses a default service. Use the existing plugin loader,
`PluginContext.load_config`, credential reference declarations and singleton desk
cardinality. Actual provider parameters are supplied by that plugin's operator
load config; this file contains only selection, revision and admission policy.
Credential values are never resolved by this seam.

```json
{
  "version": 1,
  "desks": {
    "research": {
      "plugin_id": "research-corpus",
      "plugin_version": "0.1.0",
      "config_revision": 1,
      "admission": "journal_projection_v1",
      "policy": {"recall": true, "injection": true}
    }
  }
}
```

This is a schema example, not an activation instruction or recommendation to use
the first-party transient provider. That provider is not automatically synchronized
with the journal, so its empty recall stays empty. Tests replace its registered
contribution with a deterministic local CT-43 fake; they seed its synthetic cache
explicitly. No production backend is selected by delivered repository defaults.
Unknown keys, duplicate JSON keys, unsupported policy, unavailable plugin/version
and missing CT-43 singleton refuse configuration. Missing configuration preserves
the inherited journal behavior; an accepted configured request never falls back
when its original binding is absent or changed.

`MemoryProjection` is the narrow typed context-selection interface required by
DurableMemory: bounded search, limits, validation and selection revalidation.
CT-43 remains the provider CRUD port. DurableMemory sends admissions to the
canonical journal adapter and uses the separately supplied projection only for
context assembly. Research retain uses canonical predecessor/history lookup, so
ranked omission cannot alter supersession. Optional LangMemExtractor still targets
canonical host source pins and emits proposals only; it is not invoked by startup
or provider callbacks.

A selected projection calls CT-43 `recall` with only the server-derived complete
namespace and a conservative bounded token budget. It receives candidates; only
full payload matches to currently active, exact-scope journal heads can be used.
Duplicate, forged, stale, tombstoned, expired, superseded and unknown candidates
are withheld. Grant/config validity is checked before and after the callback and
after context tokenization. Provider query/semantic enrichment is not added to
CT-43; configured projections refuse a query. The default journal search retains
its existing explicit local embedding behavior.

## Accepted work, effects and restart

Accepted RequestSpec snapshots add optional `memory_binding_sha256`; old journal
snapshots omit it and restore with the compatible default. The pin covers sorted
host selection, plugin version/full manifest, explicit config revision, actual
load-config bytes, credential-reference-map digest and recall/injection policy.
Live contribution identity, disposer state and those digests are rechecked on
execution, continuation, disclosure, retry and tool dispatch. Cancellation remains
available after the provider becomes unavailable. Unload or successful reload
makes the installed runtime binding unavailable; existing work cannot migrate to
replacement bytes. Reconfigure via a deliberate daemon restart. Identical pins
allow queued recovery; changed/removed selections withhold disclosure and the
existing recovery bridge records failed/context_changed for queued work.

Recall has journal-owned intent and observed receipts in existing JournalRecords,
keyed by request and complete namespace. No second journal is introduced. An
observed receipt retains only accepted journal IDs/revision digests and can be
reused after restart without redispatching the provider. Fresh use still rechecks
current heads and expiry. A lost callback/receipt stays uncertain and interrupts;
there is no silent replay/fallback or exactly-once remote-effect claim. The
receipt records the read effect class; no write/sync/extraction callback runs.
Existing invocation snapshots and operation receipts retain their own recovery
semantics. Frozen invocation content is distinguished from fresh recall.

Only explicit host recall and injection are accepted by this schema. Provider
sync, native memory mirroring, turn/session-end extraction, prefetch, compression
hooks, reflection and model-visible tools require separate host policy, current
authority and effect accounting before implementation. This seam invokes none of
those lifecycle callbacks. Provider-internal storage never becomes QMA evidence.
It does not offer live draining/rebinding, background TTL, native transcript
continuity, a user/global sharing pool or remote backend admission.

## Pattern sources and evidence

Hermes documents single-select configuration, offline availability checks and
explicit initialization context; its optional lifecycle hooks include prefetch,
sync, extraction and tool exposure. The useful pattern here is host-controlled
selection and explicit lifecycle policy, while QMX retains its own contracts.
See official [provider plugin documentation](https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin)
and [provider feature documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers).
This adaptation is an inference from those patterns, not a Hermes runtime port.

`test_memory_provider_seam.py` exercises actual daemon composition, plugin
registration, authenticated request dispatch, startup selection and restart with
fake inference/CT-43 recall. It also covers adversarial candidate filtering,
retirement/revocation during callback or tokenization, changed/removed binding
pins, cancellation after unload, configured output bounds, and disk-reopened
intent/observed receipts. The first unchanged runtime expectation failed because
the selected singleton received zero recalls before implementation. Imported
packet-5 tests retain exact namespace and lifecycle evidence. Full release gates,
production provider admission and parent shared-file composition remain separate.
