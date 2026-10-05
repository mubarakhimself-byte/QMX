# MA02 Mini App candidate contract

MA02 is backend candidate persistence only. The named amendment is recorded in
[ADR-0034](../docs/decisions/ADR-0034-miniapp-candidate-persistence.md).
Core owns the data-only descriptor, wire owns additive CT-40 DTOs, and daemon
owns issuance and the app_candidate_state fold on the existing SQLite class.
Complete bytes remain in the existing artifact_store. No new independent store,
definition-store slot, database engine, grant, evaluator or publication is added.

The mounted names are save_app_candidate (command), get_app_candidate and
get_app_candidate_history (queries), over the existing authenticated paired
CT-40 WebSocket. Each requires its own literal-true initialize capability.
Absent, empty, null, false, integer and string capability values enable none.
Clients cannot echo unsupported server capabilities into support.
No new HTTP candidate query is mounted. Existing /artifacts/stage is the only
byte-upload path and still requires negotiated stage_artifact and configured
registry:artifact.stage_max_bytes. No default cap is introduced.

CT-40 capabilities are per socket. The inherited HTTP gate uses the latest
successful initialize for the pairing identity; another tab may replace that
HTTP map, and closing it does not restore an earlier map. Supplied invocation
pins retain their protective validation even without advertised pin opt-in.
MA02 does not change either inherited boundary.

Save params are exactly product_session_ref, expected_context_revision, content,
plus optional instance_id on creation; an edit requires candidate_id and
expected_revision and forbids instance_id. A save JSON-RPC id must be a nonempty
string. The authenticated producer_id plus that id identifies the durable
operation receipt. Reuse both across a lost-ack reconnect; the same intent returns
the original accepted version, even when the head has subsequently advanced.
Changed intent under that pair is idempotency_conflict. A JSON-RPC notification
or numeric save id cannot create a candidate.

The existing ProductSession row must be operator-owned and authoring. The
connection must be operator, and the save must name its current context_revision.
No request-supplied profile, principal, origin, parent, receipt, validator, grant
or publication field is accepted. Bound authoring sessions stay within their
instance. New candidates may be unbound; maintenance creation may explicitly
target one installed instance, and that scope is immutable for its chain.
Current global authoring can maintain a chain; every edit records its authoring
session while preserving the originating authoring session and operator identity.
This uses the existing operator/pairing/ProductSession authority model. A session
reference or conversation is not a separately minted grant.

The closed content descriptor is:
```json
{
  "schema": "qma.miniapp.candidate-content.v1",
  "kind": "data-only",
  "metadata": {"title": "Read panel", "description": "A draft composition"},
  "composition_ref": {"fp1": "fp1:sha256:<64 lowercase hex>", "byte_count": 14, "media_type": "application/json"},
  "source_refs": [],
  "asset_refs": []
}
```
Every reference has exactly fp1, byte_count and media_type. The composition is
a daemon-held local-complete JSON object with no duplicate keys or nonfinite
numbers. Source and asset references may hold long/binary inert bytes. The
daemon recomputes fp1 and byte count for every reference; unknown, incomplete or
mismatched bytes refuse before candidate acceptance. Paths, URLs and executable
entrypoints are not descriptor reference alternatives. No inline composition,
binary blob, code module or arbitrary import is evaluated by the daemon.

CandidateContent uses the parent canonical_bytes/fp1 recipe: NFC, sorted keys,
integer identity numerics, omitted absent fields. Arrays remain order-sensitive.
candidate_id is daemon-issued appcand:<32 hex>. content_fp1 names immutable
canonical descriptor bytes. revision names a separate canonical version envelope
including parent_revision, daemon-recorded origin/edit authority, context and
operation/intent identity. Equal content in different versions can reuse
content_fp1; returning to old content cannot return the old revision (no ABA).

