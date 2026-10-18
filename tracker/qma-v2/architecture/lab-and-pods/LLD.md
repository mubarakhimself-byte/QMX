# Low-level design — Lab and Pods backend

Companion to `ARCHITECTURE-SPINE.md` (binding) and `HLD.md`. Vocabulary follows the codebase-design skill: **module**, **interface**, **implementation**, **seam**, **adapter**, **depth**. Labels: **[retrieved]**, **[remembered]**, **[inferred]**. Numbers marked **Claude's default** are placeholders the operator changes in Settings. Shot references (`shot 19`, `shot 47`) point at `research/methodology/23-ui-shots/` (01-35) and `ui-shots/` in this folder (36-58).

---

## 1. Document kinds (the editor engine)

### 1.1 Registry entry

```python
class DocumentKind(Protocol):
    kind: Literal["workflow", "bot-logic", "pod-block", "board"]
    authoritative: Literal["json", "code", "by-block-kind"]
    def to_graph(self, doc: Draft) -> GraphView: ...          # nodes, edges, ports, positions, status per node
    def to_code(self, doc: Draft) -> CodeView: ...            # text + cell map {node_id: (start_line, end_line)}
    def patch_from_graph(self, doc: Draft, op: GraphOp) -> Draft: ...   # add_node, remove_node, connect, disconnect, move, set_param
    def patch_from_code(self, doc: Draft, text: str) -> Draft: ...      # re-parse cells; unchanged cells keep their node ids
    def validate(self, doc: Draft) -> list[Finding]: ...      # engine validation + round-trip check + kind rules
    def importers(self) -> dict[str, Importer]: ...           # "model-file" | "repo" | "notebook" | "python-file"
```

| Kind | Authoritative form | Graph projection | Code projection | Round-trip rule |
| --- | --- | --- | --- | --- |
| `workflow` | `qmx.workflow/1` JSON (engine AD-2) **[retrieved]** | nodes and connections as they are; node status from the last run's memo | one cell per node: `# %% step:<node_id> <name>` header, then the node's `code_ref` body for script-family nodes or a generated call stub for others | `to_code ∘ patch_from_code = identity` on the JSON minus `position`; a cell whose header was deleted removes the node; a new unmarked cell becomes a `lab.cell` node appended after the previous cell |
| `bot-logic` | folder: `logic.py` + `declaration.json` (QML QL-2 two artifacts) **[retrieved]** | derived: one node per declared confluence leg and producer binding, one `logic` node; read-only positions | `logic.py` verbatim | code is the truth; `patch_from_graph` is refused except `set_param` on declaration parameters |
| `pod-block` | `form` → param values; `graph` → a `qmx.workflow/1` sub-document with fixed `in` and `out` ports for the slot; `code` → a Python function with the slot's signature; `model` → a model ref plus ceiling params | by kind | by kind | as `workflow` for `graph`; code is the truth for `code` |
| `board` | cell script (ruling 31) | the cell DAG: `lab.cell` and `note` nodes; cells that name an upstream cell (`# uses: <node_id>`) get an edge | the script | as `workflow` |

The Start-something-new kinds (shot 43: hypothesis, compare, train, sweep, workflow, import) each open a `workflow` draft cloned from the matching template, with the chosen subject, data and machine written into its `inputs` (shot 44).

### 1.2 Draft and view types

```text
Draft      = { item_id, ref, kind, revision, document (bytes|json), content_hash, lineage {branches_from, variant_of} }
GraphView  = { nodes: [{id, type, name, ports_in[], ports_out[], params, position, status ok|warn|stale|running|none, preview?}],
               edges: [{id, from, out_port, to, in_port, map}], validation: [Finding], read_only: bool }
CodeView   = { text, language, cells: {node_id: [start, end]}, read_only_ranges: [[start,end]] }
Finding    = { code, severity error|warn, node_id?, line?, message }
GraphOp    = add_node{type, name, params, position} | remove_node{id} | connect{from,out,to,in,map} | disconnect{edge}
           | move{id, position} | set_param{id, key, value} | rename{id, name} | place{id, runs_on}
```

Status per node is derived, never stored: `stale` when the engine memo for `(node, inputs hash, node def hash)` is missing or invalidated, `ok | warn` from the last `node_finished` span's verdict, `running` from a live attempt (shot 16 dots).

### 1.3 Importers (shot 18)

