# QMX backend code audit — Aurelius/Codex work, Oct 1–6 2026

Auditor: read-only Claude subagent, 2026-10-07. No repo, branch or file outside the scratchpad was modified.
`git fetch origin` was run on C:\Users\Mubarak\Desktop\QMX (it only adds remote-tracking refs).
Tests ran in a throwaway copy: `git archive 2dfa57d7` was extracted to `scratchpad\src2dfa`, with its venv at `scratchpad\audit-venv` (built with `uv sync --frozen --python 3.14`).
Question 4 (the UI) was skipped on operator instruction. A GitHub-side check (section 4) replaces it.

Legend: **VERIFIED** = I checked it myself, with the command or path given. **CLAIMED-UNVERIFIED** = it appears only in the Codex docs.

---

## 0. Bottom line

- Aurelius's code is **real and large**. It is not stubs. The LangChain `create_agent`, LangGraph `StateGraph`, DeepAgents `create_deep_agent` and LangMem calls all exist and run in tests.
- **The local QMX repo does not contain it today.** The Desktop repo can see the sanitized public PR heads (after my fetch). It does **not** have the MA01–MA05 commits (`ea65…`, `2dfa…`, `8ef2…`, `a906…` are all missing objects). The only full copy of MA02–MA05 is the bare repo `D:\Codex-Recovery\2026-10-04\integration-base.git` (33 MB). D: is a single point of failure.
- **Nothing is merged and nothing was ever CI-checked.** PRs 20–24 are drafts with 0 check runs. The PR bases are not `main` or `integration`, so the workflows never trigger.
- **PR20 hides the biggest change.** Its base is `qmx-stop-checkpoint-2026-10-01`, which is 316 commits and +170,860 lines (+72k of Python) ahead of `origin/integration`. No PR covers those 316 commits.
- **Tests: mostly green, with real failures.** A focused run of the weekend modules gave 408 passed, 5 failed, 3 skipped. In the full qma-daemon suite, 2 files fail at collection. The actor/canonical-join flows **fail reproducibly in isolation**: 4 tests where a request stays "running" past its deadline. The suite is very slow (about 1,868 tests; under 25% finished in 19 minutes).
- **Over-engineering is heavy and real.** There is a 4,007-line `DaemonProcess` god class. There are 223k lines of markdown against 742k lines of Python in the tree, 296 `_docwork` files, and 2,049 decision-ID references (DEC/SCN/GAP/AD) inside daemon source comments. Several modules are wired only into tests. The agent core and mini-app staging code are worth keeping but need to be collapsed.

---

## 1. Where the code lives

### 1.1 Map (VERIFIED)

| Location | Head | Contains | Reachable from Desktop QMX repo? |
|---|---|---|---|
| GitHub `main` | `c3e8ec5e` (2026-09-27) | pre-Aurelius | yes (local main = same) |
| GitHub `integration` | `a0e87697` (2026-09-30) | last factory merge (PR19) | yes as `origin/integration` |
| local `integration` | `fdc76703` | **diverged**: 7 local-only commits ("fix epic 70 destination control lifecycle"…), 29 behind origin | local only |
| GitHub `qmx-stop-checkpoint-2026-10-01` | `7b4ece09` | 316 Oct-1 commits on top of integration (+170,860/−4,486 lines, 1,141 files) | yes after fetch |
| GitHub `qmx-work-release-checkpoint-2026-10-01` | `01fed525` | Oct-1 checkpoint | yes after fetch |
| PR20 `review/backend-baseline-public-20261004` | `3a86eee0` | base = stop-checkpoint; 62 commits, +28,149/−554, 189 files | yes after fetch |
| PR21 `review/canonical-join-public-20261004` | `74ccf3bb` | base = PR20; 7 commits, +5,956/−324 | yes |
| PR22 `review/backend-ci-public-20261004` | `c738d707` | base = PR20; 2 commits, +23/−8 (CI trigger edits only) | yes |
| PR23 `review/backend-capabilities-public-20261005` | `5aed6d7f` | base = PR21; 17 commits, +5,817/−130 | yes |
| PR24 `review/backend-recovery-public-20261005` | `da6955af` | base = PR23; 12 commits, +2,139/−181 | yes |
| Recovery bare repo `D:\Codex-Recovery\2026-10-04\integration-base.git` | 24 branches | full private history incl. `ea65b50d` (final-integration), `2dfa57d7` (MA04 accepted), `8ef21bf8` (MA05 unaccepted) | **no** |
| Recovery worktrees | 21 (`git worktree list` on bare repo) | one per lane, e.g. `2026-10-05\ma04-publication-repair\worktree` @ `2dfa57d7` (clean) and `final-integration\worktree` @ `ea65b50d` (clean) | no |
| Bundles | 34 `*.bundle` files under D:\Codex-Recovery, all small incrementals (≤1.1 MB) | each needs predecessor commits, so none is standalone | no |
| `a9063ce3` sanitized MA01 publication | only inside `publication-miniapp-local\candidate-publication.bundle` | not in the bare repo, not on GitHub | no |

