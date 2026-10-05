# MA03 panel/composition validation contract

Backend MA03 only, based on accepted MA02 `1c8e0b6039846d687d7464769c7e68bde711c364`.
The named amendment is [ADR-0035](../docs/decisions/ADR-0035-miniapp-composition-validation.md).
Independent parent review is pending. No MA04 publication route or UI implementation ships.

## Authority and API

COMP-QMA-WIRE owns schemas and the existing PackUiView adapter. COMP-QMA-DAEMON
selects the validator and records proofs through MA02's authority lock,
ArtifactStore, authoritative journal and SingleSqliteWriter. No plugin-supplied
validator, module import, renderer, database class, grant or runner is introduced.

All three verbs use the existing paired CT-40 JSON-RPC WebSocket, with their own
literal-true initialize capabilities. No new HTTP route exists. The existing
stage_artifact capability and operator artifact.stage_max_bytes govern uploads.
Missing, false or nonboolean capabilities enable no MA03 access. The connection
and referenced ProductSession must be operator-owned. Existing scope rules apply:
app-use may read catalog and proofs for its immutable instance, never validate;
bound authoring cannot escape its instance. Global authoring may validate a draft.
Maintenance versions keep MA02's immutable instance and require dependencies in it.

| Verb | Closed params |
|---|---|
| get_app_ui_catalog | product_session_ref |
| validate_app_candidate | product_session_ref, candidate_id, revision, expected_context_revision, catalog_fp1 |
| get_app_candidate_validation | product_session_ref, candidate_id, revision, validation_fp1 |

Validation requires current authoring context and exact catalog identity. A stale
request catalog/context is a CT-04 refusal. Validly admitted but malformed
compositions return an immutable status=invalid result with actionable errors.
Each error has path, code, message and remediation; arrays are bounded and sorted
by path then code. Neither caller-provided success nor invented grants are accepted.

## Composition v1 and component props

The served catalog is qma.miniapp.catalog.v1. The closed composition is
qma.miniapp.composition.v1: schema, catalog_fp1, panels, bindings. A panel has
required title, root, elements; optional description, size={minW,minH}, data.
MA03 requires data to name one binding. Elements is a flat map of simple names to
{type, optional props, optional children}. Containers alone may have children.
The root must exist; every element must be reachable exactly once; unknown child,
cycle, shared child, duplicate child and orphan are invalid. Element and binding
names use letters/digits/underscore/dot/dash, starting with a letter or underscore.
Valid Unicode display text remains allowed; lone surrogates are refused.

| Component | Closed props |
|---|---|
| Stack | optional direction=row/column |
| Grid | optional columns positive integer, min positive number |
| Heading, Text, Badge | required text string |
| Metric | required label string, value finite number/string/boolean/null; optional tone=up/down/plain |
| Table | required columns string array, rows primitive-cell arrays of exactly the column count |
| LineChart | required series array of {label string, values finite-number array, optional color} |
| Callout | required text string; optional tone=info/warning/danger |
| Button | required label string and action binding name |

LineChart color accepts only catalog color tokens (var(--primary), var(--chart-1) through
var(--chart-5)). Explicit empty arrays represent no observed samples. The demo seed
fallback is excluded: validation never synthesizes financial results. Button may
reference only its panel's existing read binding. There are no URL, eval, script,
credential, provider, raw HTML, custom component or write-operation fields.

The model follows the original root/elements description and actual SDK/SpecView
component vocabulary. Demo dimensions, chart numbers and 60-element/6-depth guesses
are not product requirements. Grid retains the actual columns and min props; this
backend does not certify how a separately owned renderer uses them.

## Operation bindings and data states

The catalog returns live scoped operations separately from its content identity.
Each binding pins instance_id, qualified_id, package_version,
availability_revision, op_id, op_version, input_schema, output_shape,
descriptor_fp1, and parameters. Every pin must equal the existing mounted owner
adapter and descriptor. Currently only the existing qmb.analysis.project READ
adapter is admitted, at analysis-backtest:qmb. Descriptor membership alone does
not advertise future adapters. The ordinary grant path and MA03 share the
existing operation/contribution mapping; catalog reads and valid proofs grant
nothing and do not execute a read.

Parameters must have exactly the existing descriptor's required/optional keys.
run_fp1 is a well-formed QMB logical run fingerprint, not an ArtifactStore blob
hash or experiment-spec fingerprint. Optional as_of uses the existing UTC ISO Z
parser. Declared source_refs must remain complete with exact bytes/count/hash.
Actual run existence, owned verified DONE state, environment, fresh grant and
invocation pins remain the existing BacktestingService/dispatch checks at use.
An unready logical run may have a valid composition contract and unavailable data.
Custom asset_refs remain excluded until MA13.

