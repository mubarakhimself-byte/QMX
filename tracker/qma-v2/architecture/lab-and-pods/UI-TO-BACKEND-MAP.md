# UI → backend map: every Lab and Pods element and the piece it needs

One row per panel, field, state or action the design shows. Shots `01-35` are in `research/methodology/23-ui-shots/`; shots `36-58` are in `ui-shots/` in this folder (taken this run with demo data on). The **Backend** column names the `LabService` operation (LLD section 6), the Library kind, the engine piece or the port. **Effect** is the harness effect when an agent calls it. **Status** says `keep`, `defer` or `cut` from HLD section 7.

## A. Lab header and chrome

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Bench switch Strategies / Pods | 15, 22 | two benches with their own layouts | none (client) | — | keep |
| Subject picker "Working on" (bots, workflows, models; Start something new) | 42 | choose the editor's subject | `subjects.list(bench)` over Library kinds `bot`, `workflow`, `model` | READ | keep |
| Pod picker "Working on Trend rider v2" (pods, New pod with the copilot, New pod from a template) | 22 | choose the pod being designed | `pods.list`, `pods.templates`, `pods.from_template` | READ / DOMAIN_WRITE | keep |
| Layout tabs Build, Test, Train, Compare / Design, Test, Paper; Save layout; Reset; Delete | 15-20, 36 | arrange tiles | client only (per-viewer convenience) | — | keep (browser) |
| + Panel menu (27 panels; Build a new panel…) | 45 | add a tile | client; "Build a new panel" → `panels.propose` through the copilot | DOMAIN_WRITE | keep |
| Machine picker "All machines / this laptop / VPS / Colab"; connecting strip Reachable → Signed in → Healthy; "offline" | 15 header, research 10 | look at one machine; connect first | `compute.list`, `compute.preflight(name)` → `available, configured, authorized, reachable, healthy` (engine AD-20) | READ | keep (Colab: defer) |
| Machine-filtered tiles; "Nothing … on this machine" with where its work is | research 10, 23 | filter every tile by placement | every list takes `machine?`; `runs.list(machine)` | READ | keep |
| Run / Run test button | 15, 22 | run the published version on the chosen machine; replay bots through pods | `runs.start(template, inputs, placement)`; `pods.test` | DOMAIN_WRITE | keep |
| Lab copilot toggle and column | 21 | the Lab copilot with context, starters, tools | harness chat with the `qmx-lab` plugin; context `{subject, layout, ticked, machine}` sent per message | — | keep |
| Guided walk strip (step n of m, Back, Next) | 32, 33 | copilot-led walk across layouts | the walk is the template's `human_gate` steps; `runs.explain` text per step | READ | keep |
| Day-one starters (template, pod, copilot) | research 10 | empty state | `pods.templates`, template gallery = Library `template` objects | READ | keep |
| Status bar "3 of 4 machines · 4 jobs" | all | live counts | `compute.list` + engine `runs.list` | READ | keep |

