---
name: build-workflow
description: Build, validate and test-run a QMX workflow from one line of the operator's intent. Use when he describes a routine, schedule, automation or recurring job, or asks to build, change, test or publish a workflow.
allowed-tools: mcp__qmx__workflows_drafts_get mcp__qmx__workflows_drafts_put mcp__qmx__workflows_get mcp__qmx__workflows_put mcp__qmx__workflows_tests_run mcp__qmx__workflows_validate mcp__qmx__workflows_versions_list
---

# Build a workflow

He gives you one line. You give him a tested draft and a publish card. He never sees a form.

"Every weekday at 7, pull the ECB calendar, summarise it, and save it to the Library" is a whole
request. Do not ask him what a trigger is, which model to use, or where the Library is. Build the
thing, run it, show it.

This file is self-contained. A chat cannot read a file beside the plugin without asking him, and
nothing in a build may ask, so never reach for another file to finish a build.

## What you promise

- A draft, not a published workflow. You never publish and you never enable. `workflows_put`
  answers you with a card, and the card's button is his click (AD-11, AD-22).
- Saving the draft and test-running it never ask him. They are `domain_write` rows. Nothing in
  this skill needs a permission prompt, and nothing needs a file read or a shell command.
- The draft lands on his Library draft ref, from your chat's own agent ref. Nothing you write
  reaches `main`.
- A test run that spends as little as the workflow allows.

## The six phases

BMad's phases, in order. They are steps in your head, not messages to him. Speak to him once, at
the end, unless a question in phase 1 cannot be answered from his line.

### 1. Discover intent: the loop-me interview

The interview fills exactly three things, and nothing else:

- **Trigger.** What starts it, and when. "Every weekday at 7" is a cron trigger. "When I click
  run" is manual. "When the source changes" is a monitor.
- **Checkpoints pushed as late as possible.** Where it waits for him, if anywhere. The default is
  nowhere: a run does not stop for him (ruling 57). A checkpoint costs a `wait` node and his
  attention, so add one only when he asked for a review before an irreversible act.
- **Brief.** One paragraph he would recognise as the job: the source, the transformation, the
  result, and where the result goes.

Ask at most three numbered questions, each with the recommended answer first, and treat "yes" as
accepting all of them. Ask only what changes the graph. If his line already says it, do not ask
it. If he answered it a sentence ago, do not ask it again.

The questions worth asking, in his words:

- "Does this run on a clock, or when you click run?" Recommended: the clock he implied, plus
  manual, so he can try it once.
- "Which days, and at what hour, in your timezone?" Recommended: weekdays at the hour he named,
  else 07:00 Europe/Berlin.
- "Should it stop and show you the result before it sends anything?" Recommended: no, unless the
  last node is an external send or a trade.
- "Where does the result go?" Recommended: the Library, as the run's output, unless he named a
  channel.

"Should the digest be saved in the Library with the rest of your notes?" beats "confirm the
outputs block". If he says "yes", take every recommendation and build.

### 2. Classify

Decide the shape before you write JSON:

- **Script only.** Deterministic work: fetch, parse, filter, compute, write. No model node, so a
  run spends no tokens. Prefer this whenever the job is arithmetic or retrieval.
- **Mixed.** A script fetches and shapes, an `llm` node reads and summarises or classifies, a
  script assembles. This is the common shape.
- **Fully agentic.** The work needs judgement across tools, so one `agent` node does it. A single
  agent is still a workflow (ruling 44): it gets a trigger, a run record and the Library.

### 3. Gather requirements

Only as far as the shape needs them:

- The trigger kind and its schedule, in his words and in cron.
- The folder files: one script per deterministic step, a prompt per model step, a schema where a
  model's answer must be shaped.
- The role for each model node (`writer`, `scanner`, `judge`, and the rest of the role table).
  Never pin a model in the definition: settings map roles to models (AD-13).
- The `outputs` the run produces, which is also what lands in the Library when the run ends.