The served miniapp_read_state.v1 schema defines a proposed presentation envelope
around the existing qmb.analysis.project artifact_ref output: schema, state,
op_id, op_version, descriptor_fp1, input_hash, optional data/reason/as_of. ready
and stale require data={fp1,kind:saved-view,body}; stale/unavailable/failed require
reason; empty/unavailable/failed prohibit data. Empty is not failure. Unavailable
is not fabricated empty success. Descriptor/output-shape pins and envelope schemas
are validated; no live QMB output is observed or converted by this MA03 service.
The future caller must check exact invocation/output identity before rendering.

## Configured bounds

Configure every key in operator-config.json.miniapp_validation_limits. There are
no production defaults; missing configuration advertises validate_app_candidate
false while read contracts remain available. Malformed configuration returns a
typed refusal. Values must be positive integers, excluding booleans, within these
safety ceilings: max_bytes=65536, max_panels=128, max_elements=1024, max_depth=32,
max_json_depth=32, max_nodes=8192, max_array_items=1024, max_string_bytes=16384,
max_errors=64. max_elements counts the whole composition, max_depth the element
path (root depth 1), max_json_depth the JSON nesting (root depth 0), max_nodes
includes keys and values, max_string_bytes is UTF-8, max_bytes bounds both raw
composition bytes and stable data bytes. Size dimensions use max_array_items.
An iterative preflight bounds work before schema/tree traversal and rejects cycles,
nonfinite numbers and malformed Unicode. Proof outputs have a separate 64 KiB
ceiling. Existing stronger transport/staging limits continue to apply; changing a
host bound changes catalog identity and makes prior proofs stale.

The example config is a disposable test selection, not a registry default or
operator ratification. The closed config remains local to the existing bootstrap
owner; MA03 adds no remotely writable configuration command.

## Exact proof, recovery and future eligibility

Host validator identity is qma.daemon.panel-composition.v1. The result schema is
qma.miniapp.validation.v1. The validator_input_fp1 pins candidate_id/revision,
content_fp1, composition_ref, catalog_fp1, validator_id, sorted exact dependencies
with archived descriptor refs and parameters, authenticated owner,
product_session_ref and context_revision. Validation_fp1 fingerprints the complete
result including status/errors and PackUiView requests. Catalog, descriptor and
result bytes are immutable ArtifactStore artifacts, using the existing fp1 byte
recipe over deterministic finite JSON serialization (sorted keys, compact ASCII
JSON, no NaN). This is data byte identity: floats and null display values do not
change the parent canonical identity law for MA02 descriptors/versions.

Successful views reuse PackUiView: renderer=json-render, slot=canvas-widget,
parameter_schema/op_id from the pinned binding, ui_resource=composition_ref.fp1,
catalog_ref=catalog_fp1, view_id=view:<candidate_id>:panel:<zero-based index>,
view_version=1. The resource is the composition wrapper; that index selects the
panel root/elements. view_version denotes this adapter format, not an active
publication generation. No PackUiRequest is installed in the roster by validation.
All five existing PackUI slot names remain in the catalog, without new slot behavior.

app_candidate.validated commits on the existing app_candidate_state fold; the
app_candidate_validation table is replaceable derived state on the existing writer.
Identical admitted input/result returns the original proof receipt, including after
lost acknowledgment/restart. This dedup is by deterministic proof identity, unlike
MA02 save's producer/request-id receipt. JSON-RPC id is correlation only here.
A precommit failure leaves at most unreferenced immutable artifacts; postcommit
projection failure reports operation_committed and retries first replay the journal.

Startup verifies actual journal receipt identity, exact candidate version, artifact
bytes, catalog/validator, descriptor/input/structure and adapter output for success
before transactionally rebuilding validation rows. It uses the archived catalog and
descriptors, preserving historical evidence despite current dependency changes.
Missing/corrupt evidence refuses startup without rewriting authoritative bytes.
Current reads additionally check head, host catalog/validator, authoring context,
composition/descriptor/source bytes and live scoped operation pins. Changed content,
parameters or references require a new MA02 version; changed dependencies invalidate
validation_current. Validation_current is advisory evidence for future MA04 checks,
not publication authorization. MA04 must recheck it atomically at apply; this
backend always reports publication_supported=false and authorizes_invoke=false.

## Evidence boundary and handoff

[Exact disposable examples](MA03-COMPOSITION-EXAMPLES.json) include two panels,
real installed catalog/binding pins, candidate/proof, refusal cases, and named
configuration. They are contract fixtures, not live results or user data.
Parent review must independently replay the installed paired API and restart.
No UI/client execution, complete run-data read, publication/update/undo, MA05
activity/log service, provider, Linux, native launcher, installer, process power-loss,
full repository coverage/mutation or whole-release certification is claimed.