Commands: `gh pr list --state all`, `gh pr view N --json ...`, `git for-each-ref`, `git --git-dir=…integration-base.git for-each-ref / worktree list / cat-file -t`.

Missing from the Desktop repo after fetch: `ea65b50d`, `2dfa57d7`, `8ef21bf8`, `a9063ce3` ("Not a valid object name").
Missing from the bare repo: `da6955af`, `3a86eee0`, `c3e8ec5e`, `a9063ce3`. `a0e87697` and `7b4ece09` are present in both.

### 1.2 Source vs public SHAs: related? (VERIFIED)

- Both histories share `7b4ece09` (stop-checkpoint) as an ancestor. Each has 98 commits from `7b4ece09` to its head (`ea65` private, `da69` public). So the public history is a **rewritten parallel copy** of the same 98 commits, not a fork.
- Tree comparison, `ea65b50d` (private) vs `da6955af` (public PR24): 3,789 vs 3,703 files, 128 differing entries.
  - 68 entries are `_docwork/*` files, dropped from the public copy.
  - The rest are `qa/backend-quality/*`, `release/evidence/spot-*`, `qmx-agents/examples/*.md` (rewritten), 3 ADRs (edited) and **one code file**: `qma-daemon/tests/test_deep_agent_comparison.py`.
  - **All production Python is byte-identical** between the private `ea65` and public PR24. "Sanitized" means docs and evidence removed, not code changed.
- `ea65b50d` is an ancestor of `2dfa57d7`: 14 commits, +16,868 lines. Of that, +8,607 is Python (MA01–MA04: `staging/app_candidate.py`, `app_validation.py`, `app_publication.py`, `qma-wire/panel_composition.py`, discovery queries, `process.py` +387, qmb `doors/cli/host.py` +241). The other ~8,249 lines are md/json.
- `2dfa→8ef21` (MA05): 31 files, +2,619/−25.

### 1.3 Volume by date (VERIFIED, `git log --date=short`)

- `a0e87697..7b4ece09`: 316 commits, all dated 2026-10-01 (08:21–18:24). First is "Assemble pinned published backend, governing docs and reserved UI baseline". No PR reviews this range.
- `7b4ece09..2dfa57d7`: 112 commits (10-02: 2, 10-03: 2, 10-04: 73, 10-05: 31, 10-06: 4).
- Weekend range `7b4e..ea65`: +36,860 Python lines (205 files) and +13,166 md/json lines.
- Authorship of 413 of the 428 commits in `a0e8..2dfa` is **"Mubarak <himselfmubarak@gmail.com>"**, the operator's identity, although Codex wrote them. The rest use `codex@openai.com`, `codex@local.invalid`, `codex-review@localhost`, `codex-local@example.invalid` or `noreply@openai.com`. `git blame` cannot tell operator work from agent work.

---

## 2. Backend inventory (at `2dfa57d7`, VERIFIED with find/wc)

