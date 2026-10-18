# The template pack

QMX ships 31 workflow templates as working defaults (ruling 83). Each one is a workflow folder under `src/qmx_engine/templates/`, and each one is meant to be edited with the copilot as the operator uses QMX. Nine run today. The other 22 are complete definitions that validate, and each one names the piece of QMX it waits for in `meta.needs`. A draft's test run and its enable are refused until that piece exists, and the refusal names it.

`templates install` puts the pack on a home. The nine runnable templates are test-run, published at 0.1.0 and given their card's schedule, all disabled. The drafts are saved and go no further. A second install changes nothing. Nothing in the pack is ever enabled for him: enabling is his act.

```
uv run --no-sync python -m qmx_engine templates install --home <home>
uv run --no-sync python -m qmx_engine templates list --home <home>
```

## The 31 templates

Status is what `templates install` leaves on a fresh home. Test cost is what the template's last test run on the cheapest test models cost, where a PR measured it. Triggers are the ways a run can start: a cron trigger is installed disabled, and manual means he or the copilot starts it.

| Id | Template | Status | Test cost | Triggers | Needs |
|---|---|---|---|---|---|
| RS1 | Paper scout to research note | published, disabled | TP1 lane 2: 5 Kimi spans; 47k in, 8k out, 86k cache read; 233 s | cron `0 */6 * * *` UTC, manual | none |
| T3 | News and macro calendar watch | published, disabled | TP1 lane 3: quiet day 0 tokens, 1 s; surprise day 1 Kimi span, 6k in, 1k out | cron `5 0 * * *` UTC, manual | none |
| RS0 | Idea grill to term sheet | published, disabled | not measured yet | manual | none |
| RS2 | Source to component card | published, disabled | not measured yet | manual | none |
| RS4 | Literature review on a topic | published, disabled | not measured yet | manual | none |
| A | Fill the Library, funnel stages 1 to 7 | published, disabled | not measured yet | manual | none |
| RV | Weekly review | published, disabled | not measured yet | cron `0 6 * * 1` UTC, manual | none |
| DB | Desk brief | published, disabled | not measured yet | cron `0 6 * * 1-5` Europe/London, cron `30 7 * * 1-5` America/New_York, cron `5 17 * * 1-5` America/New_York, manual | none |
| T4 | Research desk overnight | published, disabled | not measured yet | cron `0 3 * * 0-4` Europe/London, manual | none |
| DM | Demo monitor and execution quality | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| T7 | Trade journal review in R | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| GW | Guard watchdogs | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| RK2 | Correlation and exposure drift | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| DC | Decay and limit report | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| RK5 | Stress tests | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| RK8 | Incident post-mortem | draft | none until it can run | manual | `trading-node` |
| P1 | Portfolio combination study | draft | none until it can run | manual | `trading-node`, `risk-session` |
| P2 | Daily book report | draft | none until it can run | cron (schedule not set yet), manual | `broker-read-token` |
| PP | Proposal pack he signs | draft | none until it can run | manual | `trading-node`, `risk-session` |
| B | Build and prove, funnel stages 8 to 12 | draft | none until it can run | manual | `qmb-door` |
| RS3 | Source to a Lab test | draft | none until it can run | manual | `qmb-door` |
| RS6 | Hypotheses from dead ends | draft | none until it can run | cron `0 5 * * 1` UTC, manual | `real-library` |
| RS8 | Big-data question | draft | none until it can run | manual | `rlm` |
| L1 | Idea to first result | draft | none until it can run | manual | `qmb-door` |
| L4 | Overnight Lab loop | draft | none until it can run | cron `0 23 * * *` Europe/London, manual | `qmb-door` |
| BC | Build a component or indicator | draft | none until it can run | manual | `sandbox` |
| D3 | Iterate against QMB with overfit guards | draft | none until it can run | manual | `qmb-door` |
| D4 | Variant generation and comparison | draft | none until it can run | manual | `qmb-door` |
| D6 | ML training run with a holdout | draft | none until it can run | manual | `qmb-door`, `sandbox` |
| MA | Mini app lifecycle | draft | none until it can run | manual | `sandbox`, `app-op` |
| D9 | Mini-app-to-mini-app pipeline | draft | none until it can run | manual | `app-op` |

