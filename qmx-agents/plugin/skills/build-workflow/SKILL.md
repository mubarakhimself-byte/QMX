---
name: build-workflow
description: Build, validate and test-run a QMX workflow from one line of the operator's intent. Use when he describes a routine or automation he wants, when he asks to change or test a workflow, or when he asks what a workflow would cost to run.
allowed-tools: mcp__qmx__workflows_drafts_get mcp__qmx__workflows_drafts_put mcp__qmx__workflows_get mcp__qmx__workflows_put mcp__qmx__workflows_tests_run mcp__qmx__workflows_validate mcp__qmx__workflows_versions_list
---

# Build a workflow

He gives you one line. You give him a tested draft and a publish card. He never sees a form.

"Every weekday at 7, pull the ECB calendar, summarise it, and save it to the Library" is a whole
request. Do not ask him what a trigger is, which model to use, or where the Library is. Build the
thing, run it, show it.

## What you promise

- A draft, not a published workflow. You never publish and you never enable. `workflows_put`
  answers you with a card, and the card's button is his click (AD-11, AD-22).
- Saving the draft and test-running it never ask him. They are `domain_write` rows. Nothing in
  this skill needs a permission prompt.
- The draft lands on his Library draft ref. Nothing you write reaches `main`.
- A test run that spends as little as the workflow allows. Cheap roles, and a fake run only when
  he asked for a dry run.

## The six phases

BMad's phases, in order. They are steps in your head, not messages to him. Speak to him once,
at the end, unless a question in phase 1 cannot be answered from his line.

### 1. Discover intent: the loop-me interview

The interview fills exactly three things, and nothing else:

- **Trigger.** What starts it, and when. "Every weekday at 7" is a cron trigger. "When I click
  run" is manual. "When the source changes" is a monitor.
- **Checkpoints pushed as late as possible.** Where it waits for him, if anywhere. The default is
  nowhere: a run does not stop for him (ruling 57). A checkpoint costs a `wait` node and his
  attention, so add one only when he asks for a review before an irreversible act.
- **Brief.** One paragraph he would recognise as the job: the source, the transformation, the
  result, and where the result goes.

Ask at most three numbered questions, each with a recommended answer, and treat "yes" as
accepting all of them. Ask only what changes the graph. If his line already says it, do not ask
it. If he answered it a sentence ago, do not ask it again. `references/interview.md` holds the
question bank: pick from it, never send the whole list.

### 2. Classify

Decide the shape before you write JSON:

- **Script only.** Deterministic work: fetch, parse, filter, compute, write. No model node, so a
  run spends no tokens. Prefer this whenever the job is arithmetic or retrieval.
- **Mixed.** A script fetches and shapes, an `llm` node reads and summarises or classifies, a
  script assembles. This is the common shape.
- **Fully agentic.** The work needs judgement across tools, so one `agent` node does it. A single
  agent is still a workflow (ruling 44): it gets a trigger, a run record and the Library, like
  any other.

Say the classification to yourself with one reason. It decides the roles and the cost line you
show him.

### 3. Gather requirements

Collect, in this order, only as far as the shape needs them:

- The trigger kind and its schedule, in his words and in cron.
- The folder files the workflow needs: one script per deterministic step, a prompt per model
  step, a schema where a model's answer must be shaped.
- The role for each model node (`writer`, `scanner`, `judge`, and the rest of the role table).
  Never pin a model in the definition: settings map roles to models (AD-13).
- The `outputs` the run produces, which is also what lands in the Library when the run ends.

### 4. Draft

Write one graph with `mcp__qmx__workflows_drafts_put`. The call takes
`{"definition": ..., "files": {...}, "expected_revision": n}`: the definition is the graph,
`files` are the folder's text files keyed by their path. `expected_revision` is the draft's
current revision, `0` for a new draft, or the `draft_revision` you read from
`mcp__qmx__workflows_drafts_get`.

`references/graph.md` has the shape, the node table and a worked three-node example. Follow it
exactly: the validator is strict about node ids, connection keys (node name, not id), ports and
one trigger.

### 5. Build with a deterministic lint gate

Call `mcp__qmx__workflows_validate` with the same graph. It returns `valid`, `content_hash` and
`problems`, each problem with a `kind`, a `where` and a `message`. Every problem is yours to fix.
Fix, save the draft again with the new `expected_revision`, and validate again until `problems`
is empty. Do not show him a draft that has not validated.

Two refusals are not yours to fix: a `needs_unmet` problem names a setting or tool the run needs
(show it to him in one line, keep the draft), and an unknown node type means the executor is not
built yet. Pick an available kind from `references/graph.md` instead of inventing a type.

### 6. Optimise, then test-run

Test-run the draft with `mcp__qmx__workflows_tests_run`, whole (no `subgraph`) and with
`fake: false`. A test run uses the cheap end of each role's list through the plan login, so it
costs a haiku call per model node. Pass `fake: true` only when he asked for a dry run or when you
must show the graph without spending.

The answer is `{"run": ..., "report": ...}`. The draft is **tested** when a run with status
`passed` ran the same `content_hash`. A real edit changes the hash and loses the mark, so test
after your last edit, never before it.

If the report fails, read the failing node's error, fix the graph or its script, save, validate
and test again. A test run that fails twice on the same node is a fact about the request: tell
him what failed and what you would change, and keep the draft.

## Showing him the result

One short message. It names: the workflow in his words, the trigger, the nodes in order with
their kinds, the cost line (`0` tokens for a script-only shape, otherwise the roles and that it
ran on the cheap end), the test result, and that it is a draft on his draft ref.

Then call `mcp__qmx__workflows_put` with `{}` (or a `semver` he asked for) to get the publish
card. Do not call it before the draft is tested. Show the card. His click publishes; a second
card, from `mcp__qmx__workflows_triggers_create`, arms the schedule. You stop after handing him
the cards.

## Things you never do

- Never publish, enable, disable or archive. Those are his acts, and the service answers you with
  a card instead (AD-11).
- Never write a definition with `mcp__qmx__library_save` or a file write. The draft goes through
  `workflows_drafts_put` only, so it passes the same validation and test gate as a hand-built
  one.
- Never invent a node type, a port or a tool name. If the graph needs a capability the registry
  does not have, say which one and leave the draft at that point.
- Never claim a test passed without a `report` whose status is `passed`.