| Package | src LOC | test LOC | test files | Notes |
|---|---|---|---|---|
| qmx-agents/qma-daemon | 95,253 | 61,680 | 167 | agent host; Aurelius added `request_runtime/` (11,323 LOC, 33 files) and staging app_* |
| qmx-agents/qma-core | 25,113 | 8,348 | 44 | ontology/ports |
| qmx-agents/qma-wire | 18,367 | 8,091 | 44 | wire schemas, panel_composition (MA03) |
| qmx-agents/qma-ui-contract | 0 | 0 | 0 | **empty stub** (STUB.md only) |
| qmb (backtest) | 107,043 | 48,590 | 112 | |
| qmn (node/live) | 103,520 | 42,274 | 115 | |
| qml (research lang) | 19,969 | 12,229 | 34 | |
| packages/qmf-* (7 pkgs) | ~73k | ~45k | — | core/data/indicators/registry/risk/structure/venue |
| qa/ | 45,937 py | — | — | per-epic acceptance tests (epic_05…epic_19) |
| Whole tree | 742k py lines in 2,087 files | | | plus **223k md lines in 1,069 files** |

### 2.1 qma-daemon layout (LOC by subpackage)

request_runtime 11,323 · taskgraph 10,846 · plugins 7,019 · staging 5,618 · sessions 4,892 · envs 4,037 · backtest 3,489 · hooks 3,474 · journal 3,123 · persistence 2,333 · ledgers 2,165 · artifacts 2,043 · discovery 1,962 · scheduler 1,908 · host_control 1,692 · bus 1,594 · experiments 1,341 · knowledge 1,278 · proxy 1,111 · tools 943 · … plus 14,452 LOC of root modules (`process.py` 4,828, `pairing.py` 2,426, `kit_journey*.py` 4,116, `http_pair.py` 799).

Pre/post attribution (VERIFIED with `git ls-tree`):
- `request_runtime/` does not exist in `origin/integration` or in `7b4ece09`. It is **entirely Oct 2–5 work**.
- `process.py` grew 2,937 → 3,984 (Oct 1) → 4,497 (PR24) → 4,828 (MA04).
- `kit_journey*.py`, `taskgraph/restart_fixture.py` and `pairing.py` were already on integration (the factory era), not Aurelius.

### 2.2 Spot-checks of claimed modules

| Claim | Verdict | Evidence |
|---|---|---|
| `tool_loop.py` uses LangChain `create_agent` | **VERIFIED real** | `from langchain.agents import create_agent` (L20); invoked at L624 with tools, checkpointer, middleware. The model is a `_TextActionModel(BaseChatModel)` adapter over QMA providers. Tests use `ScriptedText` fake models, so no live LLM is exercised |
| `research_workflow.py` LangGraph StateGraph | **VERIFIED real** | `StateGraph(ResearchState)` L401, uses `interrupt`/`Command`. Wired: `domain_tools.py:262` → `process.py:1227` (config-driven via `sdk.research_workflow`) |
| `actor_workflow.py` StateGraph | **VERIFIED real** | L388; wired from `process.py:1417` |
| `deep_agent.py` create_deep_agent: default or opt-in? | **VERIFIED opt-in only** | `create_bounded_deep_agent` is used only when `deep_agent is not None` (`tool_loop.py:605`). Otherwise plain `create_agent`. `subagents=[]`, general-purpose subagent disabled, filesystem tool limited to `read_file`. `DeepAgentSelection` comes from config (`process.py:322,1360`). **Not the default**, contrary to the operator's Sunday "DeepAgents default" direction |
| `memory_extraction.py` LangMem | **VERIFIED real but dead in prod** | `create_memory_manager` at L46. `LangMemExtractor` appears in 1 src file (itself) and 1 test file. Nothing in production calls it. `langmem` is an optional extra not installed by `uv sync`, and its 4 tests fail with ModuleNotFoundError instead of skipping |
| `persistence/schema.py` | **VERIFIED, but it is not a DB schema** | It is a version-stamp/open gate (`store_schema_version`), with 0 `CREATE TABLE`. The SQLite tables live elsewhere (`sqlite_writer.py`, `lifecycle.py`) |
| `authored_graphs.py` (Copilot proposal → MissionCompiler) | **VERIFIED real but dead in prod** | 116 LOC; `validate_graph_proposal` / `compile_graph_proposal` / `compile_authored_graph` are referenced only by the module itself and `tests/test_authored_graphs.py`. No production caller, so Copilot cannot actually turn a proposal into a graph. Also uses the Py3.14-only `except ValueError, KeyError, TypeError:` syntax (fine, since requires-python is `>=3.14,<3.15`) |
| `MissionCompiler` (`taskgraph/compiler.py`, 596 LOC) | **VERIFIED real, pre-existing** | referenced in 11 src / 17 test files; predates the weekend |
| `graph_storage.JournalCheckpointer` | **VERIFIED** | subclasses LangGraph `InMemorySaver`, journal-backed; 4 src / 6 test refs |
| `durable_memory.py` | **VERIFIED** | journal is the truth; LangGraph `InMemoryStore` is a rebuildable search projection (L333) |
| Providers | **VERIFIED real code** | `http_provider.ChatCompletionsProvider` (OpenAI-compatible `/v1/chat/completions`, OpenRouter path), `providers.CodexAppServerProvider` (subprocess JSON-RPC to Codex CLI), `native_codex.py` (openai_codex SDK), `native_claude.py` (`_ClaudeSDKLifecycle` marked "offline reviewed seam"). No test proves a live provider call. CLAIMED-UNVERIFIED: any real model ever answered |
| MA01–MA04 mini-app code | **VERIFIED real** | `staging/app_candidate.py` 652, `app_validation.py` 951, `app_publication.py` 869 (14–16 defs each, so very long functions), `qma-core/app_candidate.py` 179, `qma-wire/panel_composition.py` 426, `discovery/queries.py` +116. Tests: `test_app_candidate.py` 692, `test_app_validation.py` 541, `test_app_publication.py` 838, `test_ma01_discovery_queries.py` 603, all passing in my run. **Data-only**: no executable app runtime, as the docs themselves admit |
| HTTP/WS surface | **VERIFIED exists** | `http_pair.py` (pair start/confirm/renew, `/artifacts/stage`, `/host/*`), `process.py` has `_decode_ws_frame`/`_encode_ws_frame`, `_cors_headers_for_origin`, `_serve_bound_client` — a hand-rolled HTTP+WebSocket server, no framework |