The save result is the immutable version snapshot with schema
qma.miniapp.candidate-version.v1, candidate_id, revision, content_fp1,
content_byte_count, owner_principal, principal_class, originating_authoring_session,
authoring_session, context_revision, operation_key, request_fp1, producer_id,
request_id, intent, receipt_fp1 and content. parent_revision is omitted for a
first version; instance_id is omitted for an unbound candidate. No journal_seq
is exposed. intent is the exact canonical admitted request, not a transcript.

get_app_candidate params are product_session_ref and candidate_id, with optional
revision selecting an exact historical member of this chain. The result includes
schema qma.wire.app_candidate.v1, candidate_id, current_revision, version and
validated:false / published:false. MA02 records no validation/publication verdict.
Historical versions are read-only and never silently retargeted.

get_app_candidate_history uses the same required params plus optional
cursor_revision. A page returns exactly one immutable version in versions,
current_revision, and next_revision naming its parent if present. Start at the
head, then pass next_revision as cursor_revision until it is omitted. This pins
the remaining lineage even if another save advances the head. A version/cursor
from another candidate refuses. This page cardinality is DTO structure, not an
invented configurable retention/quota default.

App-use can read a candidate only when its immutable instance matches the
candidate's bound instance; an unbound new-app candidate cannot be read by
app-use. App-use cannot save by supplying authoring-looking extra fields, a
different principal class, or an unknown psess. Machine sessions/pairings refuse.
Owner and bound authoring scope are checked on reads and receipt retries.
Reads do not append events, mutate roster/grants, validate or publish.

A stale expected_revision returns CT-04 policy rejection with
field:expected_revision, refusal:stale_revision, expected/current and
wrote_version:false. A stale authoring context returns field:
expected_context_revision, refusal:stale_revision. Unavailable query capability
returns the existing typed query_unavailable. Malformed metadata/reference/schema
returns invalid input. Lone surrogate text in request IDs, metadata or other
identity strings returns CT-04 invalid input before fingerprinting/writes and
keeps the paired socket usable. Valid Unicode keeps the existing NFC/UTF-8 recipe.
Scope/profile/owner violations return policy rejection.
Unknown candidate IDs are not accepted as client-issued identities.

Acceptance is the fsynced app_candidate.saved journal commit after immutable
artifact announcements. SQLite rows are derived by journal_seq, with
as_of_recorded_at and ascending journal_seq for equal instants.
A precommit failure never changes the candidate head; it can leave orphaned
immutable artifacts. A postcommit projection failure reports storage failure,
operation_committed:true and retry_same_id:true. Live retry/read rebuilds a dirty
projection before proceeding. An ambiguous journal refusal also marks the fold
dirty, so retry of the same producer/id reconciles durable evidence.
Restart first verifies consumed candidate and product-session journal receipts
with the existing journal owner identity recipe (class, world, event, sequence,
timestamps, scope and payload). A corrupt embedded fingerprint refuses; it is
never replaced with a recomputed value. Restart validates all artifact bytes,
canonical version/content, original
request/key fingerprints, chronological authoring-session/context authority,
immutable scope/origin/owner and complete parent chains before replacing the
projection. Missing/corrupt/orphaned evidence refuses startup without accepting
a partial chain or releasing a conflicting writer early.

Shipped JSON Schemas: app_candidate_content, app_candidate_save,
app_candidate_version, app_candidate_snapshot in qma.wire.schema_data.
[Exact request examples](MA02-CANDIDATE-EXAMPLES.json) use the shipped field names;
fingerprints in runnable acceptance are produced by the installed stage endpoint.

MA03 must validate catalog, structure, limits, operation schemas/dependencies and
renderer safety; MA02's finite JSON check is persistence syntax only. MA04 must
publish/replace/undo with active-generation CAS and receipts. Candidate identity,
version, descriptor and saved composition fp1 are refused as live invocation
targets. MA02 neither applies ChangeRequests nor publishes editor drafts.
The existing ChangeRequest fixture/owner remains separate; a durable mounted
app-use change-request authoring workflow is not newly claimed here.
UI, authoring agent tools, providers, code execution, custom assets serving,
network setup, credentials, deployment, mutable app data and MA03-13 remain outside
this delivery. Parent independent review precedes integration.
