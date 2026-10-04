# Bounded host callback bridge (internal version 2)

Implementation verdict: reuse COMP-QMA-DAEMON. This is the isolated host-binding
increment requested after reviewed checkpoint 222c34ba; no new COMP, CT, scheduler,
store, canonical owner or memory scope is introduced. ADR-0029 remains draft.
The affected peers are core frozen Agent/ToolRecord definitions, wire invocation
validation, ProductSession grants, canonical TaskGraph/Job ownership, and the
existing retained metadata callback. Memory-provider selection is a separate lane.

## Trusted startup configuration

A host must first register a real compatible ToolRecord through the existing Tool
Registry. For this metadata adapter its schema is exactly:

```python
{"required_keys": ["snapshot_ref"], "optional_keys": ["locator"]}
```

Its `acts` includes `qml.research.browse`; its qualified ID is explicitly present
in the execution Agent's frozen tool set, and `library.read` is in that Agent's
frozen permission set. A current ProductSession grant independently authorizes the
same operation, contribution/package, enabled instance/configuration and bounded
arguments. The model selects only the `research_browse` alias and data arguments.

An already admitted host may configure the concrete metadata factory using:

```python
research_browse = {
    "canonical_tool_id": "installed-plugin:metadata-browse",
    "source_id": trusted_existing_source,
    "snapshot_ref": trusted_retained_snapshot,
    "allowed_locators": ["README.md"],
}
```

The example ID is a placeholder for a host-selected, already registered matching
record, not a tool shipped by this change. Registering corpus search under this ID
is not valid: its act/schema must actually match metadata browse. Selection is
host startup configuration, never a model or catalog field. ToolBinding carries a
HostCallbackIdentity sealed to the concrete executor; changing `execute` alone
invalidates it. The concrete factory and its current-target wrapper alone stamp
`qma.research-metadata-browse`, revision 1. Any semantic builder change must advance
that revision. Trusted host Python can install capabilities; this is not a sandbox
against arbitrary malicious code inside the daemon.

## Durable and effect boundaries

Canonical admission validates before journaling acceptance or persisting a Request.
Internal tool-equipped receipts use contract_version 2 and binding_version 1.
They pin the qualified callback ID, host adapter/revision, exact alias set,
descriptor and registry metadata, contribution, instance/configuration, exact grant
ID and canonical bytes digest, source identity and argument scope. JSON strings
preserve complete nullable descriptor/registry fields within the journal's existing
null-free identity-map contract. Projection exposes the original accepted pins.
No schema, act, alias or registry availability grants authority.

Host candidate resolution, actual binding preflight, inference continuation and
actual dispatch independently check those pins. Checks run in the existing runtime
-> Job -> Task -> ProductSession order and are never called from beneath a held
ProductSession callback lock. Public dispatch retains its accepted-work boundary:
a grant change after that boundary does not retroactively undo an accepted read.
The current-target wrapper additionally rejects retargeting before its metadata
callback. Cancellation/query remain responsive during accepted callback execution.

The bridge supports only the existing bounded metadata read callback. There are no
joined arbitrary/native/MCP tools, external writes, live inference or trading in
this evidence. A broader operation needs its own trusted factory, callback revision
and registry/schema compatibility rule. No default provider or production browse
registration is inferred.

## Canonical ownership and restart limits

Bounded success remains an observed result; Task/Job settlement stays owner-driven.
Definitive preflight denial occurs before a child/model/effect is started. Existing
effect dispatch writes pending evidence before grant/callback admission; a later
denial or authority loss conservatively leaves canonical UNKNOWN even when the
fixture proves zero callbacks. UNKNOWN is not resolved by this bridge. It requires
existing owner reconciliation and separately admitted fresh work. Interrupted or
same-Task joined retries continue to refuse.

Restart retains accepted binding pins and observed bytes but restores neither the
original volatile frozen Agent nor a live dispatch lease. The host may reopen its
known Quant registration for disclosure; that does not recreate Agent authority.
Changed/missing bindings cannot authorize continuation or effect replay. A completed
Request is not canonical Task settlement, and unknown children, pending effects or
missing original authority continue to require reconciliation. Existing effect keys,
child threads, canonical attribution and exact behavioral memory scopes are intact.

## SDK boundary

The existing pinned SDK composition is retained. Official LangChain documentation
describes tools as callables with schemas, with configurable names, and distinguishes
thread/checkpoint persistence from runtime context. Neither SDK naming nor checkpoint
state is treated as QMA permission authority here. No new SDK API or dependency is
introduced. References consulted:

- https://docs.langchain.com/oss/python/langchain/tools
- https://docs.langchain.com/oss/python/langchain/agents

Focused public-path tests use a scripted inference adapter and the real registered
metadata callback, local paired transport, durable journal, and real grant dispatcher.
They separately count model requests, actual metadata reads and substitution effects.
The delivery ledger records red/green runs, stable-source gates and independent
review; focused success is not a release acceptance or corpus-ratification claim.

The runtime constructs the executor and authority maps from the checked binding.
An independently supplied executor is refused; envelope operation, contribution,
instance, grant and caller kind must match that binding exactly. Passing a valid
permitted binding as a decoy cannot authorize a separately granted operation.
Result collection uses a host-owned list and does not accept another callback.