Stub/fixture/dead code:
- `qma-ui-contract` package is empty.
- `kit_journey.py`, `kit_journey_weak.py`, `kit_journey_nested.py`, `kit_journey_retry.py` (4,116 LOC) and `taskgraph/restart_fixture.py` (925) are **test fixtures inside production src**. Their own docstrings say so ("thin weak-model kit-journey fixture", "crash-restart fixture"). Factory-era, not Aurelius.
- Wired only to tests: `LangMemExtractor`, `authored_graphs.*`. `create_bounded_deep_agent` has zero direct test references (it is reached only through the deep-agent selection path).
- `native_claude._ClaudeSDKLifecycle` carries `pyright: ignore[reportUnusedClass]`, an admitted unused class.

---

## 3. Test runs (VERIFIED, Python 3.14.6, fresh venv from `uv.lock --frozen`)

The recovery worktree's own `qmx-agents\.venv` is broken (no `Scripts\python.exe`), so nothing in it can run as-is.

| Run | Result |
|---|---|
| Collection of `packages/qma-daemon/tests` | **1,868 tests collected, 2 collection errors**: `test_combined_backend_composition.py` and `test_spot_daemon_binding.py` import `test_spot_paper_slice`, which lives in `qmn/tests/`. qma-daemon tests depend on another package's test files (cross-package test coupling) |
| Focused weekend modules: tool_loop, research_workflow, deep_agent ×2, authored_graphs, memory_extraction, durable_memory, actor_workflow, app_candidate/publication/validation, ma01_discovery, http_provider, memory_provider_seam | **408 passed, 5 failed, 3 skipped** in 5m41s. 4 failures = `langmem` not installed (optional extra; the tests should skip). 1 failure = `test_deep_agent_actor::test_one_selected_specialist_two_jobs` (request stuck "running"). It passed when re-run alone, so it is flaky under load |
| Full qma-daemon suite (19-min cap) | killed by timeout at ~25%: **443 passed, 5 failed** at that point |
| Re-run of those failures alone (no parallel load) | **4 failed, 65 passed** in 8m10s, reproducible: `test_canonical_request_join.py` ×3 (`test_host_admitted_request_has_canonical_owner…`, `test_second_request_cannot_claim_same_canonical_task_attempt`, `test_two_canonical_tasks_retain_behavioral_memory…`) and `test_composed_capabilities.py::test_selected_harness_joined_callback_and_memory[allowed]`. Symptom: request stays `status: running` past a `time.monotonic()` deadline. This matches the retrospective's "four historical actor deadline failures remain unresolved". They are **not** fixed in the accepted MA04 checkpoint |
| qmb suite | not run (separate root workspace; time cap) |

