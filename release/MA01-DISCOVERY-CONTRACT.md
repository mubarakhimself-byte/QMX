# MA-01: installed contribution discovery contract

Combined candidate code head `7039fbde1bd749f5aaceac1c14df6afe611c22c2`,
composed from accepted base `af43324676357e5932a9c1c9b10c78465bba460f`,
reviewed startup `c7f0ef603dc56b2b13719c5d9ecd51c240204649` and reviewed
MA01 `8465c03f0ec168e177ba57860f19c869748c0db1`. Final delivery commit,
source manifest, wheels and reproducible install command are bound in the
candidate's supplied SOURCE-REF.json / CLAUDE-HANDOFF.md. Parent review remains
pending. Claude owns UI wiring; this delivery changes no UI.

## Transport and negotiation

Use the existing paired CT-40 WebSocket (`qmx.ct40.v1` plus the pairing proof
subprotocol), authenticated before `initialize`, with the registered Origin
and a unique live producer. These are JSON-RPC query methods, **not new HTTP
routes**. No operator CLI, grants, commands, stores or search index are added.

Request `list_installed_plugins`, `facade_search`, and `facade_get` capability
keys with literal `true`. Request `invoke_contribution_pin: true` when using
pins at invocation. The host supplies `discovery_hit_classes: ["contribution"]`
whenever a discovery method is negotiated. Client claims cannot widen it.
Omitting the capability map or sending `{}` enables none of these new reads
or the invocation-pin feature. Each requires its own literal `true`; false,
integer/string values, and metadata-only declarations grant no discovery read.
When no discovery read is negotiated, `discovery_hit_classes` is omitted,
including when the client requests that metadata or only the pin feature.
Existing default legacy queries retain the accepted base's behavior.

The existing initialize parser rejects nonobject capability declarations and
null member values. Its existing `capabilities: null` handling is equivalent
to an absent map; it also enables no discovery. A refused initialize leaves
all queries behind the existing initialization gate. No parser grammar or
legacy query gate is broadened by this repair.
`get_instance_health` is false/omitted and querying it returns
`policy rejection` / `query_unavailable`. No real scoped health owner snapshot
is composed, so enabled publication is never represented as readiness.

Existing HTTP queries `/q/list_mailbox`, `/q/get_editor_draft_head`, and
`/q/get_pack_ui_request` retain their routes, auth, schema and capability gates.
Known-ID PackUiRequest also remains available over CT-40. Discovery HTTP GETs
are intentionally not mounted; do not bind UI actions to `/q/facade_search`.

## Requests and responses

Shipped declarative schemas are `discovery_args.v1.schema.json` and
`discovery_read.v1.schema.json` in qma-wire schema_data. `parse_discovery_args`
adds method-specific field validation; unknown keys, non-string keys and wrong
scalar types refuse. `hit` uses the existing `federated_hit.v1` grammar.
`ContributionPin` retains the existing `contribution_pin.v1` tuple.

| Method | Exact params | Result |
|---|---|---|
| `list_installed_plugins` | `{}` or `{product_session_ref: "psess:..."}` | `{schema, plugins, roster_revision, authorizes_invoke:false}` |
| `facade_search` | `{query: nonempty literal string, hit_class?: "contribution", product_session_ref?: "psess:..."}` | `{schema, hits, query, hit_class:"contribution", roster_revision, authorizes_invoke:false}` |
| `facade_get` | `{hit: exact ContributionHit, product_session_ref?: "psess:..."}` | `{schema, hit, instance_id, availability_revision, authorizes_invoke:false}` |

All results have `schema: "qma.wire.discovery_read.v1"`. Each plugin row has
`plugin_id`, `package_id`, `package_version`, `instance_id`, strict integer
`availability_revision`, and `availability:"enabled"`. This inventory reads
**currently enabled instances** held by PluginLoader. It does not scan disk or
claim to enumerate disabled installed bytes. A missing/disabled selected
contribution is an explicit unavailable-dependency/tombstone at `facade_get`.
A supported search with no matches returns `hits:[]`; unavailable is not empty.

Search is a case-insensitive literal substring of plugin_id, point and
qualified_id on live `published_contributions()` multi rows, using the
existing Federation mapper. Singleton ports do not become ContributionHits.
Knowledge/Artifact search and get return typed `query_unavailable` because
those owner dependencies are not mounted in this composition. No QMA staged
bytes are surfaced as Library artifacts. Ranked/semantic/hybrid search and
extra fields are not supported. No pack configuration, host path, executable
object, pairing proof or host-control token enters these results.