`scripts/live/engine/t_templates.py doc` checks this table against the catalogue (`templates/catalog.py`) and every definition. Run it after any change to the pack.

## What each need waits for

| Need | What the template waits for | Templates |
|---|---|---|
| `trading-node` | The trading node's read-only readers: the guard, the deal feed and the unit adapter. | DM, T7, GW, RK2, DC, RK5, RK8, P1, PP |
| `risk-session` | The risk session's rulings on sizing and limits. | P1, PP |
| `broker-read-token` | The read-only broker token. | P2 |
| `qmb-door` | QMB's doors for agents: spec compile and register, backtest, walk-forward, robustness, the sealed holdout and the family ledger. | B, RS3, L1, L4, D3, D4, D6 |
| `real-library` | The real Library, with its dead-end rows and workflow memory. The engine runs on a SQLite fake until then. | RS6 |
| `rlm` | The `rlm` node kind and its research kernel. | RS8 |
| `sandbox` | The Lab sandbox, where an agent can write and built code runs. Until then every agent ask is rejected. | BC, D6, MA |
| `app-op` | The host's app operations: list, consumers, `qmx app check` and the pipelines doors. | MA, D9 |

Each draft keeps its waiting in one place. The script that would call the missing piece (for example `scripts/qmb.py` in B) states in its docstring what it would read and the shape of its answer, writes one line naming the need, and exits. Every other script in the draft is real: the gates, the checks and the verdicts run today on synthetic inputs. Each draft's `README.md` names its need in the line under its title, lists its steps, and says what was left out and why.

## Edit a template with the copilot

He asks the copilot in his own words, for example "make a paper scout for FX papers only". The copilot works on drafts; nothing it does changes a published version.

1. **Clone it as a variant.** The copilot saves a new draft whose definition `extends` the published template (its workflow id and version id) with a list of patches, such as a changed timezone, prompt or threshold. The variant keeps everything else from its parent, and once published it records the version it is a variant of.
2. **Or edit the template's own draft.** The copilot opens the draft, edits nodes, prompts, schemas or scripts, and saves it. Saving a draft never asks.
3. **Test it.** The copilot test-runs the draft on the cheapest test models with the catalogue's test inputs (the template's fixtures). A test run never asks. A run whose output carries a number its sources never gave fails its last check, render and grade, and nothing is delivered.
4. **Publish it.** Publishing needs a passing test of the exact content, and asks him once. The new version is published disabled, next to the old one, which stays for rollback.
5. **Enable it.** Enabling a version or a trigger is his act, never the copilot's.

A draft that waits for a need can be edited and saved the same way, but its test run and its enable are refused until the need exists.

## Make a draft runnable

When the piece a draft waits for lands, its PR replaces the waiting script with the real call, adds fixtures that match the real answer's shape, removes the need from `meta.needs` and from the catalogue row, records the template's test inputs, and adds one unit case that a planted number in its output fails the test run. `test_templates.py` then holds it to the same rules as the nine runnable templates.

## Rules every template keeps

- Render and grade is the last check. Its evidence is only source data: cited claims, source sections and script results. A model-written output is never its own evidence, and every prose field that can carry a number is listed in the output schema's `x-prose`.
- Shared blocks live in `templates/_shared/`. A run holds only its own folder, so a template carries a byte-identical copy of each block file it uses, and `catalog.SHARED_COPIES` lists every copy. `test_templates.py` fails when a copy drifts.
- No template names a money act or holds a credential. Every proposal (a bench, a tightening, a promotion, an install) ends as a card for his click.
- Synthetic fixtures are labelled as synthetic. Data is held (ruling 91).
