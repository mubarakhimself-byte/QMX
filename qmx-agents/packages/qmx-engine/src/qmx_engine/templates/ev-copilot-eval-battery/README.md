# EV Copilot eval battery

Built from DC-10 in `research/methodology/44-agentic-engineering-foundations.md` (engine AD-66). It tests the copilot like a workflow: a set of tasks runs three times on the model a change concerns, every answer is graded, and the report gives pass^3 per task. A task passes only when all three tries pass.

## Steps

1. `Tasks and the surface under test` takes the tasks and the slot text from the run input. Tasks are the Library items tagged `eval-task`. The slot text is the persona, methodology and skills index text under test, empty for the plain model.
2. `Brief without the grades` keeps each task's id and prompt only, so no try sees what it is graded against.
3. `Try 1`, `Try 2` and `Try 3` (role `writer`) each answer every task once, in their own chats. Each try is one model turn.
4. `Grade by code` checks every try of a code-graded task: `matches`, `contains`, `excludes`, `json_keys`, `count` and `max_chars`. A try with no answer fails.
5. `Judge the rest` (role `judge`) grades the other tries against each task's rubric.
6. `pass^3 per task` folds the verdicts into the report. `Render and grade` checks the report against `schemas/output.json`. A task failing its pass^3 is the battery's finding, not a failed run.

## Running it on a change

`qmx_engine.templates.battery.run` runs the template once per side, with the roles pinned. For a change of the copilot's default model, the new model is the candidate and the current one the baseline. For a persona, methodology or skill draft, the draft's text is the candidate and the published text the baseline, both on the current default model. The judge is the first `judge` candidate of a family that no graded model is from. When there is none, the result labels it `same_family`. A side whose tries ran on another model, because its row was unavailable and the ladder moved on, reports no pass^3.

The caller saves the result with `qmx_control.service.eval_run_input`. The Settings model card and the draft's publish card then read it. Nothing waits on the battery, and publishing stays the operator's click.

## Test runs

A run started with `{"fixture": true}` reads the 20 seed tasks in `fixtures/tasks.json`. They come from the B-51 and B-70 class (a turn with no tools must not claim or call one) and from the operator's recorded rulings: money acts are proposals only, no QMX usage caps, keys stay in the keyring, plain words, and honest answers. The answers in `fixtures/recorded/` serve the `--fake` switch and the unit tests. Test mode resolves every role to `claude/haiku` first. Only a row named in `roles.test_only` runs another provider, in a provider-proof lane.

## Left out, and why

- A try is a tool-less model turn, not a full copilot chat with its tools. The surface digest on the card is a sha256 over the slot text the battery passed, not the harness's whole Surface digest.
- Starting a battery when he opens a change card needs a door on the engine host, so the caller starts it today.