Speed: ~69 tests in 8 minutes for the canonical-join files, so the full daemon suite would take about 50+ minutes serially. pytest-xdist is not installed.

CLAIMED-UNVERIFIED: "2358 QMA passes", "843 MA04 tests", "QMB 1486", coverage 79.x%. I did not reproduce any aggregate count. The docs' own numbers already sit below the 80% coverage floor (gate exit 1).

---

## 4. GitHub side (VERIFIED; replaces the UI question)

- `gh auth status`: logged in to github.com as **MubarakHimself** (keyring, https, `gho_` token). That is the operator's GitHub account,; this machine's Claude account is a different identity. The GitHub **MCP** plugin fails with "Authorization header is badly formatted". The `gh` CLI works.
- `git remote -v`: `origin https://github.com/MubarakHimself/QMX.git`. Repo is **public** (`visibility=public`), default branch `main`.
- PRs: 20–24 are open drafts authored by MubarakHimself, all `MERGEABLE`, with **0 reviews, 1 comment each, 0 status checks** (`gh pr checks N` → "no checks reported"). Older draft PRs 9 and 10 (`codex/factory-enforcement-*`) are also still open. Last merged: PR19 (2026-09-30), which carried 7 green checks.
- **Why no CI on 20–24 (misconfiguration):** `battery.yml`, `skylos.yml` and `qmn-ubuntu-24.04.yml` trigger only on `pull_request: branches: [main, integration]`. The stack's bases are `qmx-stop-checkpoint-2026-10-01` and `review/*`, so nothing ever runs. PR22 adds those bases to the triggers, but it is a side branch that PRs 21/23/24 do not contain, and even PR22 shows 0 checks.
- `gh api .../actions/runs` returned `total_count 0`, although `integration`'s head shows 7 check-runs. Either run history was purged/expired or the token cannot list runs; I did not resolve which. Actions is enabled (`allowed_actions: all`). There are 6 workflows, all active.
- Branch protection:
  - `main`: **NOT protected** (HTTP 404 "Branch not protected"). Anyone with push access can push or force-push straight to main. This conflicts with the project rule that main moves only by the operator's squash-merge click. **Biggest config risk.**
  - `integration`: protected. Required checks are skylos, check, vulture, agents and qmn-ubuntu-24-04 (strict), `enforce_admins=true`, no force-push or delete, **no required reviews**.
  - `ui-integration`: same, plus `ui`.
- What Aurelius pushed in Oct 2026 (remote branches by committer date):
  - `qmx-stop-checkpoint-2026-10-01` (7b4ece09) and `qmx-work-release-checkpoint-2026-10-01` (01fed525), both Oct 1.
  - The 5 `review/*-public-*` branches (Oct 4–5).
  - Nothing to main or integration (`origin/integration` last moved 2026-09-30).
  - The proposed `review/backend-discovery-public-20261005` (MA01) is absent, as the docs say.
- Other misconfigurations:
  - Commits are authored under the operator's email by an agent (provenance is lost).
  - Several fake `.invalid`/`localhost` emails appear in public history.
  - A stray remote ref `origin` (= origin/HEAD) is listed.
  - Local `integration` has diverged from `origin/integration` (7 local-only commits, 29 behind).

---

## 5. Code-quality red flags and keep / simplify / delete

### 5.1 Red flags (VERIFIED metrics)

1. **God class.** `DaemonProcess` in `process.py` is **4,007 lines** (AST). Its largest methods are `_dispatch_paired_ct40` 354, `_execute_bound_product_operation` 337, `compose` 328 and `_dispatch_product_session_invoke` 277. Each Aurelius increment bolted more onto it (+1,891 lines since integration).
2. **Hand-rolled HTTP/WebSocket server** inside that class (`_decode_ws_frame`, `_encode_ws_frame`, CORS) plus a 2,426-line `pairing.py` and a 799-line `http_pair.py`. A small framework (Starlette/FastAPI plus websockets, which is already in the lock) would replace thousands of lines.
3. **Ceremony in source.**
   - 2,049 decision-ID references (DEC-/SCN-/GAP-/AD-/FR-Q/CT-) in daemon src comments.
   - Docstrings are written in governance prose. `request_runtime` alone repeats "canonical" 75×, "bounded" 64×, "admitted" 60×, "frozen" 51× and "admission" 50×.
   - Many functions spend more lines on refusal and digest checks than on behaviour (e.g. `authored_graphs.py`: 116 LOC to select one pre-pinned graph and call the compiler).
