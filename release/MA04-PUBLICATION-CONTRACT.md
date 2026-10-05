# MA04 local publication contract v1

Backend-only candidate for independent review, based on accepted MA03
41082c1805e33c9d7083ccd3ac81b6c31a2f8fe3. This contract implements MA04 only.
Ownership and the named amendment: [ADR-0036](../docs/decisions/ADR-0036-miniapp-local-publication.md).
The complete calls and observed test-host receipts are in
[MA04-PUBLICATION-EXAMPLES.json](MA04-PUBLICATION-EXAMPLES.json).

## Transport and authority

Existing paired CT-40 JSON-RPC WebSocket adds commands publish_app_candidate and
undo_app_publication and query get_app_publication. Each needs its own literal-true
initialize capability. No new HTTP route is added. Commands are advertised only
when the trusted dev-factory host is loaded and MA03 limits are explicitly valid;
this advertisement does not certify a candidate, health or an operation grant.
The query remains available to explain committed state. Existing get_pack_ui_request
requires its own capability and exact installed instance/availability revision.

Each socket retains its negotiated capabilities. HTTP staging and existing HTTP
queries use the pairing identity's most recent successful initialize map, replacing
the whole map. Include stage_artifact and every needed HTTP gate in that map; closing
a socket does not restore an earlier map. An absent/false invoke_contribution_pin
advertisement never relaxes supplied pin validation at start_mission/launch_task.

Only the authenticated operator in current authoring profile can publish or undo.
App-use may read the publication in its exact pack:dev-factory scope. It cannot
save candidates or publish/undo implementation. Machine/cross-scope requests refuse.
A globally unbound authoring session can publish this first app; a bound authoring
session must match the publication host, while candidate origin scope stays immutable.
No autonomous Copilot policy is supplied; that is MA06.

## Closed request shapes

All arguments are required; extra keys, authority/grant fields, URLs/code and
nonliteral capability values refuse. The shipped publish_app_candidate,
undo_app_publication and get_app_publication schemas are the declarative DTOs.

publish_app_candidate takes product_session_ref, candidate_id, revision,
validation_fp1, expected_context_revision, expected_active_revision and
expected_availability_revision. The first active CAS is explicit null; subsequent
CAS is the exact prior active_revision fp1. Context and installed availability are
non-negative integer revisions, never booleans. Other ids are bounded strings;
revision/proof/active identities are fp1:sha256 with 64 lowercase hex characters.

undo_app_publication takes the same fields except revision is replaced by
 target_publication_revision, the active_revision of a prior committed publication
of this app. It takes a current compatible MA03 validation_fp1 for that candidate
version, current context, active and installed-host CAS. Undo issues a fresh
publication generation and receipt; it does not reuse an old active identity.

get_app_publication takes only product_session_ref and candidate_id. Unknown app
is a typed refusal. Result is {schema: qma.miniapp.publication.v1, active: receipt,
authorizes_invoke: false, health: not-observed}. It describes committed history;
readiness/data/job outcome must come from actual operation owners.

## Receipts and exact identity

Successful commands return the same immutable body plus active_revision and
receipt_fp1. miniapp_publication_record.v1.schema.json defines the closed body.
It includes candidate_id/revision/content_fp1, validation_fp1 and its actual
validation_receipt_fp1/catalog_fp1, instance_id/pack_id/pack_version/local_id,
publication_generation/availability_revision/roster_generation,
base_pack_ui_request/pack_ui_request, owner_principal/product_session_ref/
context_revision, producer_id/request_id/operation_key/request_fp1/intent and
action (publish, replace, undo). Replacements add previous_active_revision; undo
also adds undo_target_revision. The instance is pack:dev-factory; its version is
the current trusted package version. The stable local contribution is
 dev-factory:miniapp-<candidate UUID>, at the existing toolset contribution point.

active_revision fingerprints the complete immutable receipt body using the MA03
finite sorted JSON UTF-8 byte recipe (compact separators, ensure_ascii=true,
allow_nan=false), explicitly including initial intent's null active CAS. It is
not the candidate revision, validation identity or availability revision.
receipt_fp1 is the actual app_candidate.published journal event fingerprint.
operation_key is existing canonical fp1({producer_id, id}); request_fp1 is the
byte fingerprint of {method, params, owner_principal}. No timestamp guess or
projection generation can substitute for those identities. Publication body and
installed PackUiRequest each have a 64 KiB hard ceiling, in addition to MA03's
explicit composition bounds. MA03 numeric examples are test configurations only.

## Apply and recovery

Before any new publication, under the same authority/roster locks, the host replays
MA03 authoritative validation and rechecks candidate head, owner/session/context,
catalog/limits/validator, complete source/composition/descriptor bytes and exact
live declared READ pins. Current host permission and dependency owners are checked.
An undo waives only candidate-head staleness for its previously committed target.
Invalid or stale proofs refuse before a journal append. This does not execute a
read or grant invocation. Existing grant expiry/revocation, input/effect/session
and pin checks remain mandatory at actual use; no UI-view change edits them.

Publication stages inert immutable bytes, then appends app_candidate.published.
Only that acceptance can advance the existing child projection, installation
record, AtomicRoster and live loader. Precommit failure retains the old generation.
An ambiguous journal response returns storage failure with operation_committed:
unknown, retry_same_id: true and reconciliation_required: true. A confirmed commit
followed by projection failure returns storage failure with operation_committed:
true and the exact active_revision/receipt_fp1. Retry the identical producer/id,
method and parameters; do not increment CAS or invent another id to recover.

Retry authenticates current profile/scope/owner, reconciles accepted history and
returns the original operation receipt before new-work staleness checks. Changed
intent at the same producer/id is idempotency_conflict. New ids require current CAS.
Concurrent requests from one active revision yield one accepted generation and a
typed stale_revision refusal. The single-app dev-factory slot refuses a second app.

Existing QMB host start/stop performs dead-PID marker cleanup before acquiring the
sole-writer root. A raw DaemonProcess.compose against an abrupt-stop marker refuses;
it is not a replacement for that owner path. Installed abrupt before/after-append
proof uses the existing host.stop owner, then reopens and retries the exact operation.

Startup verifies stored journal identities, closed receipt shape, immutable bytes,
historical authoring authority, candidate/host/active CAS, generation chain,
preceding positive validation evidence and exact PackUiRequest adaptation before
rebuilding derived rows. Missing/corrupt evidence refuses startup without rewriting
it. Derived projection loss is repaired. Loader activation and roster reconciliation
preserve committed availability revision and one registration. Staging failure
leaves the prior registration intact; cleanup depth does not grow per replacement.
Reads encountering an unfinished commit reconcile or return refusal.

## Milestone limits

Installed proof uses two real supported qmb.analysis.project bindings and actual
paired API, staged bytes and journal receipts on disposable local hosts. It proves
presentation/lifecycle identity, not a ready logical QMB run or live SavedView body.
Health remains not-observed; grants are unchanged. Existing accepted-job continuation
regressions are rerun; no new provider job is started by publication.

One app per trusted host, fixed host version and data-only composition are the
bounded milestone. No arbitrary code/module import, custom UI/assets, API server,
remote provider, external network deployment, live trading, MA05–MA13, connected UI,
full coverage/mutation, launcher/installer/Linux or physical power-loss certification.
Independent parent review must inspect the candidate and evidence before integration.
