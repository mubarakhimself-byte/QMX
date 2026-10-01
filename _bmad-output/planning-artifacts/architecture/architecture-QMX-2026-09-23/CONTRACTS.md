---
name: Contracts — pack-and-grant kit
sitting: architecture-QMX-2026-09-23
---

# Contracts

Parent `architecture-QMX-2026-09-18/CONTRACTS.md` remains the envelope, GrantRecord, JobHandle, and pack-lifecycle authority. This file only adds what that sitting left silent.

## 1. Pack SDK surface (request, not grant)

A pack manifest **requests**:

- `contributes`: list of `{point, local_id}` for operations only (parent AD-2)
- optional `view:*` wire DTOs (parent AD-17) — not a contribution point
- optional `copilot_profile` request blob — not a contribution point, not a grant
- `requested_capabilities` — **request**

Host **grants** GrantRecords into a `psess:`. Absence of `copilot_profile` is valid.

## 2. Envelope caller

Parent InvocationEnvelope plus:

```text
caller_kind: user | agent | workflow
```

Same `logical_invocation_id` / `attempt_id` / effect-class retry as parent AD-24.

## 3. Authoring instance

Named parent amendment: `app_instance_id` optional when `profile=authoring`. Required when `profile=app-use`. `selected_refs` may include kind `instance_id`. Authoring with no session instance invokes only when exactly one `instance_id` is selected; envelope `instance_id` is still required.

## 4. Nested workflow

Callee identity: Graph Template `(qualified_id, version)`. Lifecycle verbs: `start` | `query-state` | `cancel` | `await`. Result is a JobHandle. No merge of live Task Graphs.

## 5. Diagnosis

Headless query returns:

| Field | Meaning |
| --- | --- |
| `failure_class` | `grant` \| `workflow` \| `view` \| `dependency` \| `host` |
| `job_handle` | parent JobHandle or null |
| `correlation_id` | join key |
| `healthy` | listing axis |

## 6. Operator log line (daemon)

JSON-lines, stdlib logging. Required: `ts`, `level`, `event`, `correlation_id`. When known: `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Never secret values. Never a journal.

## 7. Adapters

json-render catalog `action` names an existing `op_id`. MCP App `tools/call` is intercepted by the host against the session GrantRecord.