4. **Docs and evidence outweigh code.**
   - 1,069 md files / 223k lines in the tree.
   - `_docwork/` 296 files (7.2 MB), `qa/` 345 files (5.1 MB), `release/` 141 files, `_bmad-output/` 574 files (17 MB).
   - In the MA01–04 increment, docs/evidence lines (8,249) ≈ code lines (8,607).
   - In `D:\Codex-Recovery`: about 27 lane folders, each with REPORT/HANDOFF/evidence/seal files, and 34 bundles.
   - "Accepted", "independent review" and "safeguard" stages were run by the same agent family. This is staging theatre, not product progress.
5. **Duplicated layers.**
   - Memory: `daemon/memory/admission.py` (CT-43 "QMA supplies no memory engine") and `request_runtime/durable_memory.py` + `scoped_memory.py` + `memory_projection.py` + `memory_extraction.py` (~1,190 LOC).
   - Providers: `providers.py`, `http_provider.py`, `provider_config.py` and six `native_*.py` files (~1,680 LOC), plus `proxy/` (broker, egress, harness, local_proxy, opencodex, registry, router; 1,111 LOC). These are three overlapping ways to reach a model.
   - Workflows: `taskgraph/` (10.8k) as the canonical engine **and** LangGraph StateGraphs in `request_runtime`, glued by `canonical_join.py` (1,185 LOC), which exists only to reconcile the two.
6. **Dead or test-only code in prod paths:** `LangMemExtractor`, `authored_graphs.*`, the `kit_journey*` fixtures and `restart_fixture.py` in src (5k LOC), `_ClaudeSDKLifecycle`, and the empty `qma-ui-contract`.
7. **Test hygiene.** Cross-package imports of qmn test modules, optional-dependency tests that fail instead of skipping, wall-clock deadline flakes (4 reproducible failures), and a ~50-minute serial suite.
8. **Very long functions in the mini-app code:** `app_validation.py` has 951 LOC in 14 defs and `app_publication.py` 869 LOC in 14 defs.

### 5.2 Keep / simplify / delete (auditor's recommendation; QMX core = agent core + mini-app code)

