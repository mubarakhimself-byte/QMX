# The template pack

QMX ships 31 workflow templates as working defaults (ruling 83). Each one is a workflow folder under `src/qmx_engine/templates/`, and each one is meant to be edited with the copilot as the operator uses QMX. Ten run today. The other 22 are complete definitions that validate, and each one names the piece of QMX it waits for in `meta.needs`. A draft's test run and its enable are refused until that piece exists, and the refusal names it.

`templates install` puts the pack on a home. The ten runnable templates are test-run, published at 0.1.0 and given their card's schedule, all disabled. The drafts are saved and go no further. A second install changes nothing. Nothing in the pack is ever enabled for him: enabling is his act.

```
uv run --no-sync python -m qmx_engine templates install --home <home>
uv run --no-sync python -m qmx_engine templates list --home <home>
```

## Names and ids

Every template's title says in plain words what it does, and its id is a plain phrase (ruling 35, SOLUTION-DESIGN 26.9). The code prefix is gone from the id: `rs1-paper-scout` is still the folder, and the template answers to `paper-scout-to-research-note`. `templates/catalog.py` keeps every old id in `ALIASES`, so a script, a note or a copilot habit that names `RS1`, `rs1` or `rs1-paper-scout` finds the same template. The folder name is the workflow's id in the Library and does not change.

## The 32 templates

Status is what `templates install` leaves on a fresh home. Test cost is what the template's last test run cost on real models. At TP4 that is the plan login with every role on `claude/haiku` (`t_templates.py all-plan`). Triggers are the ways a run can start: a cron trigger is installed disabled, and manual means he or the copilot starts it.

| Id | Template | Status | Test cost | Triggers | Needs |
|---|---|---|---|---|---|
| paper-scout-to-research-note | Paper scout to research note | published, disabled | TP4 lane 2: 5 haiku spans, cache read 71k, out 10k, fresh in 0; 47 s | cron `0 */6 * * *` UTC, manual | none |
| news-and-macro-calendar-watch | News and macro calendar watch | published, disabled | TP4 lane 2, surprise day: 1 haiku span, cache read 15k, out 1k, fresh in 0; 7 s | cron `5 0 * * *` UTC, manual | none |
| rough-idea-to-test-plan | Question a rough idea until it is a clear test plan | published, disabled | TP4 lane 2: 2 haiku spans, cache read 33k, out 10k, fresh in 0; 53 s | manual | none |
| source-to-component-card | Source to component card | published, disabled | TP4 lane 2: 5 haiku spans, cache read 92k, out 4k, fresh in 0; 29 s | manual | none |
| literature-review-on-a-topic | Literature review on a topic | published, disabled | TP4 lane 2: 9 haiku spans, cache read 163k, out 25k, fresh in 0; 129 s | manual | none |
| video-to-strategy-ideas | Turn a video, a playlist or saved posts into strategy ideas | published, disabled | TP4 lane 2: 7 haiku spans, cache read 127k, out 8k, fresh in 0; 54 s | manual | none |
| weekly-review | Weekly review | published, disabled | TP4 lane 2: 2 haiku spans, cache read 33k, out 1k, fresh in 0; 17 s | cron `0 6 * * 1` UTC, manual | none |
| morning-market-brief | Morning market brief before each session | published, disabled | TP4 lane 2: 1 haiku span, cache read 15k, out 2k, fresh in 0; 13 s | cron `0 6 * * 1-5` Europe/London, cron `30 7 * * 1-5` America/New_York, cron `5 17 * * 1-5` America/New_York, manual | none |
| research-desk-overnight | Research desk overnight | published, disabled | TP4 lane 2: 4 haiku spans, cache read 66k, out 12k, fresh in 0; 50 s | cron `0 3 * * 0-4` Europe/London, manual | none |
| copilot-eval-battery | Copilot eval battery | published, disabled | EVAL lane 2: 4 haiku spans (3 tries and the judge), 40 s | manual | none |
| demo-trades-fill-quality | Watch demo trades and check fill quality | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| trade-journal-in-risk-units | Review my trade journal in risk units | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| trading-guards-alive | Check that the trading guards are alive | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| correlation-and-exposure-drift | Correlation and exposure drift | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| decay-and-limit-report | Decay and limit report | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| stress-tests | Stress tests | draft | none until it can run | cron (schedule not set yet), manual | `trading-node` |
| incident-post-mortem | Incident post-mortem | draft | none until it can run | manual | `trading-node` |
| portfolio-combination-study | Portfolio combination study | draft | none until it can run | manual | `trading-node`, `risk-session` |
| daily-book-report | Daily book report | draft | none until it can run | cron (schedule not set yet), manual | `broker-read-token` |
| change-bundle-for-approval | Bundle a change for me to approve | draft | none until it can run | manual | `trading-node`, `risk-session` |
| strategy-idea-to-paper-tested | Turn a strategy idea into a tested strategy, ending on paper | draft | none until it can run | manual | `qmb-door` |
| source-to-a-lab-test | Source to a Lab test | draft | none until it can run | manual | `qmb-door` |
| hypotheses-from-dead-ends | Hypotheses from dead ends | draft | none until it can run | cron `0 5 * * 1` UTC, manual | `real-library` |
| question-over-a-large-table | Answer a question over a large table | draft | none until it can run | manual | `rlm` |
| first-backtest-from-an-idea | Get a first backtest result from an idea | draft | none until it can run | manual | `qmb-door` |
| overnight-lab-loop | Overnight Lab loop | draft | none until it can run | cron `0 23 * * *` Europe/London, manual | `qmb-door` |
| build-a-component-or-indicator | Build a component or indicator | draft | none until it can run | manual | `sandbox` |
| iterate-against-qmb-with-overfit-guards | Iterate against QMB with overfit guards | draft | none until it can run | manual | `qmb-door` |
| variant-generation-and-comparison | Variant generation and comparison | draft | none until it can run | manual | `qmb-door` |
| ml-training-run-with-a-holdout | ML training run with a holdout | draft | none until it can run | manual | `qmb-door`, `sandbox` |
| mini-app-lifecycle | Mini app lifecycle | draft | none until it can run | manual | `sandbox`, `app-op` |
| connect-mini-apps | Connect one mini app's output to another | draft | none until it can run | manual | `app-op` |

