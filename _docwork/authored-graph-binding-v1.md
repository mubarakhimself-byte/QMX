---
id: DRAFT-AUTHORED-GRAPH-V1
type: contract-draft
status: draft
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0305, DEC-0311, DEC-0312, DEC-0342, DEC-0421, DEC-0455]
sources: [docs/decisions/ADR-0029-controlled-canonical-request-join.md]
---
# Authored graph-to-request binding v1

Local implementation candidate under the October 4 delegated backend scope.
Reuse COMP-QMA-DAEMON, existing GraphTemplateCatalog/MissionCompiler/TaskGraph,
RequestRuntime and qualified ProductSession callbacks. No component, listener,
scheduler, runtime database, public method or dependency is added. Existing
CT-40 and canonical join v2 remain the admission doors and authority owners.

## Definition and typed path

A host-owned actor-workflows.json workflow may add graph = {author, edges,
operations, sha256?}. Workflow id must be a qualified GraphTemplate id; workflow
version is explicit. The host hashes id/version/author/steps/edges/operation pins;
an optional supplied sha256 must match. Each read node has an exact op_id and
positive integer version in operations keyed by node id. The installed callback
must match that pin before acceptance; current grant and frozen canonical Agent
ceilings are checked by the existing callback boundary at actual dispatch.

This adapter admits 1..12 unique nodes on one explicit path, 0..1 inference
specialists, one data value per predecessor (one/data-to-data edges). No implicit
joins, collections, cycles, fanout, Cartesian products, arbitrary operations or
code tools. Normalize, metadata read and collect use no inference. Inference
receives only its named predecessor output plus the frozen prompt and authorized
scoped memory. Collect emits the named predecessor value deterministically.

The host compiler emits exactly one canonical Task for the entire inner cursor:
the specialist is the anchor when present; otherwise the final deterministic
node is the anchor. Other nodes are structural graph records and do not create
extra executors. Host-admitted running Task, executing Agent, JobHandle, Mission,
TaskGraph, logical-run and attempt identities remain the canonical join's pins.
The host must explicitly materialize/ready/dispatch the compiled anchor and
submit its JobHandle. Authored joined admission verifies the graph definition,
node bindings, edges, digest and single Task. It never mints those authorities.

## Prompt proposal and host action

An existing paired agent job can produce JSON {workflow, graph_sha256, goal}.
validate_graph_proposal checks exact fields, byte limits, current catalog digest,
and the host-selected profile route; extra tools/permissions or a foreign route
refuse. GraphJobProposal carries no executable authority. The explicit host call
compile_graph_proposal rechecks frozen catalog/graph/profile revisions, then uses
MissionCompiler. The host still independently admits Task/Agent/Job and submits
through existing authenticated paired ingress. The proposal is selection among
host-authored graphs; free-form model-authored topology is deferred.

## Effects, persistence and certainty

Existing req:...:step:<node> read effects and req:...:child:<node> inference,
model/tool budget and memory recall namespaces stay stable across restart/retry.
Intent precedes dispatch, observed receipt precedes node progression. Successful
predecessor effects retain their exact identities. Pending effects stay UNKNOWN;
no request terminal shortcut settles a canonical Task or releases its lease.
Cancel uses the existing parent or named-child request target. Sole Task/Job
terminal authorship stays with existing daemon owners.

Request-only authored jobs can explicitly resume after disk reopen when original
ProductSession grants still authorize them; an observed predecessor is reused,
not redispatched. Canonical joined reopen preserves receipts but does not recreate
Agent authority or dispatch leases: resume refuses until a separately implemented
host reconciliation contract. This is not canonical successor recovery proof.
No automatic reconstruction or fabricated exactly-once inference is introduced.
Legacy definition/catalog and memory-source fingerprints remain byte-compatible.

## Exact next seam

Before a cron adapter: define explicit canonical owner reconciliation that restores
or replaces an Agent/lease without widening frozen authority or rewriting accepted
attempts; prove successor continuation once after observed predecessor completion.
Then extend this typed path adapter to bounded partitions and explicit joins,
proving stable successful partition ids and unknown leases. Cron still names a
pinned GraphTemplate and goal through RoutineScheduler and CT-49, with stable
occurrence receipt and no automatic missed-fire replay. No new cron code ships.

General editor, free topology generation, SDK children, native sessions, external
providers, remote workers, UI/CORTIS/Lab and release activation remain excluded.
LangGraph owns the cursor/checkpointer, the SDK the selected inference loop and
QMA its journal/lifecycle. Dependency versions were checked locally; the official
persistence contract was reviewed at https://docs.langchain.com/oss/python/langgraph/persistence.
