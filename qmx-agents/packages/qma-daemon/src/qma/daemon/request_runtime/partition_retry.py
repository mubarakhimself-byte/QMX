"""Exact typed joins for the two-read canonical recovery slice; no execution owner."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from qma.core.vocabulary.enums import EdgeMapping
from qma.daemon.taskgraph.join import (
    DuplicateKeyPolicy,
    JoinArrival,
    JoinPartitionStatus,
    JoinRetryPlan,
    apply_join_arrival,
    open_join,
    plan_partial_retry,
)
from qma.daemon.taskgraph.records import TaskGraph
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import policy_rejection

from .actor_profiles import ActorWorkflow, digest
from .contracts import RequestRecord
from .graph_storage import JournalRecords


@dataclass(frozen=True, slots=True)
class PartitionRetryAdmission:
    request_attempt: int
    plan: JoinRetryPlan
    evidence_sha256: str


def stage_partition_retry(
    row: RequestRecord,
    flow: ActorWorkflow,
    graph: TaskGraph,
    records: JournalRecords,
    *,
    partition_id: str,
    definition_revision: int,
    join_revision: int,
) -> Result[tuple[JoinRetryPlan, str]]:
    """Pure staging: no join persistence, Agent restoration, or Request admission."""
    if (
        tuple(s.kind for s in flow.steps) != ("read", "read", "collect")
        or flow.graph_sha256 is None
        or str(definition_revision) != flow.version
        or type(definition_revision) is not int
        or type(join_revision) is not int
        or join_revision != 1
        or partition_id != flow.steps[1].step_id
    ):
        return policy_rejection("partition_retry", "exact two-read authored definition required")
    first, failed, collect = flow.steps
    edge = next(
        (e for e in graph.edges if e.from_node == failed.step_id and e.to_node == collect.step_id),
        None,
    )
    if edge is None or edge.mapping is not EdgeMapping.ONE:
        return policy_rejection("partition_retry", "exact authored collect edge required")
    refusal = records.get("partition_refusal", row.request_id)
    expected = {
        "request_id": row.request_id,
        "request_attempt": row.attempt,
        "partition_id": failed.step_id,
        "tool": failed.tool,
        "arguments_json": failed.arguments_json,
        "reason": "pre_dispatch_context_refused",
    }
    if refusal is None or any(refusal.get(k) != v for k, v in expected.items()):
        return policy_rejection("partition_retry", "known original pre-dispatch refusal required")
    stamp = refusal.get("occurred_at")
    if not isinstance(stamp, str):
        return policy_rejection("partition_retry", "known refusal timestamp required")
    first_key, failed_key = (row.request_id + ":step:" + s.step_id for s in (first, failed))
    observed = records.get("effect", first_key)
    if (
        observed is None
        or observed.get("status") != "observed"
        or observed.get("tool") != first.tool
        or observed.get("input_hash")
        != hashlib.sha256(
            json.dumps(json.loads(first.arguments_json), sort_keys=True).encode()
        ).hexdigest()
        or not isinstance(observed.get("result"), dict)
        or records.get("effect", failed_key) is not None
    ):
        return policy_rejection(
            "partition_retry", "observed predecessor and never-dispatched failed read required"
        )
    opened = open_join(
        graph_run_id=graph.id,
        node_id=collect.step_id,
        edge_id=failed.step_id + ":" + collect.step_id,
        definition_revision=definition_revision,
        join_revision=join_revision,
        mapping=edge.mapping,
        expected_cardinality=2,
        duplicate_key_policy=DuplicateKeyPolicy.REFUSE,
    )
    if is_refusal(opened):
        return opened
    state = opened.value
    for step, key, status, identity in (
        (first, first_key, JoinPartitionStatus.DONE, first_key),
        (failed, failed_key, JoinPartitionStatus.FAILED, None),
    ):
        applied = apply_join_arrival(
            state,
            JoinArrival(
                step.step_id,
                key,
                stamp,
                stamp,
                status=status,
                logical_invocation_id=key,
                result_identity=identity,
            ),
        )
        if is_refusal(applied):
            return applied
        state = applied.value
    planned = plan_partial_retry(
        state, definition_revision=definition_revision, join_revision=join_revision
    )
    if is_refusal(planned):
        return planned
    return Ok((planned.value, digest([refusal, observed])))