The list is bounded by the host's loaded roster and the existing CT-40 frame
and request admission limits. There is no new numeric page limit, cursor or
index. `roster_revision` is the loader's publication high-water, not a complete
change cursor, CAS token or a readiness revision: disable need not advance it.
Use exact `facade_get` revalidation instead of relying on that number.

## Scope and authority

An authenticated operator may discover globally when no product_session_ref
is supplied. An explicit operator-owned authoring session also allows global
discovery. An explicit app-use session narrows list/search to its immutable
app_instance_id; get for another live instance refuses policy. Unknown or
nonoperator sessions refuse. This session reference is a narrowing argument,
not a new bearer or app principal; an operator connection retains its existing
global read authority. Machine principals cannot access these discovery reads.
Origin/Bearer refusals stay at the existing paired socket admission boundary.

A discovered hit is never an operation grant. No read calls journal append,
stamp, roster mutation, grant mint, pin lease acquisition, or owner writes.
`facade_get` uses ContributionPinService.revalidate and compares the full live
hit, including plugin, point, package identity, version and revision. A stale
pin never silently retargets. A successful get resolves canonical live metadata;
it does not evaluate a tool, fetch an artifact or certify compatibility with
a custom renderer. Use the actual operation/schema contract at the grant door.

## Selection, invocation and reconnect

From the selected hit, keep exactly `(qualified_id, package_version,
availability_revision)`. Refresh/recheck with `facade_get` before use. When
submitting the existing `start_mission` or `launch_task` invocation, put that
existing pin DTO in optional `params.contribution_pin`; keep all existing
product_session_ref, envelope, payload, grant, input hash and command identity
fields unchanged. The host revalidates the pin **inside invocation admission**,
before durable stamping or effects, checks it agrees with envelope contribution
and enabled instance, and then performs the existing grant checks. A match is
not sufficient to authorize invocation. Missing pin retains the previous
invocation contract for existing callers; callers using pinned discovery must
submit it to obtain the added revision check. No new `invoke_op` method exists.

After restart reconnect with the same pairing identity and reinitialize the
new socket/producer. Reread list/get rather than reuse an old advertised set.
Unchanged bundled pack IDs and current availability revisions are recovered by
the existing journal-backed loader; reads add no enable receipts. A changed or
disabled dependency is unavailable, even if the UI retained its previous hit.
This packet adds no event cursor or replay guarantees.

## Examples and refusals

`MA01-DISCOVERY-EXAMPLES.json` provides JSON-RPC requests, positive result
shapes, optional invocation pin, and refusal examples. Examples were captured from source composition with bundled packs; their
revisions apply only to that capture. Obtain actual revisions from the daemon.
Never make a UI fallback succeed by substituting these fixture values.

| Trigger | Actual refusal contract |
|---|---|
| Before initialize | policy rejection with field `initialize` |
| Capability absent/false or unsupported owner | policy rejection, reason `query_unavailable` |
| Machine principal | policy rejection, field `principal_class` |
| Wrong Origin/missing or invalid proof | existing socket/HTTP admission refusal; no query dispatch |
| Unknown/extra/malformed params | invalid input |
| Wrong full contribution identity | policy rejection, field `hit` |
| Stale version/revision or departed contribution | unavailable dependency with `availability:"tombstone"`, `silent_retarget:false` |
| Other app-use instance | policy rejection, field `instance_id` |
| Pin inconsistent with envelope/instance | policy rejection, field `contribution_pin` |
| Live pin with fabricated grant | existing grant refusal; pin does not mint authority |

## Host lifecycle and artifact staging

Use the supplied 14 noneditable wheels and exact hash-locked dependency closure
under CPython 3.14.7. The supplied CLAUDE-HANDOFF.md gives the installation
commands and source hash; the installer itself is not recertified here.
`QMA_DAEMON_ROOT` selects the private root. Required research-corpus setup stays
in the operator-owned `operator-config.json` field `research_corpus_root_path`.
This candidate adds no provider credentials or provider-enabled cold-start proof.

