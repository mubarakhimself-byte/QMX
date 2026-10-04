# Hermes memory provider pattern: bounded QMX fit

Evaluation and integration recommendation, not a ratified contract or executable
provider-selection change. The user authorized the Hermes pattern of pluggable
providers/configuration; no particular backend, service, credential, automatic
extraction, new default or Hermes runtime is activated by this packet.

## Reference observations

Hermes selects one external memory provider through configuration. Its provider
interface includes availability, configuration and lifecycle callbacks; discovery
does not import every provider or install packages, and availability checks are
offline. Explicit session/agent context is passed to initialization.
[Memory Provider Plugins](https://hermes-agent.nousresearch.com/docs/developer-guide/memory-provider-plugin)

Activation can inject prompt context, prefetch, sync turns, extract at session end,
mirror native memory writes and expose tools. These are separate behaviors whose
authority and effect boundaries must be evaluated individually in QMX.
[Memory Providers](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers)

Hermes documents additive plugin APIs, keyword-compatible callbacks, persisted
schema migration/replay and isolated plugin testing. These compatibility ideas
fit incremental adaptation. Its full agent/transport API is a separate surface.
[Build a Hermes Plugin](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins),
[Programmatic Integration](https://hermes-agent.nousresearch.com/docs/developer-guide/programmatic-integration)

## Existing QMX seams and gaps

| Existing seam | Fit / constraint |
| --- | --- |
| Core `ports/memory.py` CT-43 `MemoryProvider` | Reuse the typed port and admitted candidate vocabulary. Hermes' callback/tool interface is not a drop-in implementation of exact typed get/history/retirement semantics. Do not add a second competing provider ABC. |
| Core `plugins/context.py` `PluginContext` | Already exposes operator-principal `load_config`, credential references and `register_memory_provider(desk, provider)`. Reuse this public plugin route rather than arbitrary module imports or a separate provider discovery system. |
| Daemon `plugins/context.py` | Registers a singleton MemoryProvider contribution per desk. This registration alone does not prove RequestRuntime consumes it or that provider admission has passed. |
| Daemon `memory/admission.py` | `MemoryProviderRegistry` enforces one binding per desk; the gate owns write-hook admission and confidence. No-memory/staged behavior and explicit external-backend refusal remain current contract constraints. Hermes' one-external-provider rule does not change QMX desk cardinality. |
| `request_runtime/durable_memory.py` | `DurableMemory` accepts the concrete `JournalMemoryProvider`, and selection/projection uses journal-specific capabilities. This is not already a generic runtime provider seam. |
| `request_runtime/scoped_memory.py`, `actor_workflow.py`, `memory_extraction.py` | Existing research/actor composition constructs or consumes that concrete adapter. These shared files need integration-owner composition work before configurable recall can be claimed. Only the bounded legacy TTL check in scoped_memory.py changes here. |

The conclusions below are QMX recommendations inferred from those reference
patterns and the inspected code, not claims that QMX already implements them.

## Incremental integration recommendation

1. Keep selection in trusted host/plugin composition. A future versioned load
   configuration should identify the admitted plugin/provider version and
   non-secret parameters/credential references using the existing plugin route.
   Profiles, skills, recalled text and client requests must not select a provider,
   namespace, import path or authority. No automatic install, availability network
   probe, fallback backend or default change is implied.
2. Resolve and freeze the admitted binding/configuration revision for accepted
   work. The integration lane should define draining, unload/disposer behavior
   and restart handling before any rebind; unfinished work must not silently move
   to a new provider or lose its authority context. Canonical actor/Task join and
   Task/Job cardinality stay with that lane.
3. Preserve all current scope inputs and byte-compatible namespace recipes.
   Build the complete namespace from granted server context, revalidate current
   grants on each continuation and refuse absent/incompatible bindings. Session
   titles, inferred OS user, behavior profiles and provider-returned metadata are
   provenance or content, not identity grants. Global sharing requires an explicit
   future host-admitted policy.
4. Preserve QMA journal admission, retirement heads and observed effect receipts
   as authoritative. A semantic provider may propose candidates or project only
   authorized active memory with journal/source/revision traceability. Ranked
   recall must not substitute for exact get/history or override a tombstone,
   deadline, supersession, revocation or uncertain effect. A backend unable to
   meet CT-43 must remain unavailable or be behind an explicitly amended port.
5. Adapt the concrete DurableMemory composition only after resolving the current
   CT-43/DEC-0317/DEC-0342 admission-provenance discrepancy. Determine whether a
   narrow typed projection seam suffices; do not blindly widen its annotation to
   MemoryProvider while leaving journal-only calls. Preserve persisted schema,
   replay and no-deadline legacy compatibility. No second memory journal,
   scheduler, private-core monkeypatch or Hermes runtime is needed for the pattern.
6. Treat prefetch, turn sync, session-end extraction, prompt injection and tools
   as separately admitted capabilities. Pattern authorization does not authorize
   these automatic effects or external spend. Hooks and provider output cannot
   bypass the central permission ceiling or memory write admission.

Before activation, integration acceptance should include deterministic fake
provider registration/configuration, duplicate and unavailable binding refusal,
no implicit fallback, exact-scope reads, cross-scope rejection, live revocation,
restart recovery, provider unload/rebind refusal for active work, and journal
retirement filtering of stale provider results. Retain the seven-field negative
tests and distinguish frozen invocation snapshots from fresh recall. Run provider
admission and the repository's mandatory release gates after actual composition.

## Delivery boundary

This packet provides a reviewed lifecycle repair, executable offline evidence and
the recommendation above. It intentionally leaves executable provider configuration
and shared composition to the integration owner: no selected backend is necessary
to complete these checks, but backend selection/admission is necessary before
production activation. NoMemoryProvider/default behavior, plugin registration,
wire contracts and source checkouts are unchanged.