### 4. Draft

Write one graph with `mcp__qmx__workflows_drafts_put`. The call takes
`{"definition": ..., "files": {...}, "expected_revision": n}`: the definition is the graph, and
`files` are the folder's text files keyed by their path. `expected_revision` is the draft's
current revision, `0` for a new draft, or the `revision` you read from
`mcp__qmx__workflows_drafts_get`.

The document:

```json
{
  "schema": "qmx.workflow/1",
  "id": "weekday-ecb-digest",
  "name": "Weekday ECB digest",
  "inputs": {},
  "outputs": {"type": "object", "description": "the day's calendar in one paragraph"},
  "settings": {"timezone": "Europe/Berlin", "on_error": "park", "caller_policy": "any"},
  "nodes": [],
  "connections": {},
  "meta": {}
}
```

- `id` is lowercase words joined by hyphens, and it is the workflow's id everywhere.
- `name` is the plain title he sees on the shelf.
- `outputs` describes what a run produces. The run's output files and its summary land in the
  Library when the run ends, so a request that ends "and save it to the Library" needs no extra
  node: say so in `outputs`.
- `settings.timezone` is the zone a cron expression is read in. `on_error` is `park` for anything
  on a schedule.

Every node has `id`, `name`, `type`, `typeVersion` (always `1`), and `parameters`, plus
optionally `position`, `effect`, `role` and `retry`. Give every node a distinct, plain `name`:
`connections` is keyed by name, not id.

The kinds an executor exists for:

| type | in | out | parameters | use |
|---|---|---|---|---|
| `trigger` | none | `main` | `kinds`: some of `manual`, `cron`, `event`, `webhook` | the one entry node |
| `script` | `in` | `main` | `script`: a path in the folder | deterministic work |
| `rule` | `in` | `true`, `false` | `expr`: a boolean expression over `items` | a branch with no model |
| `monitor` | `in` | `changed`, `silent` | `source`, `wake_when`, fixture refs | wake only when a source moved |
| `llm` | `in` | `main` | `prompt_ref`, `schema_ref`; `role` required | one model call |
| `agent` | `in` | `main` | `prompt_ref`, `max_turns`; `role` required; `toolsets` | a chat with tools |
| `grader` | `in` | `pass`, `fail` | `mode`: `deterministic` with `script`, or `llm` with `role` | a check that can fail |
| `join` | `in` | `main` | none | wait for every branch |
| `loop` | `in`, `next` | `body`, `done` | `over`, `max_iterations` | the one cycle a graph may hold |
| `wait` | `in` | `main` | `seconds`, or `until` | a checkpoint he asked for |
| `subworkflow` | `in` | `main` | `workflow`, `inputs` | call another workflow |
| `app_op` | `in` | `main` | the catalog row's arguments | an app's operation |

`library`, `human_gate`, `rlm` and `claude_workflow` have no executor yet. Never draft one.

Connections name the source node, its output port, then a list of fan-out groups, then targets:

```json
"connections": {
  "Weekdays at 07:00": {"main": [[{"node": "Pull the ECB calendar", "port": "in", "map": "one"}]]},
  "Pull the ECB calendar": {"main": [[{"node": "Summarise", "port": "in", "map": "one"}]]}
}
```

`map` is `one` unless the edge really fans a list (`zip`, `broadcast`, `chunk`, `cartesian`,
`keyed-join`).

A worked three-node draft for the ECB request:

```json
{
  "definition": {
    "schema": "qmx.workflow/1",
    "id": "weekday-ecb-digest",
    "name": "Weekday ECB digest",
    "outputs": {"type": "object", "description": "the day's ECB calendar as one paragraph"},
    "settings": {"timezone": "Europe/Berlin", "on_error": "park"},
    "nodes": [
      {"id": "start", "name": "Weekdays at 07:00", "type": "trigger", "typeVersion": 1,
       "position": [0, 0], "parameters": {"kinds": ["cron", "manual"]}},
      {"id": "pull", "name": "Pull the ECB calendar", "type": "script", "typeVersion": 1,
       "position": [220, 0], "effect": "none",
       "parameters": {"script": "scripts/pull_ecb.py"}},
      {"id": "summarise", "name": "Summarise", "type": "llm", "typeVersion": 1,
       "position": [440, 0], "role": "writer", "effect": "none",
       "parameters": {"prompt_ref": "prompts/summarise.md", "schema_ref": "schemas/summary.json"}}
    ],
    "connections": {
      "Weekdays at 07:00": {"main": [[{"node": "Pull the ECB calendar", "port": "in", "map": "one"}]]},
      "Pull the ECB calendar": {"main": [[{"node": "Summarise", "port": "in", "map": "one"}]]}
    },
    "meta": {}
  },
  "files": {
    "scripts/pull_ecb.py": "import json, os, urllib.request\n...",
    "prompts/summarise.md": "Summarise the calendar below in one paragraph...",
    "schemas/summary.json": "{\"type\": \"object\", \"required\": [\"summary\"]}"
  },
  "expected_revision": 0
}
```

The folder files:

- A script takes JSON on stdin and answers JSON on stdout. It reads engine state nowhere. It
  writes only inside `QMX_WORK`, its own overlay, and it takes the clock from `QMX_NOW` rather
  than `datetime.now()`.
- A prompt is markdown holding the instruction, with no model name in it. The role picks the
  model.
- A schema is a small JSON Schema object the model's answer is parsed against.

The schedule is not a node. A `trigger` node declares the kinds that may start it; the cron row
is a trigger object made after publish, and making one is his act, so say the schedule in the
trigger node's name and in your message.

### 5. Build with a deterministic lint gate

Call `mcp__qmx__workflows_validate` with the same `{"definition": ..., "files": ...}`. It returns
`valid`, `content_hash` and `problems`, each with a `kind`, a `where` and a `message`. Every
problem is yours to fix: fix, save the draft again with the new `expected_revision`, and validate
again until `problems` is empty. Do not show him a draft that has not validated.

Two refusals are not yours to fix: a `needs_unmet` problem names a setting or tool the run needs,
so show it to him in one line and keep the draft, and an unknown node type means the executor is
not built yet, so pick an available kind from the table instead of inventing one.

### 6. Optimise, then test-run

Test-run the draft with `mcp__qmx__workflows_tests_run`: the whole graph (no `subgraph`) and
`fake: false`. A test run uses the cheap end of each role's list, so it costs one model call per
model node. Pass `fake: true` only when he asked for a dry run or when you must show the graph
without spending.

The answer is `{"run": ..., "report": ...}`. The draft is tested when a run with status `passed`
ran the same `content_hash`, so test after your last edit: an edit changes the hash and loses the
mark. If the report fails, read the failing node's error, fix, save, validate and test again. A
test run that fails twice on the same node is a fact about the request: tell him what failed and
keep the draft.

## Showing him the result

One short message. It names the workflow in his words, the trigger, the nodes in order with their
kinds, the cost line (no tokens for a script-only shape, otherwise the roles and that it ran on
the cheap end), the test result, and that it is a draft on his draft ref.

Then call `mcp__qmx__workflows_put` with `{}` (or a `semver` he asked for) to get the publish
card. Do not call it before the draft is tested. Show the card. His click publishes; a second
card, from the trigger row, arms the schedule. You stop after handing him the cards.

## Things you never do

- Never publish, enable, disable or archive. Those are his acts, and the service answers you with
  a card instead (AD-11).
- Never write a definition with `library_save` or a file write. The draft goes through
  `workflows_drafts_put` only, so it passes the same validation and test gate as a hand-built one.
- Never invent a node type, a port or a tool name. If the graph needs a capability the registry
  does not have, say which one and stop at that point.
- Never claim a test passed without a `report` whose status is `passed`.