| Card | Input | Produces | Rule |
| --- | --- | --- | --- |
| Model file | `.onnx`, `.pkl`, `.joblib` | a `model` object (weights blob, format, inferred input schema) | the file is a blob; inference code is a generated `lab.model` wrapper that loads from the blob, never from a URL ("shipped inside the bot so it never fetches at run time") |
| Code from a repo | a folder or `CodeSource{repository, revision}` (qmx_remote shape **[retrieved]**) | a `bot-logic` draft | the folder becomes the logic blobs; `declaration.json` is scaffolded from discovered parameters; Layer-1 lint runs; network and clock reads are findings |
| Notebook | `.ipynb` | a `board` or `workflow` draft | each code cell → `lab.cell`; a cell tagged `# step: <type>` → that node type; markdown → `note` |
| Python file | `.py` | one `lab.cell` node, or a `bot-logic` draft when it defines the runtime protocol entry points | the user picks "one step" or "whole bot" (shot 18's note) |

---

## 2. The Lab node pack

Every type is a pack type with a `base_kind` (engine AD-5) and typed `data` ports (engine AD-4); the validator checks it against its base kind's contract. Parameters are JSON Schema; `effect` defaults as listed.

| Type | Base kind | In → out | Parameters (summary) | Effect |
| --- | --- | --- | --- | --- |
| `lab.data` | library | — → `bars` | `recipe_ref` or `{source, symbol, timeframe, range}` → resolves to a qmf-data room read and a CT-12 split ref | none |
| `lab.feature` | script | `bars` → `features` | `component_refs[]` (indicators), params | reversible |
| `lab.label` | script | `bars` → `labels` | method (`triple_barrier`, `fixed_horizon`), params | reversible |
| `lab.model` | script | `features, labels` → `signals` | `model_ref` or inline training spec; `validation` (walk-forward folds, purge, embargo) | reversible |
| `lab.test` | subworkflow | `signals \| bot_ref` → `result` | wraps `qmb.compile → qmb.run`; costs preset | per callee |
| `lab.report` | library | `result` → `artifact` | report type; `save_to_library` | compensable |
| `lab.cell` | script | `*` → `*` | `code`, `uses[]` | reversible |
| `note` | — (the engine's one draft-only type, engine AD-5; not a Lab type) | — | markdown | none |
| `qmb.compile` | script over `QmbPort` | `subject_ref, composition_ref, data_ref, costs, assignment` → `setup_ref` | see section 3 | compensable (writes a `setup`) |
| `qmb.run` | app_op (`qmb_backtest` on the `qmb` placement, via `QmbPort`) | `setup_ref` → `backtest_result_ref` | `procedure backtest`, `window in_sample\|validation` | none (memoised by intent key; retried freely) |
| `qmb.sweep` | app_op (`qmb_backtest`) | `setup_ref, grid` → `backtest_result_refs[]` | the Cartesian batch (QMB B-12) run inside ONE qmb invocation; `partition_by: placement` only | none |
| `qmb.walk_forward` | app_op (`qmb_backtest`) | `setup_ref, folds, purge, embargo` → `backtest_result_refs[]` | | none |
| `qmb.robustness` | app_op (`qmb_backtest`) | `setup_ref, checks[]` → `check_results[]` | ladder order; early exit at first fail; each check names its bar | none |
| `qmb.optimize` | app_op (`qmb_backtest`) | `setup_ref, space, objective, generations, seed` → `trial_refs[], sensitivity` | B-8 generation-stepped sampler | none |
| `qmb.compare` | script | `result_refs[]` → `readout` | `compare_runs` (query, no occupancy) | none |
| `qmb.holdout_touch` | app_op (`qmb_backtest`, sealed window) | `family_ref, setup_ref` → `backtest_result_ref` | refuses if the window was touched; journals who and why; runs only on `qmb` or `pc` | irreversible (the one Lab compute node that is) |
| `ml.dataset` | script over Kernel | `bars, features` → `dataset_ref` | point-in-time build | reversible |
| `ml.split` | script | `dataset_ref` → `split_ref` | CT-12: train / validation / sealed-test, purge, embargo | compensable |
| `ml.leakage_check` | grader (deterministic) | `dataset_ref, split_ref` → `pass \| fail` | horizon vs purge, feature knowable-at, shuffle test | none |
| `ml.train` | script over Kernel + Compute | `dataset_ref, split_ref, spec` → `model_ref` | framework in the workflow folder; `runs_on`; checkpoints every N epochs; emits `metric` events (loss curves, shot 20) | none (checkpointed and memoised by intent key; a retry resumes from the last checkpoint; a dead worker never pages him) |
| `ml.evaluate` | script | `model_ref, split_ref` → `metrics` | validation only; `likely_overfitting` flag when train/validation gap passes `settings.lab.overfit_gap` | none |
| `ml.plug` | library | `model_ref, owner_ref, slot` → `owner_version_ref` | mints a new owner version with `uses → model` | compensable |
| `pod.sim` | script over the simulator | `pod_version_ref, bot_refs[], window` → `pod_result_ref` | replay trades through the stack; equity, interventions, size trails | reversible |
| `pod.stress` | script | `pod_version_ref, scenario_refs[]` → `stress_cells[]` | shocks or real-date replay | reversible |
| `pod.fan` | script | `pod_result_ref, paths, horizon_days` → `fan` | resampled drawdown paths (p5, p50, p95), p(kill) | reversible |
| `pod.head_to_head` | script | `pod_result_refs[]` → `measures` | profit, deepest dip, worst crash, kill-line risk, luck share, steps in; noise band from the fan | none |
| `pod.mix` | script | `pod_version_refs[], weights, pot` → `pod_result_ref` | combined curve | reversible |
| `paper.step` | script | `paper_run_ref` → `paper_run_ref` | one bar of live prices through bots and simulator on the paper ledger; appends decisions | compensable |
| `paper.check` | grader | `paper_run_ref` → `pass \| fail` | the five readiness checks (shot 39) | none |
| `data.inspect` | library | `dataset_ref` → `coverage, gaps, schema, freshness, revision` | | none |
| `data.snapshot` | library | `dataset_ref` → `snapshot_ref` | frozen id (D2 step 2) | compensable |

A UI step kind (shot 16: DATA, FEATURE, MODEL, TEST, OUTPUT) is the palette *group* of these types; the group colours the node.

---

## 3. Setups and the QMB door

### 3.1 `setup` object (Library kind `setup`, CT-47 shape **[retrieved]**)

```json
{
  "kind": "setup",
  "fields": {
    "subject": {"item_id": "…", "object_id": "fp1:…", "kind": "bot"},
    "composition": {"target": "book_bms", "book_fp1": "fp1:…", "bms_fp1": "fp1:…", "pod_version": "fp1:…"},
    "data": {"recipe_def": "…", "release_fp1": "fp1:…", "split_fp1": "fp1:…", "window": "in_sample|validation|sealed"},
    "costs": {"preset": "default-spread|stress-spread-x2|broker-fills", "fragment_fp1": "fp1:…"},
    "assignment": {"atr_stop": "1.5", "lookback": "40"},
    "assignment_is_canonical": false,
    "measures": ["net_pct", "sharpe", "max_drawdown", "profit_factor"],
    "placement": "qmb",
    "resolved_run_config_fp1": "fp1:…",
    "world": "replay", "clock": "replay", "data_provenance": "recorded"
  }
}
```

`qmb.compile` calls `QmbPort.compile(...)` which calls `qmb.config.compile_run_config` with layers `invocation-flags > run-spec > bms-fragment > book-fragment > workspace-defaults` **[retrieved compiler.py]**; the resolved artifact's `fp1` is the run-id root; a dummy Book or BMS is refused by the compiler itself (DEC-0424). The scenario dialog's "new parameter … added to the bot's declared ranges as a new version" (shot 41) is `drafts.patch(bot, set_param_space)` followed by Save, which mints a new bot version before the setup is compiled (QML QL-3: a changed parameter space mints a new Bot).

### 3.2 `QmbPort`

```python
class QmbPort(Protocol):
    def compile(self, req: CompileRequest) -> ResolvedRunConfig | Refusal: ...
    def run(self, setup: Setup, procedure: Procedure, placement: str) -> RunOutcome: ...   # one qmb invocation
    def compare(self, result_refs: list[ObjectId]) -> CompareReadout: ...                   # query, no occupancy
    def project(self, result_ref: ObjectId, predicate: Projection) -> SavedView: ...
    def data(self, cmd: Literal["catalog","verify","gap_check","download"], args) -> Document: ...
```

Adapters: `adapters.qmb_app_op` (**default**: the engine's `app_op qmb_backtest` on the `qmb` placement, engine AD-31, ruling 68; results come back as objects by hash on the run's branch) and `adapters.qmb_api` (in-process `qmb.doors.api`, used only when the registered `qmb` placement is the PC itself, the developer fallback; governed lane `spawn_governed` so the ledger line exists). The earlier `qmb_cli`-in-a-remote-worker adapter is dropped: backtests never run on agent hosts. A fake adapter returns recorded CT-32 fixtures for tests (ruling 51: tests use real models for model steps, but QMB fixtures are allowed for door tests). `RunOutcome = { ledger_line_fp1, ct32_fp1, role, world, claim_class, fidelity, measures {name: {value, unit}}, chart_series_ref, trade_events_ref }` — copied, never computed by the Lab.

### 3.3 `backtest-result` import

The node writes one `backtest-result` object per QMB run (per sweep cell) on `refs/runs/<run_id>` with relations `run-of → workflow-run`, `derived-from → setup`, `tested-by ← subject version`, fields = `RunOutcome` plus `procedure`, `symbol`, `timeframe`, `changed[]` (the grid axes that differ from the base), `placement`, `exploration_only`. The Runs table (shot 19), Equity, Compare (shot 36) and the Sweep grid read these.

---

## 4. Families, holdouts and the identity rule

```text
families.ledger(root) -> { trials: n, trials_by_kind {backtest, sweep_cell, walk_forward, child, variant, training_config},
                           deflated_sharpe (over every trial's best in-sample Sharpe; Bailey–López de Prado shape [remembered]),
                           holdout: { window: split_fp1, created, touched: n, last_touch {run_id, by, why} },
                           dead_ends: [object ids tagged negative_result] }
families.luck_warning(scenario) -> { runs_planned, trials_so_far, warn: bool, text }   # shot 41's warning line
families.identity(change_label) -> "variant-of" | "branches-from" | "new-item"            # AD-16 table
```

`qmb.holdout_touch` refuses with `holdout_already_touched` unless the operator or a template end step (L4, D3, D6) calls it, and then journals a `holdout_touch` event on the run; a second touch requires a new CT-12 manifest with a later seal (research 17 Q3).

---

## 5. Pods

### 5.1 Objects (shots 22, 47-50)

```json
{ "kind": "pod", "fields": {
    "name": "Trend rider", "template": "trend-rider", "stage": "paper",
    "stack": {
      "inputs":    [{"block": "fp1:regime-label", "params": {"source": "mis:regime_hmm_v1"}},
                    {"block": "fp1:volatility-ewma", "params": {"days": 30}}],
      "guards":    [{"block": "fp1:kill-line", "params": {"kill": 15}},
                    {"block": "fp1:daily-stop-and-health", "params": {"daily": 3}},
                    {"block": "fp1:news-aware-kill-switch", "params": {"window_min": 30}}],
      "allocator": [{"block": "fp1:equal-split", "params": {}}],
      "sizer":     [{"block": "fp1:fixed-fractional", "params": {"risk": 0.75}}],
      "throttles": [{"block": "fp1:regime-throttle", "params": {"chop": 0.5, "crash": 0}},
                    {"block": "fp1:volatility-spike", "params": {"mult": 0.5, "hours": 2}}],
      "caps":      [{"block": "fp1:exposure-caps", "params": {"coin": 25, "positions": 8}},
                    {"block": "fp1:correlation-cap", "params": {"cluster": 40}}],
      "ledger":    [{"block": "fp1:daily-utc-ledger", "params": {"currency": "USD", "fees": true}}]
    },
    "members": null } }
```

A **mix** ("Run together", shot 38) is a `pod` whose `members = [{pod_version, share}]` and whose `allocator` is the single block `split-across-pods`; it goes to paper like a pod (OPEN-4).

```json
{ "kind": "pod-block", "fields": {
    "name": "News-aware kill switch", "slot": "guards", "block_kind": "graph", "required": false,
    "docs": "new", "what": "Halt around big events",
    "param_schema": {"window_min": {"type": "number", "min": 5, "max": 120, "step": 5, "unit": "min", "default": 30}},
    "signature": {"inputs": ["calendar", "clock"], "outputs": ["halt: bool"]} },
  "blobs": {"graph.json": "…"} }
```

Block kinds: `form` (pure parameter function from the catalogue), `graph` (a `qmx.workflow/1` sub-document with the slot's `in`/`out` ports; shot 47 "Open in the editor"), `code` (a Python function with the slot's signature), `model` (a model ref plus ceiling params; the model answers ×0–1 under a rule ceiling). Required blocks (`kill-line`) cannot be removed.

### 5.2 The simulator (one implementation)

```text
simulator.trail(pod_version, sample_trade, market{dip, weekend, regime}) -> [{step, usd}]              # shot 47 Size trail
simulator.replay(pod_version, bot_results[], window, ledger_start) -> PodResult{equity[], trades[], interventions[], trails[]}
simulator.stress(pod_version, scenario) -> StressCell{loss, of_room, fired, stood_down}                  # shot 37
simulator.fan(pod_result, paths=1000, horizon_days=90) -> Fan{p5[], p50[], p95[], p_kill, kill}
simulator.head_to_head(pod_results[]) -> {profit, deepest_dip, worst_crash, kill_line_risk, luck_share, steps_in, noise{...}}
simulator.mix(pod_results[], weights, pot) -> PodResult
simulator.paper_step(paper_run, bar, bot_intents[]) -> PaperRun'                                         # shot 39 decisions
```

Rules: blocks are pure functions `(context, params) -> decision`; the order inside the stack is fixed by slot order; venue fit (lot step, minimum order, fee) runs last from the venue's instrument metadata (qmf-venue read through `NodePort.instrument_meta`, never a Lab import); every intervention (shrink, refuse, halt, stand down) is a journaled row `{at, pod, bot, what, by_block, multiplier|reason}` (shot 37 Interventions). Measures: `luck_share` = share of profit from the top 5 trades; `steps_in` = share of trades shrunk or refused; `worst_crash` = min over stress cells; `kill_line_risk` = `fan.p_kill`; the head-to-head trophy shows only when the gap exceeds the fan's noise band for that measure.

### 5.3 Stress scenarios (shots 37, 22 "New crisis")

`stress-scenario` object: `{ name, kind: shock | replay, shock: {price_move_pct, speed_min, spread_mult, outage_min, stablecoin_px}, replay: {from, to}, by: operator | copilot }`. The three creation paths are one object: by hand (shock fields), replay real dates (replay fields), described to the copilot (the `pod.stress_scenario` tool writes the same object).

### 5.4 Composition adapter and node reads (ruling 14)

```python
class PodCompilerPort(Protocol):
    def compile(self, pod_version: ObjectId, target: Literal["book_bms", "policy_pair"]) -> ResolvedComposition: ...
ResolvedComposition = { target, book_fragment_fp1?, bms_fragment_fp1?, policy_pair_fp1?,
                        placed_blocks: [{block, section}], unsupported_blocks: [{block, reason}] }

class NodePort(Protocol):
    def servers(self) -> list[Server]: ...                      # Portfolio Servers strip; paper run "server" picker
    def seats(self) -> list[Seat]: ...                         # unit = bot + pod + MIS needs, read as a list of parts
    def bindings(self) -> list[Binding]: ...
    def mis_snapshot(self) -> MisSnapshot: ...                 # TN-19 snapshot; feeds the regime input block
    def instrument_meta(self, venue, symbol) -> InstrumentMeta: ...
    def register_candidate_labeler(self, component_version: ObjectId) -> CandidateId: ...   # shadow lane
    def promote_labeler(self, candidate: CandidateId) -> Receipt: ...                        # MANAGE (Portfolio MIS switch)
    def mint_promotion_card(self, pod_version, unit_parts, evidence_refs) -> CardRef: ...     # TN-20 input; signing elsewhere
```

v1 adapter `adapters.pod_book_bms`: `sizer fixed-fractional → money_rules (seat_r_ceiling, r_unit_price shape)`; `guards kill-line → control_policy.kill_line = money_rules.loss_floor`; `guards daily-stop → control_policy force-flat rule`; `caps exposure/correlation → BMS constraints`; `ledger → BMS accounting_rules`; `guards news-aware → protection_windows (news kind)`; `allocator → capacity_and_sweep`. Everything else (`regime throttle`, `volatility spike`, `thin hours`, `model sizer`, `liquidity cap`, `peg input`, `cooldown`, `streak bench` beyond `bench_consecutive_loss_threshold`) is returned as `unsupported_blocks` **[inferred from CT-22/CT-27 sections, retrieved]** until the risk session rules; the Lab shows them as a failed "Ready for live?" row ("3 blocks run only in the Lab").

### 5.5 Paper run (shot 39)

```json
{ "kind": "paper-run", "fields": {
    "pod_version": "fp1:…", "members": ["bot fp1…"], "money": {"kind": "server-ledger", "balance_start": 20000, "currency": "USD"},
    "placement": "contabo", "trigger_id": "…", "started": "2026-09-29", "days_planned": 7, "days_extra": 0, "day": 4,
    "state": "running|paused|stopped|ready", "band": {"from_test": "fp1:pod-result", "p5": [...], "p95": [...]},
    "equity": [...], "decisions": [{"at": "…", "bot": "…", "side": "Buy", "symbol": "…", "steps": [{"by": "Sizer 0.75%", "usd": 860}], "refused": null}],
    "interventions": [...], "checks": {"soak_time": false, "inside_band": true, "kill_line_distance": true, "fills_matched": true, "no_unknown_positions": true},
    "verdict": "as-tested|drifting|ready" } }
```

The `paper` template is a **chain of finite daily runs** (spine AD-12; engine AD-25): `trigger(cron, daily at session open, market zone, continuity: true, max_concurrent: 1)` → `loop(bounded by the day's bars)` { `wait(next bar close)` → `paper.step` } → `paper.check` at session close. `continuity` hands each day's run the previous day's ledger state, open positions and band position; each day appends one version to the `paper-run` item. A daily run ends at its session boundary, never on a wall-time ceiling (engine AD-40). For a 24-hour market (crypto, and FX through the trading week) the "day" is the market's session boundary from the instrument calendar (00:00 UTC by default for crypto): each daily run's loop ends at that boundary, before the next fire, so `max_concurrent 1` never blocks the next day. A stalled day is caught by the engine's stuck detector, not a time cap. `service.paper.pause/resume` disable and enable the trigger, `extend` raises `days_planned`, `stop` disables the trigger and marks the `paper-run` stopped (record kept); none of them writes `gate_resolved`, which stays reserved for human gates. A daily run that dies mid-day is folded and resumed by the engine like any run; a missed day collapses into one catch-up run (engine AD-10). Money kinds: `server-ledger` (v1), `broker-demo`, `exchange-testnet` (OPEN-2, through `NodePort` later). `fills_matched` is trivially true on the server ledger and reads the node's reconciliation on a demo account.

---

## 6. Service (the one interface)

```python
class LabService:
    # subjects and drafts (Build; Inspector; Resources)
    subjects.list(bench, machine?) -> [Subject{item_id, kind, name, version, stage, draft_revision, published_version}]
    drafts.get(item, ref="refs/drafts/<item>") -> Draft + GraphView + CodeView   # main holds published versions only
    drafts.patch(item, ref, ops: list[GraphOp] | {code: str}, expected_revision) -> Draft
    drafts.validate(item, ref) -> [Finding]
    drafts.save(item, ref, message) -> version (his Save: merges refs/drafts/<item> into main as the next version, branches-from, no ask because he is the operator; an agent's save stays on its own ref)
    drafts.publish(item, ref, semver) -> version   # merge into main; semver is an annotation; tested-by copied when content_hash matches (27d C1); MANAGE for governed and lifecycle kinds
    drafts.import(item, kind: model-file|repo|notebook|python-file, payload) -> Draft
    palette() -> [{group, type, name, note, ports, param_schema}]
    # runs (Run button; Runs; Equity; Robustness; Log; Compare; Sweep grid)
    runs.start(template, inputs, placement, mode live|test, subgraph?) -> run_id
    runs.list(subject?, machine?, filter) -> [RunRow]    # backtest-result + workflow-run fold
    runs.get(run_id) -> RunCard; runs.logs(run_id) -> stream; runs.cancel/pause/resume(run_id)
    runs.explain(run_id) -> text + spans                 # "Why did the USOIL M15 run fail?"
    runs.compare(run_ids) -> CompareReadout              # not ranked across procedures
    robustness.ladder(result_ref) -> [Check{name, cost, bar, result, state, placement}]; robustness.add_check(result_ref, check)
    # scenarios and presets (Sweep grid; New scenario)
    scenarios.draft(subject, markets, pairs, timeframes, params, measures, costs, placement) -> ScenarioDraft{runs, estimate, luck_warning, exploration_only}
    scenarios.save_preset(draft) -> setup_ref; scenarios.run(draft) -> run_id
    sweeps.grid(run_id|subject) -> cells[{symbol, timeframe, result_ref, status, measures}]
    # training, models, slots, data, compute (Train; Model slots; Data; Compute)
    training.start(spec, placement) -> run_id; training.get(run_id) -> {pipeline steps + states, curves, split, overfit_flag}
    models.list(); models.get(ref); models.import(file) -> model_ref
    slots.list(owner) -> [{slot, owner_doc, model?, scope}]; slots.plug(owner, slot, model_ref) -> owner_version; slots.add(owner, slot_spec)
    data.list() -> [Dataset{coverage, gaps, revision, provider, schema, timezone, freshness}]; data.inspect(ref); data.add(kind upload|connect|derive|from_run, payload)
    compute.list() -> [Placement{name, kind, hardware, status, slots_used, slots_total, cost, evidence_ok, preflight}]
    compute.preflight(name) -> {available, configured, authorized, reachable, healthy}; compute.estimate(template, inputs, placement) -> {seconds, usd}
    compute.add(kind ssh|modal|e2b|amp|qmx-machine, settings_ref)   # keys stay in the credential store
    agents.tree(subject?) -> [AgentNode{name, role, task, state, placement, children[]}]   # engine spans + harness chats
    # pods (Design; Test; Paper; Library pod views; Portfolio pod panel)
    pods.list() -> [PodRow{item, version, stage, template}]; pods.get(item, ref) -> Pod + stack view with live settings
    pods.patch(item, ref, ops: add_block|remove_block|set_param|set_members, expected_revision) -> Pod
    pods.save(item, ref) -> version; pods.discard(item, ref); pods.from_template(template) -> item; pods.templates() -> [...]
    blocks.catalogue(slot?) -> [PodBlock]; blocks.create(kind graph|code|model, slot, name) -> block item (opens in the editor)
    pods.trail(item, ref, sample, market) -> [{step, usd}]
    pods.test(pod_refs[], bot_refs[], window, scenario_refs[], mix?) -> run_id         # pod-test template
    pods.results(pod_refs[]) -> {equity, head_to_head, fan, stress_cells, interventions}
    pods.send_to_paper(item, ref, money, placement) -> paper_run_id                   # MANAGE (ruling 80; creates the daily paper trigger, AD-12)
    paper.get(pod) -> PaperRun; paper.pause/resume/extend/stop(paper_run_id); paper.decisions(paper_run_id, since) -> stream
    paper.checks(paper_run_id) -> {checks, ready}; paper.promote(paper_run_id) -> card_ref   # MANAGE; card lands in Portfolio
    scenarios_stress.create(spec) -> stress_scenario_ref
    # copilot support (Pinned panel; draft panel in chat; attachments)
    panels.propose(spec, data_op) -> panel_ref (validated against the catalog); panels.pin(panel_ref, layout)
    attach.resolve(kind toolbox|runs|tile|repo|dataset, ids) -> [LibraryRef]
    explain(subject|run|pod|block) -> plain words + diagram spec
```

Every method takes the principal first (library AD-7); `caller_kind user | agent | workflow` is logged.

### 6.1 REST (under `qmx_control`)

| Area | Routes |
| --- | --- |
| drafts | `GET/PATCH /api/lab/subjects/{id}/draft?ref=`, `POST …/validate`, `POST …/save`, `POST …/publish`, `POST …/import`, `GET /api/lab/palette` |
| runs | `POST /api/lab/runs`, `GET /api/lab/runs?subject=&machine=`, `GET /api/lab/runs/{id}`, `GET /api/lab/runs/{id}/logs` (SSE), `POST …/cancel|pause|resume`, `GET …/explain`, `POST /api/lab/compare` |
| scenarios | `POST /api/lab/scenarios/draft`, `POST /api/lab/scenarios/presets`, `POST /api/lab/scenarios/run`, `GET /api/lab/sweeps/{run}` |
| training | `POST /api/lab/training`, `GET /api/lab/training/{run}`, `GET/POST /api/lab/models`, `GET/POST /api/lab/slots` |
| data, compute | `GET/POST /api/lab/data`, `GET /api/lab/compute`, `POST /api/lab/compute/{name}/preflight`, `POST /api/lab/compute/estimate`, `GET /api/lab/agents` |
| pods | `GET/POST /api/pods`, `GET/PATCH /api/pods/{id}?ref=`, `POST /api/pods/{id}/save|discard|trail|test|send-to-paper`, `GET /api/pods/results`, `GET /api/pods/blocks`, `POST /api/pods/blocks`, `GET/POST /api/pods/stress-scenarios` |
| paper | `GET /api/paper/{id}`, `POST /api/paper/{id}/pause|resume|extend|stop|promote`, `GET /api/paper/{id}/decisions` (SSE), `GET /api/paper/{id}/checks` |
| panels | `POST /api/lab/panels`, `POST /api/lab/panels/{id}/pin` |
| events | `GET /api/engine/events` (engine SSE; Lab names in section 8) |

Auth: the existing `qmx-control` bearer; agent calls arrive through the MCP tools below.

---

## 7. The capability pack (AD-14): 17 UI tools → service operations → Effects

| UI tool (shot 21 composer) | Service operation | Effect | Note |
| --- | --- | --- | --- |
| `qmb.backtest` | `runs.start("backtest", …)` | DOMAIN_WRITE (test mode) | test mode on a draft (DOMAIN_WRITE); a live run of a published version goes through the engine's `workflows_run` (MANAGE, asks once, engine SOLUTION-DESIGN §13) |
| `qmb.sweep` | `scenarios.draft` + `scenarios.run` | DOMAIN_WRITE | no spend ask (ruling 27); the estimate is shown, never gated on |
| `qmb.walk_forward` | `runs.start("walk-forward", …)` | DOMAIN_WRITE | |
| `qmb.robustness` | `runs.start("robustness", …)` | DOMAIN_WRITE | |
| `qmb.optimize` | `runs.start("optimise", …)` | DOMAIN_WRITE | trial cap from the family ledger |
| `lab.train` | `training.start` | DOMAIN_WRITE | no spend ask (ruling 27) |
| `lab.import_model` | `models.import` | DOMAIN_WRITE | |
| `graph.edit_draft` | `drafts.patch(ops)` | DOMAIN_WRITE | onto `refs/agents/<session>/<item>` |
| `code.edit` | `drafts.patch({code})` | DOMAIN_WRITE | same ref |
| `lab.add_panel` | `panels.propose` | DOMAIN_WRITE | the operator pins |
| `compute.place` | `compute.preflight` + `compute.place` | DOMAIN_WRITE | choosing among registered placements never asks; adding a new provider is the engine's onboarding flow (MANAGE once, engine AD-30) |
| `data.inspect` | `data.inspect` | READ | |
| `pod.edit` | `pods.patch` | DOMAIN_WRITE | agent ref; merge into `main` is MANAGE (publishing a lifecycle kind, ruling 80) |
| `pod.test` | `pods.test` | DOMAIN_WRITE | |
| `pod.stress_scenario` | `scenarios_stress.create` | DOMAIN_WRITE | |
| `pod.mix` | `pods.patch(set_members)` + `pods.test` | DOMAIN_WRITE | |
| `pod.paper` | `pods.send_to_paper` | MANAGE | "Needs your yes" (shot 27) |

Plus reads the pack needs that the composer does not list: `runs.list/get/explain`, `subjects.list`, `pods.get`, `paper.get`, `families.ledger`, `compute.list` (all READ). Rows are added to `qma.harness.tools.AGENT_OPERATIONS` **[retrieved]** as `lab_*` and `pod_*` names. Table rows are still a harness change no ruling grants, so they are part of engine HARNESS-REQUESTS H17 and need his grant (ruling 24); until then the Lab is driven from the UI, and the copilot reaches Lab drafts and test runs through the engine's H17 fallback (`library_save` of a draft plus the test-on-save watcher).

Pack layout (a Library item materialised as a plugin view, engine AD-55; no `.mcp.json`: its tools are the in-process `pack-qmx-lab` server, engine AD-61): `.claude-plugin/plugin.json`, `skills/<template>/SKILL.md` for `l1-idea-to-first-result`, `l2-run-this-part`, `l3-promote`, `l4-overnight-loop`, `d1-component-build`, `d2-spec-compile`, `d3-iterate-against-qmb`, `d4-variants`, `d5-indicator`, `d6-training`, `d10-code-health`, `pod-design`, `pod-test`, `pod-paper`; `prompts/lab-layer.md` (the Lab's system-prompt layer: it knows the open subject, layout and runs because the UI sends `context {subject, layout, ticked_runs, machine}` with each message).

---

## 8. Sequence flows

### 8.1 Run just this part (Build, selected step)

```mermaid
sequenceDiagram
  participant UI
  participant S as qmx_lab.service
  participant E as qmx_engine.service
  participant L as Library
  UI->>S: runs.start(template=draft, subgraph=[model], mode=test)
  S->>S: documents.validate(draft) incl. round trip
  S->>E: tests.run(draft_id, subgraph=[model])
  E->>E: fold memos: data, feature, label fresh → reuse; model stale → schedule
  E-->>UI: events: node_started(model) … node_finished(model, span)
  S->>L: workflow-run + artifacts on refs/runs/<run>
  UI->>S: drafts.get → GraphView with status badges fresh/stale/reran
```

### 8.2 New scenario → sweep (Test)

```mermaid
sequenceDiagram
  participant UI
  participant S as service
  participant F as families
  participant C as ComputePort
  participant E as engine
  participant Q as QmbPort
  UI->>S: scenarios.draft(subject v7, markets, timeframes, params, measures, costs, placement=qmb)
  S->>F: luck_warning(runs=72, family)
  S->>C: estimate(sweep, 72 runs, qmb) → 26 min (shown, never gated on)
  S-->>UI: ScenarioDraft{72 runs, estimate, warn, exploration_only=false}
  UI->>S: scenarios.run(draft)
  S->>E: runs.start(template=sweep, inputs={setup grid}, placement=qmb)
  E->>Q: qmb.compile ×1, qmb.sweep ×1 (app_op qmb_backtest: one qmb invocation on the QMB machine; QMB runs 72 isolated runs)
  Q-->>E: ledger lines + CT-32 by hash
  E->>S: backtest-result ×72 on refs/runs/<run> (evidence: the qmb placement is a controlled host)
  UI->>S: sweeps.grid(run) → cells; runs.list → rows
```

### 8.3 Train a model and plug a slot (Train, Model slots)

```mermaid
sequenceDiagram
  participant CP as Copilot (train start, shots 57-58)
  participant S as service
  participant C as ComputePort
  participant E as engine
  participant K as KernelPort
  CP->>S: training.start(spec{predicts=entry_signal, data=fx-m1, model=lightgbm}, placement=<a registered GPU row, e.g. an ssh provider row>)
  S->>C: preflight(placement) → healthy; estimate
  S->>E: runs.start(template=training)
  E->>K: ml.dataset, ml.split (CT-12 sealed), ml.leakage_check (grader)
  E->>K: ml.train on the placed worker; metric events → loss curves
  E->>E: ml.evaluate → likely_overfitting flag
  S-->>CP: run card; model object
  CP->>S: slots.plug(owner=bot v7, slot=entry_signal, model) → bot v8 (uses → model)
```

### 8.4 Design a pod, test it, send it to paper, promote (Pods)

```mermaid
sequenceDiagram
  participant UI
  participant S as service
  participant SIM as pod simulator
  participant E as engine
  participant N as NodePort
  participant P as Portfolio (human)
  UI->>S: pods.patch(trend-rider, add_block guards:news-aware, set_param kill=15)
  S->>SIM: trail(pod draft, sample trade) → size trail
  UI->>S: pods.save → v3
  UI->>S: pods.test([classic, trend, voltarget], bots[3], crises[7])
  S->>E: runs.start(template=pod-test) → pod.sim ×3, pod.stress ×21, pod.fan ×3, pod.head_to_head
  E-->>UI: results (equity, stress board, fan, head to head, interventions)
  UI->>S: pods.send_to_paper(trend v3, money=server-ledger, placement=contabo)  [MANAGE, his one yes]
  S->>E: triggers.create(paper, daily cron at session open, continuity, max_concurrent 1) → one finite run per day: paper.step per bar, paper.check at close
  E-->>UI: paper run, decisions stream, checks
  UI->>S: paper.promote(run)  [MANAGE]
  S->>N: mint_promotion_card(pod v3, unit parts, evidence refs)
  N-->>P: card waits in Portfolio › Road to live; sign + activate are two human clicks (TN-20)
```

### 8.5 The copilot edits a draft beside the operator

The Lab copilot calls `drafts.patch` on `refs/agents/<session>/<item>`; the operator keeps `refs/drafts/<item>`, and `main` holds published versions only; `library_merge` (library AD-7) brings the agent's draft into his draft (DOMAIN_WRITE) or, as publishing, into `main` (MANAGE) with a three-way merge of the JSON (structural) or the code (line); a conflict shows the comparison view; a governed kind (`bot`, `unit`, `book`, `bms`) or a lifecycle kind (`pod`, `workflow`) merges into `main` under MANAGE; `pod-block` stays DOMAIN_WRITE.

---

## 9. Defaults (Claude's defaults; every one UI-editable; one home: `qmx_lab.settings.DEFAULTS`)

| Setting | Default |
| --- | --- |
| `lab.cheap_run_seconds` (L2 stale-upstream prompt) | 120 |
| `lab.overfit_gap` | 0.05 of loss |
| `lab.luck_warning_runs` | 200 |
| `lab.trial_caps` | L4 200/night, D3 3 generations × 4 children, D4 12 variants, D6 6 configs (a multiple-testing bound of the research method, GAP-0048/0049, counted in the family ledger for deflated statistics; not a usage or spend limit, engine AD-40; he edits it) |
| `lab.robustness_ladder` | costs ×2 ≥ 50 % kept; trade shuffle 1,000 p95 DD ≥ −15 %; candle noise positive in 90 %; significance p < 0.05; walk-forward 7 of 9 clusters |
| `pod.fan_paths` / `pod.fan_horizon_days` | 1,000 / 90 |
| `pod.noise_quantile` | 0.9 |
| `paper.min_days` / `paper.extend_days` | 7 / 7 (seven daily runs, then seven more) |
| `paper.day_trigger` | daily cron at the market's session open, market zone (24-hour markets: the session boundary, 00:00 UTC for crypto); the paper day ends at the session close by its own rule; no wall-time cap (engine AD-40, removed after 41 H4) |
| `paper.band_quantiles` | p5–p95 of the pod's own test |
| `identity_rule` | D4 label set, `profile → branches-from` |

---

## 10. Failure modes

| # | Condition | Behaviour | Governed by |
| --- | --- | --- | --- |
| FM-1 | Code edit breaks the cell markers | `round_trip_failed` finding; the draft keeps the last good JSON; the editor shows the bad cell | AD-2 |
| FM-2 | QMB refuses the compile (dummy Book, key collision, synthetic-tainted data with a replay clock) | the refusal is returned verbatim as the node result; the run parks with the refusal text; no relabelling | AD-5 |
| FM-3 | A sweep cell fails | that cell's QMB ledger line is `aborted`; the grid shows ✕ (shot 19); the other cells stand; rerun is one cell | AD-4, engine AD-7 |
| FM-4 | The placement is not `healthy` at run start | `placement_not_healthy` refusal before any spend; the picker shows the failing check (shot: Connecting strip) | AD-8 |
| FM-5 | A run placed off a controlled host (`pc`, `qmb`) is cited as evidence | `exploration_only` results refuse `tested-by` edges and the robustness ladder; "rerun winners on the QMB machine" | AD-8 |
| FM-17 | A daily paper run dies mid-day, or a day is missed | the engine folds and resumes the run; missed days collapse into one catch-up run; `continuity` carries the ledger forward | AD-12, engine AD-10 |
| FM-6 | Second touch of a sealed window | `holdout_already_touched`; the template ends with "did not hold" marked; a new window is required | AD-6 |
| FM-7 | A block with side effects (network, clock) | `block_not_pure` at save; the block stays a draft | AD-10 |
| FM-8 | A pod block the node cannot run | `unsupported_blocks` in the composition; Ready-for-live row fails; paper still runs in the simulator | AD-11 |
| FM-9 | Live price feed drops during a paper run | `paper.step` waits (engine `waiting`); the band check pauses; no synthetic bars | AD-12 |
| FM-10 | Paper ledger and decisions disagree | `paper.check` fails `fills_matched`; verdict `drifting`; inbox item | AD-12 |
| FM-11 | An agent calls `pod.paper` or `publish` | MANAGE ask in chat ("Needs your yes"); nothing happens until the operator answers | AD-13 |
| FM-12 | An agent tries to loosen a gate | the validator refuses the Settings write; the template lint rejects the step | AD-13 |
| FM-13 | The kernel dies mid-cell | the attempt fails `retryable`; the engine ladder retries; snapshots restore state within the same run | AD-9 |
| FM-14 | Two agents edit one pod | each on its own ref; merge into `main` conflicts → comparison view | library AD-7 |
| FM-15 | Model slot named on a document that has no such port | `slot_unknown` | AD-7 |
| FM-16 | The family cap is reached (trials per night, children per generation) | `family_cap_reached`; the loop ends its revolution and writes the morning card with what exists | AD-6, AD-13 |

---

## 11. Seams and adapters (codebase-design)

| Seam | Adapters | Test strategy |
| --- | --- | --- |
| `QmbPort` | engine `app_op qmb_backtest` on the `qmb` placement (default); in-process `qmb.doors.api` (PC dev fallback); fixture adapter (recorded CT-32) | door parity: both real adapters give byte-identical `RunOutcome` for one setup (QMB B-1 parity test reused) |
| `KernelPort` | a local Python process inside the run's Job object (day one, spine AD-9 as amended 2026-10-18); the engine's `sandbox_python` kernel in a container or on a remote placement when he picks one; in-memory fake | the same cell suite across adapters; snapshot/restore round trip |
| `ComputePort` | the engine's `WorkerPort`/`GatewayPort` over `qmx_remote` providers; local-only fake | preflight states asserted per provider |
| `PodCompilerPort` | `pod_book_bms`; `pod_policy_pair` (later); identity fake | every catalogue block is either placed or named unsupported; the compiled Book/BMS passes QMB's dummy check |
| `NodePort` | node doors over the three thin doors (TN-17); fake with canned seats and MIS snapshot | the Lab test suite never needs a node |
| `LibraryPort`, `qmx_engine.service` | consumed as given by the parents; in-memory fakes from their suites | — |
| document kinds (internal) | one class per kind | round-trip property tests per kind |
| the pod simulator (internal) | one implementation | golden trails and stress cells; purity check (same inputs, same output) |

Deletion test: remove `qmx_lab` and the editor, the palette, the scenario builder, the pod simulator, the family ledger and the 17 tools reappear across the UI, the control service, the engine and the harness. It earns its depth. The interface is the test surface: the Lab's suite crosses `LabService` and the five ports only.