| Area | Path(s) | Verdict | Why |
|---|---|---|---|
| LangChain tool loop | `request_runtime/tool_loop.py` (769) | **KEEP, simplify** | Real `create_agent` loop with budgets/checkpointer. Cut governance prose, split out `_TextActionModel` |
| LangGraph workflows | `research_workflow.py`, `actor_workflow.py`, `graph_storage.py` | **KEEP** | Real StateGraph + interrupt/resume, journal-backed checkpointer. This is the agent core |
| DeepAgents | `deep_agent.py` (196) | **KEEP, decide default** | Real, small. Either make it the default agent path (operator's stated wish) or delete it; opt-in limbo serves nobody |
| Scoped memory | `durable_memory.py`, `scoped_memory.py`, `memory_projection.py` | **SIMPLIFY → one module** | Merge with `daemon/memory/admission.py` into a single MemoryProvider seam |
| LangMem | `memory_extraction.py` | **DELETE or wire** | Unused in prod; optional dep not installed |
| Copilot proposal adapter | `authored_graphs.py` | **DELETE or wire** | Unreachable from any production path |
| Canonical join | `canonical_join.py` (1,185), `partition_retry.py` | **SIMPLIFY hard** | Exists to marry two workflow engines. Pick LangGraph for agent flows and keep taskgraph for deterministic jobs behind one interface. This is where the failing tests are |
| Providers | `providers.py`, `http_provider.py`, `provider_config.py` | **KEEP, collapse** | One provider interface: OpenAI-compatible HTTP + Codex CLI |
| Native SDK sessions | `native_claude.py`, `native_codex.py`, `native_sessions.py`, `native_boundary.py`, `native_composition.py`, `native_configuration.py` | **SIMPLIFY or park** | ~1.7k LOC, no live proof, overlaps providers |
| Proxy/harness | `daemon/proxy/*` | **SIMPLIFY or delete** | Third model-access path |
| Skills/hooks | `agent_extensions.py`, `sdk_middleware.py`, `hooks/` | **KEEP** | Small, LangChain middleware based |
| Mini-app staging | `staging/app_candidate.py`, `app_validation.py`, `app_publication.py`, `qma-core/app_candidate.py`, `qma-wire/app_*.py`, `panel_composition.py`, `discovery/queries.py` | **KEEP, refactor** | Real and tested; core for the mini-app SDK. Break up 900-line files into a small `miniapp/` package with candidate → validate → publish modules |
| Daemon host | `process.py` `DaemonProcess` (4,007) | **SIMPLIFY (split)** | Separate HTTP/WS transport, session dispatch, product ops and composition root |
| HTTP/WS transport | `http_pair.py`, WS framing in `process.py`, `pairing.py` | **REPLACE** with a framework | Hand-rolled protocol code is a liability |
| Taskgraph engine | `taskgraph/*` (10.8k, pre-existing) | **KEEP, review** | MissionCompiler is load-bearing; `projection.py` 1,960 and `nested.py` 1,530 need trimming |
| Fixtures in src | `kit_journey*.py`, `taskgraph/restart_fixture.py` | **DELETE / move to tests** | 5k LOC of fixtures shipped in the wheel |
| Empty package | `qma-ui-contract` | **DELETE** | stub |
| Docs/evidence | `_docwork/`, `release/evidence/spot-*`, `qa/backend-quality/*`, per-lane REPORT/HANDOFF/seal files in `D:\Codex-Recovery` | **DELETE from repo** (archive once) | Ceremony; already excluded from the public copy |
| qmb / qmn / qml / qmf | domain engines | **KEEP (not audited deeply)** | Large (100k+ each) but pre-existing domain code; out of this audit's depth |

---

## 6. VERIFIED vs CLAIMED-UNVERIFIED summary

VERIFIED:
- PR20–24 SHAs, stack and draft status, with 0 checks.
- The bare-repo SHAs (`ea65`, `2dfa`, `8ef2`) and their worktrees.
- Production code is identical between private `ea65` and public `da69`.
- The MA01–04 delta exists (+8.6k Python).
- LangChain/LangGraph/DeepAgents/LangMem calls exist.
- DeepAgents is opt-in only. LangMem and authored_graphs are test-only.
- Test results as listed in section 3, including 4 reproducible actor/join failures.
- main is unprotected and integration is protected.
- The Oct-1 316-commit range is not covered by any PR.

CLAIMED-UNVERIFIED (from the Codex docs):
- Aggregate pass counts (2358/843/1486/987).
- Coverage percentages.
- "Independent acceptance" of MA02–04 (performed by Codex's own reviewer).
- Installed-wheel replays.
- QMB production CLI child runs.
- MA05 author-only results.
- Port and process closure receipts.
- Any live model or provider call ever succeeding.
- The "app-read gap" reproduction (grant refusal for `qmb.analysis.project`).

## 7. Shortest honest path to a usable backend (no UI)

1. Preserve first. Copy `D:\Codex-Recovery\2026-10-04\integration-base.git` somewhere durable, or push branch `work/qmx-ma04-repair` (`2dfa57d7`) to a private remote. It is the only copy of MA02–04.
2. Decide the base. `da6955af` (PR24) is code-identical to `ea65`, and `2dfa` adds 14 commits on top. Importing `2dfa` as a single squashed branch onto `origin/integration` gives one reviewable diff, instead of the 316 + 98 + 14 commit ladder.
3. Fix CI reachability. Open that branch as a PR **into `integration`** so the existing workflows and required checks actually run. Protect `main`.
4. Fix the 4 reproducible deadline failures and the 2 cross-package collection errors before any merge.
5. Then start the YAGNI pass in section 5.2: split `DaemonProcess`, collapse memory and providers, and delete the fixtures and ceremony.
