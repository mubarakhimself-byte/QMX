# MA-01: installed contribution discovery contract

Backend implementation candidate from `af43324676357e5932a9c1c9b10c78465bba460f`.
Claude owns UI wiring. The original packet's installed evidence is retained.
MA01-R1 corrects omitted/empty capability negotiation. Source checks and
serial installed replay of this correction pass. Independent parent review
remains required before integration.

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

## Evidence and retained limits

Focused tests cover actual bundled roster metadata, literal empty result,
unchanged read journal/continuity, no minted grant IDs, dependency disable,
full identity mismatch, app-use scope, exact restart identities/revisions,
capability false/echo protection, closed inputs and invocation-time stale pin.
Original packet source evidence (`f9fdacac`): **338 wire tests and 57 selected
daemon tests passed**;
canonical nested lint/format, strict cross-system types (zero errors), citation,
registry, inventory and diff checks pass. Strict documentation lint still has
17 inherited stale/provisional-document errors; no MA-01 document adds one.

Original packet serial installed acceptance used 14 noneditable offline wheels, an isolated
interpreter outside checkout, the production paired loopback listener and real
bundled packs. It confirms all three reads, exact contribution resolution,
Origin/proof refusals, app scope, missing owners, read purity, disabled and stale
pins, and restart identity/revision. A fixture advances the existing publication
owner after selection to prove stale invocation refuses before journal mutation.
Machine refusal is tested at authenticated installed dispatch; no external
machine credential is enrolled. The three existing HTTP paths retain admission:
PackUiRequest and mailbox reads succeed; a missing editor head explicitly
refuses at its existing owner. Existing source tests also retain positive
editor-head reads.

A separate external client against the installed `python -I -m qma.daemon`
entrypoint repeats list/search/get, known-ID PackUiRequest, health unavailable
and same-proof restart. Local installed `qmb host pair` confirms pairing;
`qmb host status/stop` work. This direct entrypoint evidence does **not** certify
fresh `qmb host start` readiness. The startup worker's pending repair is not
included. All owned test hosts/listeners are stopped. No connected UI or
provider proof is claimed. Full logs, captured JSON, source/wheel/installed
hash verification and retained failed harness attempts are in the private
MA-01 acceptance report supplied to the parent.

MA01-R1 source verification passes **342 wire tests and 32 MA-01 daemon tests**,
plus nested lint/format, strict types (zero errors/warnings) and citation checks.
Strict documentation debt remains the accepted base's identical 17 errors.
Real-dispatch cases cover absent, empty, false, true, partial, nonboolean,
metadata-only and malformed declarations. They
check advertised capabilities, all three query outcomes, default mailbox and
PackUiRequest compatibility, explicit editor-head admission, and unchanged
journal/roster state. The repair report records its separate focused evidence.

Revised installed proof rebuilds qma-wire in a separate 14-wheel noneditable
D: environment. An external paired client replays all 13 declaration cases
through the installed daemon entrypoint, then repeats after stop/restart with
the same pairing proof and exact identities/revisions. Capability maps match
captured source dispatch; all three read outcomes/refusals match. An explicit
legacy-only request additionally confirms no discovery enablement and retains
HTTP mailbox/PackUiRequest success plus explicit missing-editor-head refusal.
Absent/empty maps retain default mailbox and PackUiRequest HTTP reads; the
existing editor-head opt-in gate still refuses them. Journal events stay
unchanged across each matrix. Both hosts exit cleanly and the serial slot is
released. The revised 14 wheels / 832 Python+JSON members match source and
installed bytes, with the exact pinned 95-package runtime inventory. Startup
changes remain separate; direct-entrypoint evidence does not certify fresh
QMB-spawn readiness. Original installed evidence is retained separately and
is not substituted for this corrected negotiation replay.

MA-02 onward remains unsupported. No UI, provider call, credential enrollment,
deployment or publication is included. Retain inherited aggregate coverage
floor, strict docs debt, QMB formatting debt, historical actor deadline failures,
fresh `qmb host start` reliability limit and absent connected-UI/real-provider/
Linux/remote proof. MA-01 does not recertify installer or whole-release quality.