## B. Strategies › Build

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Resources tile: Workflows, Bots, Models, Datasets, Features, Saved tests, Presets, Reports; counts; "+" add per group; Add to copilot | 15 | the subject's toolbox | `subjects.list` + Library search by kind (`workflow`, `bot`, `model`, `dataset`, `component`, `setup`, `test-report`, `artifact`); "+" opens the matching template or importer; Add to copilot = `attach.resolve(toolbox)` | READ | keep |
| Resources › Machines (slots used/total, cost, status; manage in Settings) | 15 | where work runs | `compute.list` | READ | keep |
| Editor header "Breakout research · draft v7 · published v6" | 15, 16 | the subject's draft and published version | `drafts.get(item, ref)` → `revision`, `published_version` | READ | keep |
| Editor › Graph: nodes with kind colour, title, detail, status dot (ok / warn / stale), output preview; edges; pan, zoom, minimap | 16 | the draft as a graph | `drafts.get` → `GraphView` (status from the engine memo, preview from the last span's artifact) | READ | keep |
| Add a step (palette), connect, disconnect, move, delete | guide text 32 ("Add steps from Resources") | build the graph | `palette()`, `drafts.patch(ops)` | DOMAIN_WRITE | keep |
| Editor › Code (Python, editable) | 17 | the same draft as code | `drafts.get` → `CodeView`; `drafts.patch({code})`; round-trip check | DOMAIN_WRITE | keep |
| Editor › Import: Model file, Code from a repo, Notebook, Python file | 18 | bring in outside work | `drafts.import(kind, payload)` → `model` object / `bot-logic` draft / `board` or `workflow` draft / `lab.cell` | DOMAIN_WRITE | keep |
| Inspector: step kind, name, machine chip (Colab / VPS / laptop), Settings fields, Code tab | 15 | edit one step; choose where it runs | `drafts.get` node params; `drafts.patch(set_param, place)`; `compute.list` for the chip | DOMAIN_WRITE | keep |
| Log tile: run console of the selected run (`placed on …`, bars loaded, trades, CT-32 written) | 15, 20 | watch a run | `runs.logs(run_id)` SSE from engine `log` events | READ | keep |
| Draft / published; "drafts never run, only published versions do" | 15 | lifecycle | engine AD-11: `tests.run` on drafts, `runs.start` on versions; `drafts.save`, `drafts.publish` | DOMAIN_WRITE / MANAGE | keep |
| Workflow walk step 2 "Choose what starts it: a schedule, new data, a news event, or by hand. Choose where it runs." | 33 | trigger and placement for a workflow | engine `triggers.create` (cron, event, webhook, manual) + `runs_on`; enabling is MANAGE (engine OPEN-5) | MANAGE | keep (the control is missing in the design; add a trigger row editor) |
| Workflow walk step 3 "Dry-run it on recent data… then publish" | 31 | test gate | engine `tests.run` with pinned data, `drafts.publish` | DOMAIN_WRITE / MANAGE | keep |
| Pinned-by-the-copilot tile | research 10, 34 | a panel the copilot drafted | `panels.propose`, `panels.pin`; spec validated against the tier-1 catalog; `data` bound to a service read | DOMAIN_WRITE | keep |

## C. Strategies › Test

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Sweep grid: markets across, timeframes down; measure toggle Net / Sharpe / Max DD; cell states done, running %, queued, failed; "13 of 15 finished runs made money" | 19 | the sweep as a grid | `sweeps.grid(run)` over `backtest-result` objects; states from engine spans | READ | keep |
| Add a market / Add a timeframe / Pair two markets | 19 | grow the scenario | `scenarios.draft` (pairs: OPEN-6) | DOMAIN_WRITE | keep (pairs: defer) |
| New scenario dialog: market groups + own pair; Pairs A vs B; timeframes; parameters from the bot's declared ranges (from, to, step, on/off, "n values"); Add a parameter ("added to the bot's declared ranges as a new version"); measures (raw numbers, never a combined score; Your own); Costs preset; Run on (machine, offline greyed); N runs = markets × timeframes × settings; time estimate on the machine; "Exploration only: rerun winners on this laptop for evidence"; luck warning over 200 runs; Save as preset; Run N runs | 40, 41 | build a permutation sweep | `scenarios.draft` → `{runs, estimate, luck_warning, exploration_only}` (`compute.estimate`, `families.luck_warning`); `drafts.patch(bot, set_param_space)` + save for a new parameter; `scenarios.save_preset` → `setup`; `scenarios.run` → sweep template; costs preset = QMB condition-preset fragment | DOMAIN_WRITE (MANAGE above `ask_above_usd`) | keep |
| Runs table: filter All / Running / Done / Failed; sort by Net, Max DD, Sharpe, Trades; columns run, procedure, market, role, where, state, progress; tick to compare; click to select | 19, 36 | every run for the subject | `runs.list(subject, machine, filter)` over `backtest-result` + `workflow-run`; roles copied from QMB | READ | keep |
| Equity: selected run's curve with ticked overlays; net, DD, Sharpe; machine chip; plotted table | 19, 36 | compare curves | `runs.get(run_id)` → CT-32 chart series (display downsample declared); overlays from ticked ids | READ | keep |
| Robustness ladder: checks cheapest first, early exit; bar per check (editable); result; state pass / fail / running / skipped; machine; Add check (list + Build your own…) | 19 | QMB validation ladder | `robustness.ladder(result_ref)` → `test-report`; `robustness.add_check`; bars from `settings.lab.robustness_ladder` bound to the content hash; "Build your own" → D1 component template | READ / DOMAIN_WRITE | keep |
| Compare table: measures per ticked run; best marked only when the procedure is the same; "Different procedures: not ranked"; procedure · role; where; state; changed | 36 | side by side | `runs.compare(run_ids)` → QMB `compare_runs` readout; `changed[]` from the setup diff | READ | keep |
| Start something new › Test a hypothesis / Compare versions / Sweep markets: name, works on, data, runs on; steps preview; keep as template | 43, 44 | start a layout and a draft | clone the matching template into a `workflow` draft with inputs; `templates` as Library `template`; the layout stays client | DOMAIN_WRITE | keep |
| Start › Train a model / Custom workflow / Bring in outside work ("starts a copilot conversation") | 43, 57, 58, 31 | copilot-led starts | the guided-start questions are the template's `grill-to-card` step (research 17); the copilot calls `training.start`, `drafts.*`, `drafts.import` | DOMAIN_WRITE | keep |

## D. Strategies › Train and the model panels

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Training tile: model name, epoch n / N, "Likely overfitting", machine chip; pipeline chips Dataset, Features, Split, Leakage check, Train, Evaluate, Plug into slots (done / running / waiting; click = edit in Build); + Step | 20, 21, 46 | a training run | `training.get(run_id)` = the `training` template's node states; chips are the nodes; "+ Step" = `drafts.patch(add_node)` on the training draft; overfit flag from `ml.evaluate` | READ / DOMAIN_WRITE | keep |
| Loss curves training vs validation (live) | 20 | watch training | engine `metric` events on `events.stream` | READ | keep |
| Split: Train 2015–2022, Validation 2023–2024, Sealed test 2025 (lock), Purge, Embargo | 20 | the honest split | CT-12 split manifest on the `model` object; `ml.split` | READ | keep |
| Model slots: n of 4 with a model; Entry signal, Position sizing, Regime, Risk throttle; picker (Default rules / a model / Import a model…); + Slot | 46 | where models plug in | `slots.list(owner)`, `slots.plug` (mints the owner's next version), `slots.add`, `models.import`; owner per slot: bot (entry), pod block (sizing, throttle), MIS config (regime) | DOMAIN_WRITE | keep |
| Model full page › Slots tab: "Not plugged in", Plug in… | 51 | which slots a model fills | `slots.list(model)` (reverse `uses` edges); `slots.plug` | DOMAIN_WRITE | keep |
| Model full page › Performance: AUC, fold stability, leakage checks n/6, inference ms, validation score by fold; evidence runs with roles | 09 | the model card | `models.get` → `model` fields + `backtest-result` evidence with QMB roles | READ | keep |
| Data panel: datasets with coverage bar, provider, schema, timezone ("Unknown: set it before use"), freshness, gaps, revision fp1; features; Add data (upload, connect, derive, from another run's output) | 45 note, research 10 | datasets and features | `data.list`, `data.inspect`, `data.add`; Library `dataset` pointing at qmf-data rooms; `component` for features | READ / DOMAIN_WRITE | keep |
| Compute panel: machines with status, slots, hardware, cost, "Can produce evidence / Exploration only", jobs; Add compute (SSH server, Colab, cloud GPU, GPU marketplaces, another QMX machine); Storage (buckets) | 45 note, research 10 | where work runs | `compute.list`, `compute.add` (ssh, modal, e2b, amp, qmx-machine); storage = Library tiers (library AD-10) | READ / MANAGE (add) | keep (Colab: defer) |
| Agents panel: Quant → Agent → Sub-agent tree, task, state (running, done, queued, unknown), machine | 45 note, research 10 | who is working on the subject | `agents.tree` over engine spans and harness chats | READ | keep (live last line: defer) |
| Copilot "Train something new": What should the model predict (Entry signal, Regime, Position size, Something else) → Which data (FX majors M1, Calendar events, Upload new data) → … | 57, 58 | scope a training run by three questions | the D6 template's grill step; answers become `training.start(spec)` | DOMAIN_WRITE | keep |

## E. Lab copilot (column and tools)

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Hint "Knows BTC breakout, the open layout and every run" / "Knows Trend rider, its blocks, every pod test and paper run" | 21, 22 | the copilot's context | the UI sends `context` with each message; the prompt layer in `plugins/qmx-lab/prompts/lab-layer.md` | — | keep |
| Starters: Sweep …; Why did the USOIL M15 run fail?; Compare the three ticked runs; Build a panel showing drawdown by session | 21 | one-click asks | `scenarios.*`, `runs.explain`, `runs.compare`, `panels.propose` | per tool | keep |
| Pod starters: Why did Trend rider refuse the AVAX entry; Build a stress scenario from the March 2020 crash; Make a block that halves size after three losses; Split $20,000 across the ticked pods | 22 | | `paper.decisions` + `explain`; `scenarios_stress.create(replay)`; `blocks.create(code)` via the D1 template; `pods.patch(set_members)` + `pods.test` | per tool | keep |
| 17 tools in the composer (qmb.*, lab.train, lab.import_model, graph.edit_draft, code.edit, lab.add_panel, compute.place, data.inspect, pod.*) | research 10 §1 | what the copilot may do | LLD section 7 table; `AGENT_OPERATIONS` rows | as listed | keep |
| Targets Researcher, Analyst, Developer ("not configured") | research 10 | hand work to an agent | engine `agent` nodes with roles `researcher`, `analyst`, `builder`; "not configured" = no role candidate in Settings | — | keep |
| Attach: toolbox item, ticked runs, a tile, code folder, dataset upload | research 10 | attachments | `attach.resolve`; uploads through the Library blob door | READ / DOMAIN_WRITE | keep |
| Draft panel in chat: Keep / Throw away / Pin to the Lab | 34 | a panel the copilot drafted | `panels.propose`, `panels.pin`; spec stored as `artifact` (`panel-spec`) | DOMAIN_WRITE | keep |
| Errand receipt: helpers, tools, changes, reports; asks ("Which paper money should it soak on?") and permissions ("Put Weekend rider v1 on paper") | 27, 28 | what the copilot did | engine spans + harness blocks; the ask is the paper template's `human_gate`; the permission is the MANAGE on `pods.send_to_paper` | MANAGE | keep |

## F. Pods › Design

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Pod resources: pods (tick, stage Draft / Tested / On paper / Live, working pod highlighted), New pod (copilot / template); bots to run tests over (tick); crises (built-in + Yours; New crisis: copilot / replay real dates / set the shocks by hand); paper money accounts with balances; Library link | 22 | what a test runs over | `pods.list`, `pods.templates`, `pods.from_template`; bots = Library `bot` published versions; `stress-scenario` objects; `scenarios_stress.create`; paper money = `NodePort.servers()` paper accounts + the server ledger | READ / DOMAIN_WRITE | keep (demo/testnet money: defer) |
| Pod stack: seven slots Inputs, Guards, Allocator, Sizer, Throttles, Caps, Ledger; chips with live setting; kind icon for graph / code / model; remove (not for required); "+" per slot: catalogue by slot, New block as a graph, New block as code, Use a model; "Empty"; version · stage; slot explainer | 22, 47 | design the pod | `pods.get` (stack view), `pods.patch(add_block, remove_block, set_param)`, `blocks.catalogue(slot)`, `blocks.create(graph\|code\|model)`; required flag on `pod-block` | DOMAIN_WRITE | keep |
| Draft vN+1 · Discard · Save vN+1 | 22 | version the pod | `pods.discard`, `pods.save` → new `pod` version (`branches-from`) | DOMAIN_WRITE | keep |
| Send to paper popover: checks Saved, Kill line set, Stress board run; "vN is on paper" | 48 | gate before paper | `pods.send_to_paper` preconditions; MANAGE | MANAGE | keep (OPEN-3) |
| Block panel: slot · docs status (in the docs / partly / new scope); name; "pure: same inputs, same answer"; sliders per parameter (changed shown); Remove from / Add to pod; Open in the editor (graph and code blocks) | 22, 47 | edit one block | `blocks.catalogue` param schema; `pods.patch(set_param)`; `drafts.get(block item)` for graph/code kinds (document kind `pod-block`) | DOMAIN_WRITE | keep |
| Size trail: sample trade (bot, entry, stop, equity), bars per step Sizer → throttles → Caps → Venue fit with $; Market popover (under its peak %, weekend) | 22, 47 | why this size | `pods.trail(item, ref, sample, market)` = `simulator.trail`; venue fit from `NodePort.instrument_meta` | READ | keep |
| Pod template gallery (Paper starter, Classic Book, Vol-targeted core, Trend rider, Alt scalper, Kelly-lite, Risk-parity, Capital guard, Canary, Model-sized hybrid) | 22, research 10 | start from a template | Library `template` objects whose `instantiates = pod` | READ | keep |

## G. Pods › Test

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Pod equity: Each pod / Run together; "3 bots · 2022–2025"; curves; Gain, Deepest dip per pod; Run together: Split popover (pot $, share sliders, Equal money / Equal risk, Ask the copilot, Save mix); Together line and shares | 37, 38 | compare pods on the same bots and years | `pods.results` over `pod-test` run outputs (`pod.sim`); mix = `pod.mix`; Save mix = `pods.patch(set_members)` + `pods.save` (a pod with members, OPEN-4) | READ / DOMAIN_WRITE | keep |
| Stress board: scenarios × pods; cell = loss, % of room to the kill line, guard that fired, stood down (red border); "Run" for an untested cell; + Scenario (copilot / replay dates / by hand); click = select that pod | 37 | crises × pods | `pods.results.stress_cells` from `pod.stress`; a "Run" cell = `pods.test(pod, scenario)`; `scenarios_stress.create` | READ / DOMAIN_WRITE | keep |
| Head to head cards: Profit, Deepest dip, Worst crash, Kill-line risk, Luck share, Steps in; bars; trophy only beyond noise; summary line "X earns most, Y loses $N less in a crash" | 37 | pods as player cards | `pods.results.head_to_head` from `pod.head_to_head` (noise band from `pod.fan`) | READ | keep |
| Drawdown fan: p(kill) per pod; p5–p95 bands over 90 days; dashed kill line | 37 | chance of the kill line | `pods.results.fan` from `pod.fan` (1,000 resampled paths) | READ | keep |
| Interventions (test): every shrink, refusal, halt, stand-down with the block that did it; click → tune that block in Design | 37 (docked), 39 | why the pod stepped in | `pods.results.interventions` (simulator journal rows); click = client navigation to the block | READ | keep |
| Run test (header): "replay N bots through M pods and K stress scenarios on <machine>" | 22 | start the pod test | `pods.test(pod_refs, bot_refs, window, scenario_refs, mix?)` → `pod-test` template run with placement | DOMAIN_WRITE | keep |

## H. Pods › Paper

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Paper run: pod tabs on paper; verdict "Behaving as tested / Drifting / Soak done: ready for live / Paused / Stopped"; version · paper money · server; Day n of m with day pips; equity line against the shaded band from its own test; today marker; Pause / Resume; +7 days | 39 | a pod soaking on paper | `paper.get(pod)` → `paper-run` object (band from the pod's test); `paper.pause/resume/extend` | READ / DOMAIN_WRITE | keep (money: server ledger now, demo/testnet defer) |
| Live decisions: newest first; All / Refused n; each trade: time, side, symbol, bot, sizing steps with $, refusal reason | 39 | each paper trade and how it was sized | `paper.decisions(run, since)` SSE from `paper.decision` events | READ | keep |
| Ready for live?: n of 5 checks (Soak time, Inside the tested band, Kill line kept its distance, Every fill matched the exchange, No unknown positions); Promote ("promotion card waiting in Portfolio, Road to live"); Stop paper run (two clicks, "record kept"); Restart | 39 | gate to promotion | `paper.checks` (`paper.check` grader) + the composition's `unsupported_blocks` as an extra row; `paper.promote` → `NodePort.mint_promotion_card`; `paper.stop` keeps the `paper-run` | READ / MANAGE | keep |
| Interventions (paper): today's shrinks and refusals from the pods on paper | 39 | | `paper-run.interventions` | READ | keep |

## I. Library and Portfolio where pods and models appear

| UI element | Shot | What it is for | Backend | Effect | Status |
| --- | --- | --- | --- | --- | --- |
| Library › Pods shelf: cards (Live / On paper), template, used in Lab / Portfolio; inspector Used in map, Journal & logs, Code (YAML stack), Settings; Open in Lab; Add to copilot; New version | 13 | pods as Library items | Library `pod` kind with preview/detail schema (library AD-17); Code = generated YAML of the stack; Used in = relation neighbourhood (`part-of`, `run-of`, `instance-of` to seats) | READ / DOMAIN_WRITE | keep |
| Library › Pod blocks shelf (25): slot label, name, what, "Used in Lab / Not used yet"; inspector Used in, Code (signature stub), Settings (Slot, Built as, Setting); Open in Lab; New version | 49, 50 | blocks as Library items | Library `pod-block` kind; `uses` edges from pods | READ | keep |
| Library › Stress scenarios, Paper runs, Test reports, Saved setups, Data, Files shelves | 13 (rail) | proof and inputs | kinds `stress-scenario`, `paper-run`, `test-report`, `setup`, `dataset`, `artifact` | READ | keep |
| Library › Bot full page: Performance (Sharpe, max DD, win rate, net; equity; evidence runs with roles), Trading (journal; connections server · pod · mode · seat), Setup; Road to live | 08 | the bot card | `backtest-result` evidence with roles; connections from `NodePort.seats()`; `Road to live` opens Portfolio | READ | keep |
| Portfolio › Pods cards (money, room above the kill line, method, paused / trading) and Pod panel (live / paper side; equity; at stake next trade; losses to kill line; room; deepest dip; limits right now; Sizing method Book+BMS / Model / Workflow / Hybrid / Simple rules; knobs; Drawdown ladder steps; Bots weights; Draft vN+1 replay; Discard / Save; Pause / Resume; Open in the Lab) | 52 | steer a running pod version | reads from `NodePort.bindings()` + the pod simulator's replay of the draft (`simulator.replay`); Save = `pods.save` (a new version, which re-enters test before it can trade); Pause / Resume = node control through Portfolio's own path, not the Lab; method chips map to sizer block kinds | READ / DOMAIN_WRITE | keep (live Pause/Resume is Portfolio's) |
| Portfolio › MIS tab: labelers (Volatility state, Session, News state, Regime HMM, Liquidity) with value, since, Live / Shadow switch; "build new labelers in the Lab" | 53 | market labelers and who listens | `NodePort.mis_snapshot()` (TN-19); switch = `NodePort.promote_labeler` (MANAGE); new labeler = `component` of class `labeler` via the D5 template, registered as a shadow candidate | READ / MANAGE | keep |
| Portfolio › Road to live lanes and the Promotion card (checks, Sign for live, Sign and activate, Activates 00:00 UTC, Pull back to paper) | 06 (workflow) and research 10 | sign and activate | the node's two-click promotion (TN-20) through Portfolio; the Lab only mints the card's evidence | MANAGE (human) | keep (not Lab scope) |
| Portfolio › Servers strip / Trading servers (latency, restart, drain, move accounts, log; add a server) | 52 header | the trading servers | `NodePort.servers()`, `latency()`; actions are Portfolio's | READ | keep (not Lab scope) |
| Library › Workflows full page (steps chain, "runs this month", "a draft runs only after it is published") and Templates "Use this template" → Lab | 05, 06, 10 | workflows in the Library | engine kinds `workflow`, `workflow_version`, `workflow_run`; `drafts.get` for the editor | READ | keep (engine's) |

## J. Elements the design shows that are cut or deferred (from HLD section 7)

| UI element | Shot | Decision |
| --- | --- | --- |
| Pairs (one market against another) | 40 | defer (OPEN-6) |
| Colab as a machine; AWS GPU as a named provider | research 10 | defer Colab; AWS via `ssh` |
| Binance testnet / Bybit testnet / IC Markets demo as paper money | 22, 39 | defer (OPEN-2); server paper ledger in v1 |
| Agents panel live "last line" per sub-agent | research 10 | defer; spans now |
| "Explain it as" diagram / interactive / video for Lab results | 11 (articles) | defer to the output-layer design |
| Model sizer, regime throttle, vol spike, thin hours, liquidity cap, peg input, cooldown on the live node | 22, 47 | keep in the Lab; named unsupported by the adapter until the risk session rules |