`scripts/live/engine/t_templates.py doc` checks this table against the catalogue (`templates/catalog.py`) and every definition. Run it after any change to the pack.

## What each need waits for

| Need | What the template waits for | Templates |
|---|---|---|
| `trading-node` | The trading node's read-only readers: the guard, the deal feed and the unit adapter. | demo-trades-fill-quality, trade-journal-in-risk-units, trading-guards-alive, correlation-and-exposure-drift, decay-and-limit-report, stress-tests, incident-post-mortem, portfolio-combination-study, change-bundle-for-approval |
| `risk-session` | The risk session's rulings on sizing and limits. | portfolio-combination-study, change-bundle-for-approval |
| `broker-read-token` | The read-only broker token. | daily-book-report |
| `qmb-door` | QMB's doors for agents: spec compile and register, backtest, walk-forward, robustness, the sealed holdout and the family ledger. | strategy-idea-to-paper-tested, source-to-a-lab-test, first-backtest-from-an-idea, overnight-lab-loop, iterate-against-qmb-with-overfit-guards, variant-generation-and-comparison, ml-training-run-with-a-holdout |
| `real-library` | The real Library, with its dead-end rows and workflow memory. The engine runs on a SQLite fake until then. | hypotheses-from-dead-ends |
| `rlm` | The `rlm` node kind and its research kernel. | question-over-a-large-table |
| `sandbox` | The Lab sandbox, where an agent can write and built code runs. Until then every agent ask is rejected. | build-a-component-or-indicator, ml-training-run-with-a-holdout, mini-app-lifecycle |
| `app-op` | The host's app operations: list, consumers, `qmx app check` and the pipelines doors. | mini-app-lifecycle, connect-mini-apps |

Each draft keeps its waiting in one place. The script that would call the missing piece (for example `scripts/qmb.py` in the strategy-idea-to-paper-tested folder) states in its docstring what it would read and the shape of its answer, writes one line naming the need, and exits. Every other script in the draft is real: the gates, the checks and the verdicts run today on synthetic inputs. Each draft's `README.md` names its need in the line under its title, lists its steps, and says what was left out and why.

## Edit a template with the copilot

He asks the copilot in his own words, for example "make a paper scout for FX papers only". The copilot works on drafts; nothing it does changes a published version.

1. **Clone it as a variant.** The copilot saves a new draft whose definition `extends` the published template (its workflow id and version id) with a list of patches, such as a changed timezone, prompt or threshold. The variant keeps everything else from its parent, and once published it records the version it is a variant of.
2. **Or edit the template's own draft.** The copilot opens the draft, edits nodes, prompts, schemas or scripts, and saves it. Saving a draft never asks.
3. **Test it.** The copilot test-runs the draft on the cheapest test models with the catalogue's test inputs (the template's fixtures). A test run never asks. A run whose output carries a number its sources never gave fails its last check, render and grade, and nothing is delivered.
4. **Publish it.** Publishing needs a passing test of the exact content, and asks him once. The new version is published disabled, next to the old one, which stays for rollback.
5. **Enable it.** Enabling a version or a trigger is his act, never the copilot's.

A draft that waits for a need can be edited and saved the same way, but its test run and its enable are refused until the need exists.

## Make a draft runnable

When the piece a draft waits for lands, its PR replaces the waiting script with the real call, adds fixtures that match the real answer's shape, removes the need from `meta.needs` and from the catalogue row, records the template's test inputs, and adds one unit case that a planted number in its output fails the test run. `test_templates.py` then holds it to the same rules as the ten runnable templates.

## Rules every template keeps

- Render and grade is the last check. Its evidence set is built per run from the pinned inputs, the fetched and read artifacts, and the results of the declared scripts no model in the run wrote (engine AD-45). The output of model-written code is never in the set, `llm` and `agent` outputs and the run's own prompt are never in it, and timestamps, dates, run ids, hashes and version strings are removed from both sides before a number is compared. Every prose field that can carry a number is listed in the output schema's `x-prose`.
- Shared blocks live in `templates/_shared/`. A run holds only its own folder, so a template carries a byte-identical copy of each block file it uses, and `test_templates.py` lists every copy in `BLOCK_COPIES` and fails when one drifts.
- No template names a money act or holds a credential. Every proposal (a bench, a tightening, a promotion, an install) ends as a card for his click.
- Synthetic fixtures are labelled as synthetic. Data is held (ruling 91).
