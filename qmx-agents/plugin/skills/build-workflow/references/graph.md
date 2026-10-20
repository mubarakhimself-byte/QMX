# The workflow graph

The long form, for whoever edits the skill. A build never reads this file: a chat cannot open a
file beside the plugin without asking him, and nothing in a build may ask, so `SKILL.md` carries
what the copilot needs. Keep the two in step when the definition format changes.

A draft is the document below plus its folder's text files. Save both in one
`workflows_drafts_put` call, `{"definition": {...}, "files": {"scripts/pull.py": "..."}}`.

## The document

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

- `schema` is always `qmx.workflow/1`. `id` is lowercase words joined by hyphens and matches the
  workflow you are drafting. `name` is the plain title he sees on the shelf.
- `outputs` describes what a run produces. The run's output files and its summary land in the
  Library when the run ends, so a request that ends "and save it to the Library" needs no extra
  node: say so in `outputs`.
- `settings.timezone` is the zone a cron expression is read in. `on_error` is `park` for anything
  he runs on a schedule. Do not set `meta.needs` unless the workflow really waits for a piece of
  QMX that does not exist; a need keeps the draft out of test runs and enable.

## Nodes

Every node has `id`, `name`, `type`, `typeVersion` (all `1`), `parameters`, and optionally
`position`, `effect`, `retry`, `runs_on` (default `"pc"`). `connections` is keyed by node
**name**, not id, so give every node a distinct name.

The kinds an executor exists for, with their ports:

| type | in | out | parameters | use |
|---|---|---|---|---|
| `trigger` | none | `main` | `kinds`: list of `manual`, `cron`, `event`, `webhook` | the one entry node |
| `script` | `in` | `main` | `script`: path in the folder | deterministic work |
| `rule` | `in` | `true`, `false` | `expr`: a boolean expression over `items` | branch without a model |
| `monitor` | `in` | `changed`, `silent` | `source`, `wake_when`, fixtures | wake only when a source moved |
| `llm` | `in` | `main` | `prompt_ref`, `schema_ref`, `recording_ref` | one model call; `role` required |
| `agent` | `in` | `main` | `prompt_ref`, `max_turns`; `role` required; `toolsets` | a full chat with tools |
| `grader` | `in` | `pass`, `fail` | `mode`: `deterministic` with `script`, or `llm` with `role` | a check that can fail |
| `join` | `in` | `main` | none | wait for every branch |
| `loop` | `in`, `next` | `body`, `done` | `over`, `max_iterations` | the one cycle a graph may hold |
| `wait` | `in` | `main` | `seconds`, or `until` | a checkpoint he asked for |
| `subworkflow` | `in` | `main` | `workflow`, `inputs` | call another workflow |
| `app_op` | `in` | `main` | the catalog row's arguments | an app's operation |

`library`, `human_gate`, `rlm` and `claude_workflow` have no executor at this head. Validation
refuses them, so never draft one.

A `grader` in `mode: llm` needs a `role`; in `deterministic` mode it must not carry one.

## Connections

```json
"connections": {
  "Start": {"main": [[{"node": "Pull the calendar", "port": "in", "map": "one"}]]},
  "Pull the calendar": {"main": [[{"node": "Summarise", "port": "in", "map": "one"}]]}
}
```

The outer key is the source node's name, the inner key is its output port, then a list of fan-out
groups, then the targets. `map` is `one` unless the edge really fans a list: `zip` pairs two
lists, `broadcast` copies one value to many, `chunk` splits a list, `cartesian` and `keyed-join`
are the join shapes.

## A worked three-node draft

The request: "every weekday at 7, pull the ECB calendar, summarise it, and save it to the
Library". Three nodes, one model call, one script:

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
    "scripts/pull_ecb.py": "...",
    "prompts/summarise.md": "...",
    "schemas/summary.json": "..."
  },
  "expected_revision": 0
}
```

## The folder files

- A script reads no engine state. Its inputs arrive as JSON on stdin, its answer is JSON on
  stdout. It writes only inside `QMX_WORK`, its own overlay.
- `QMX_MODE` is `test` or `live`, and `QMX_NOW` carries the clock, so a script that needs the date
  reads `QMX_NOW` instead of `datetime.now()`.
- A prompt is markdown with the instruction and no model name in it. The role picks the model.
- A schema is a JSON Schema object. The model's answer is parsed against it, so keep it small and
  literal.

## The schedule is not a node

A `trigger` node declares the *kinds* that may start the workflow. The cron row itself is a
trigger object made after publish, and making one is his act: `workflows_triggers_create` answers
you with an enable card. Say the schedule in the node's name (`Weekdays at 07:00`) and in your
message, and let the card carry it.