Installed `qmb host start`, `status`, `stop`, and same-root reopen use the
existing local host-control token. Readiness needs an authenticated held-writer
status with matching PID. The five-second monotonic startup budget includes
connect/send/framed reads; late success refuses and cleans the owned child.
CLI wall time includes parent imports and is not that startup budget. A bind
collision remains a refusal with diagnostics; a later reopen is a new command.
Only confirmed exited/absent writer objects are stale, including retained
Windows process handles with exit code 259. No loose lock PID authorizes signaling.

`qmb host configure artifact-stage-max-bytes <non-negative integer bytes>` is
the local operator-only configuration door. Fresh roots leave the registry cap
unset and upload refuses without an object. `PUT /artifacts/stage` accepts raw
bytes with registered Origin and `Authorization: Bearer pairing:<proof>` after
the cap is configured. Complete at/below-cap bodies return exact fp1. Oversize
or interrupted bodies write no object. Zero permits a complete empty upload.
Cap restoration selects greatest authoritative journal_seq before validating
receipt/value, so backward/equal wall clocks cannot select an older larger cap.
Invalid latest receipts refuse startup; no older/default fallback or replay
configuration receipt is written. Setup fields do not override the journal.

## Cancel and authority boundaries

Discovery is a synchronous metadata read and creates no JobHandle or cancellable
work. Closing the view or disconnecting the socket does not cancel accepted jobs.
Existing `cancel_job` remains a distinct CT-40 command under its negotiated
capability and paired operator admission; it is not an app operation or host stop.
Its payload contains exactly `handle_id`, `logical_run_id`, `attempt_id`,
`command_id`, `expected_state`. The durable handle supplies the originating
product session; clients cannot name authority. Existing origin/principal and
attempt fences still apply. Repeating command identity deduplicates; expected
state is observational across a queued/running race. A terminal cancel is a
recorded no-op. This candidate does not certify a connected provider/worker kill.
Consult qma.wire.cancel_job and the existing cancel tests for the closed grammar.

Keep these distinctions in the UI and future implementation:

- Global Copilot identity is shared presentation identity; each psess retains
  profile, immutable instance, current grants and authority. Conversation history
  cannot grant authoring or copy another session's authority.
- App-use reads/uses admitted operations. Authoring owns save/apply boundaries;
  this packet has no Mini App candidate save or publication command.
- Memory is owner-admitted durable content with provenance. Checkpoints recover
  execution state and do not constitute memory admission or durable backup.
- AgentLedger/task evidence and authoritative journal receipts establish known
  outcomes. Diagnostic logs are bounded observations and cannot establish success.
- A native harness runs/supervises actual tools under its owner boundary. An
  inference proxy routes model requests; neither proves the other's execution,
  isolation, credentials or provider health.

## Combined verification and limits

The exact candidate source and all installed product member bytes are bound by
the final source/install manifest supplied to the parent. Combined tests include
the complete wire suite, configured offline SDK/import regressions, daemon
discovery/pairing/pin/cap/transfer checks and the full host compatibility suite.
Serial external installed acceptance uses actual `qmb host start` under product
defaults, paired HTTP/WS, all 13 declarations and explicit legacy reads before
and after same-proof restart, with exact bundled identities/current revisions
and no extra enable/configuration receipts. A separate installed owner fixture
tests scoped/principal/stale/disabled refusals and no journal/roster/grant changes.
Injected clock tests cover decreasing/equal times and invalid latest cap receipts.
Owner fixtures are acceptance setup, not new product wire mutation methods.

MA02 through MA13 are not shipped. Health and Artifact/Knowledge discovery remain
typed unavailable. [MA02-NEXT-TASK.md](MA02-NEXT-TASK.md) is a next-task pointer;
first data-only create/publish/update/undo needs MA02 candidate persistence, MA03
validation, MA04 publication/undo and MA05 activity acceptance. No arbitrary
generated code, autonomous apply, mutable app database, API credentials,
remote worker, always-on authority, custom UI or deploy route is added here.

No full repository suite or measured aggregate coverage was run. Keep existing
80% aggregate/per-package coverage, exact/chrono 100% and core mutation 68% floors;
none is lowered or claimed passed. Strict docs retains 17 identical inherited
stale/provisional errors. QMB formatting debt and historical actor deadline
failures remain outside this bounded acceptance. Provider-enabled cold start,
other Python overrides, connected UI/provider, native harness, Linux/remote,
installer recertification, crash/power-loss and whole-release proof are excluded.
Parent independent review/publication remains outstanding; no public push,
protected merge, credentials, provider call, deployment or UI edit occurred.
