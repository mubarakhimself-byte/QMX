# Independent backend composition review

Date: 2026-10-04. Reviewed tracked candidate `6ea6da67433d7e47878b019db01ed20ec366caad` in `task-12/backend-candidate`. Scope: independent read-only semantic review of the five reviewed patches on the native/skills ancestry, chiefly shared daemon composition, startup cleanup/restoration, descriptor routing, session authority and environments. No candidate or original source was edited; no dependencies were installed; no tests, providers, credential reads, network calls, trading, UI, publication or deployment were performed by this reviewer.

**Verdict: no actionable runtime patch-composition defect found in the reviewed scope.** This approves the semantic composition for its bounded integration milestone; it does not establish full backend or release acceptance. The integrator's runtime verification remains separately owned evidence.

## Identity and patch preservation

`git merge-base --is-ancestor bf3c6b59 HEAD` returned 0. Candidate history preserves the exact native/skills baseline `bf3c6b592e89917c17747eb1072203a28241e74a`, itself directly following `1f3b98f6b6f268e98f0f14edbb918b727069eb9c`.

Each source/candidate pair has identical output from `git show <commit> --pretty=format: | git patch-id --stable`:

| Reviewed source | Applied candidate | Stable patch ID |
|---|---|---|
| `23fba3d5` | `26aa658d501ba660150e31e1ce1e5af1f507f248` | `48a029587241687741022c6f52148278d2e99c5b` |
| `797159d1` | `ebe05ea3a4986c7acabd78626f05fc50f0612a01` | `bb772397d9d1e56c08af556ab7525dca4d3b9f3c` |
| `4122420d` | `fa68378c2cfcc05e6979fb055cf5c2ce8a5ce808` | `401184d75599d07a156b03251e036512da1d5fc0` |
| `61268744` | `3308542c27c74ad9dc8d2d53b66ffc9a077ea52d` | `cc4c274f42163a43ae03a5cc83705bb61b035ab3` |
| `8bee17d4` | `6ea6da67433d7e47878b019db01ed20ec366caad` | `e2a1a44678eaeee201342b1bb3af54ea85b62c96` |

Tree checks also returned no differences for `git diff 4122420d HEAD -- qmb packages/qmf-data` and `git diff 8bee17d4 HEAD -- qmn packages/qmf-venue`. The inspected `provider_config.py`, `domain_tools.py`, all `pyproject.toml` files, dependency requirements and `uv.lock` files have no diff from `bf3c6b59`. Existing native restrictions and SDK skills/hook policy therefore remain intact.

Candidate dirty state at review end consisted of the integrator's new untracked `tools/backend-integration-check.ps1` and `qmx-agents/packages/qma-daemon/tests/test_combined_backend_composition.py`. These are draft additions outside the reviewed tracked SHA; the latter was read as supplementary acceptance design, not included in the patch-preservation verdict.

## Shared daemon semantic checks

References below are candidate paths under `qmx-agents/packages/qma-daemon/src/qma/daemon/`.

* **Combination preserves both contributions.** Comparing the final `process.py` against reviewed spot `8bee17d4` leaves exactly QMB's optional local-environment import/registration/pass-through plus the native/skills `AgentExtensions` import, configuration argument and forwarding. There are no unexplained replacements or dropped native/skills configuration calls. Comparing against `bf3c6b59` shows the reviewed QMB and spot additions together.
* **One environment authority.** `process.py:914` creates/registers the optional operator declaration before persistence opens and passes that same registry at `:987`. `composition.py:53` retains the provided instance and shares it among router, dispatcher, tools, backtesting and runtime service. An absent declaration retains normal unbound behavior. `bootstrap_config.py` accepts exact `provider_ref` and `network=none`; its own documentation correctly says this declaration does not enforce an OS network sandbox or mint CT47 provenance.
* **Startup refuses without lock recursion.** Spot configuration is loaded after the live roster is activated. Configured instance, enabled tool contribution and package version are checked before binding. New refusal branches at `process.py:1092`, `:1111`, `:1117`, `:1123` call `_release(release_process_gate=False)` while `compose` owns the non-reentrant process lock. `_release` still closes the journal, transport and substrate; the optional flag only avoids reacquiring that lock. The global holder is installed only at successful composition completion. No spot reader/writer is created during startup.
* **Restoration is compatible with SDK startup.** Configured spot reads restore durable product sessions before use. If SDK requests are also configured, `configure_agent_requests` restores the same journal again. `ProductSessionService.restore_from_journal` folds authoritative session snapshots and replaces its in-memory indices; it writes the SQLite projection without appending new session events. The second restoration is redundant but does not mint a grant, overwrite host spot bindings, or execute a request. The shared service instance is retained.
* **Read descriptor and grants remain bounded.** `_operation_descriptors` adds only the spot read descriptor when at least one explicit host binding exists. The spot operation reaches the existing authenticated command/invocation path and existing `dispatch_public_call` grant/retry admission. Open-session checks pin contribution/package/config and opaque account authority; a retained session cannot silently become a different account merely because the same config revision is reused. Grant routing requires the correct enabled contribution and current binding. Invocation requires exact provider/venue/account payload equality and the session's host authority token; execution validates contribution/package/config again.
* **Writer/execution authority stays outside the daemon read path.** `spot_state.py` imports neither QMN runtime nor its account writer. Only operator configuration supplies an absolute state path. Each read opens SQLite with `mode=ro` and `PRAGMA query_only=ON`, checks retained view version/scope/policy/simulation identity, and returns storage/policy refusals for absent or inconsistent evidence. The model tool-provider configuration remains unchanged and exposes no new submit/cancel tool. Retained evidence does not establish writer/feed liveness.

## Reproducibility finding and available behavior evidence

The first integrator seam run in `evidence/seams-800ec466812a4930a99b89bf61372da2` recorded **57 passed, 3 failed**, with all three failures preserved. Its Python was the existing `task-6/sdk-venv/Scripts/python.exe`. The QMB process tests explicitly derive `Path(sys.executable).with_name("qmb")`; that interpreter had no sibling QMB entrypoint, yielding Windows `FileNotFoundError`. Adding PATH alone cannot repair these exact fixtures.

**Actionable entrypoint prerequisite:** use an existing interpreter with its sibling installed QMB launcher, or provide a reviewed portable-entrypoint adaptation; record that executable and import origins in the reproducible command evidence. The integrator has reported selecting the existing task-8 QMB environment with current candidate sources before read-only dependency paths, and is recording Scripts/PATH for other lookup paths. This is an execution-harness prerequisite, not evidence of a runtime composition regression. Its resolution must be established by the completed rerun; the initial red run must remain available.

The completed integrator rerun in `evidence/seams-7df354202b8e475cac214334f4aba29a` reports **56 passed, 2 skipped**, exit 0, using the existing task-8 QMB interpreter. Its new paired composition test covers one startup configuration containing offline SDK skills, spot retained reads and the shared QMB environment, then repeats paired operations across restart. This reviewer read its setup and authenticated socket assertions and inspected the completed result, but did not execute the test. Prior source-lane test counts in the work ledger and imported review documents are historical evidence only.

**Acceptance gap in that rerun:** cached pytest node IDs show the new combined case added but all four cases from `test_native_configured_daemon.py` absent compared with the initial run. The module uses top-level optional SDK `importorskip` calls; a native-routing case also uses function-level `importorskip`. The two skips therefore must not be counted as complete native seam verification. The integrator was notified to restore optional SDK visibility and preserve exact reasons/inventory, or explicitly retain this execution-environment limitation. The initial run exercised the four native cases successfully but failed the three QMB executable cases; neither run alone demonstrates the whole roster under one setup.

## Bounded acceptance limits and next checks

1. Pin the final tracked milestone SHA, include reviewed runner/test additions, and record the completed combined seam result plus interpreter/dependency/import provenance. The semantic verdict above is anchored to `6ea6da67`; later runtime changes need their own review.
2. Preserve full appropriate component gates and every failure/skip separately. The source spot review records full QMN at 1,070 passed / 39 failed / 23 skipped; the data ledger records 14 broad failures. These do not become green through composition or through a passing QMA count.
3. QMB environment wiring is not legitimate CT47 authoring/public projection ingress. Actor-dispatched owner/provenance authoring and projection bridge remain unresolved; do not invent records to claim their acceptance. Paired Dukascopy observations and correction folding also remain outside this review.
4. Full native authenticated provider operation, ordinary native tools, remote endurance, distributed fencing, cold restore/release packaging, DeepSeek policy/key support, spot FX/live venue execution, and wider memory/actors/workflows/API/DevOps acceptance are unproven or pending as recorded in `BACKEND-WORK-LEDGER.md`. No whole-backend readiness claim follows from this review.

The candidate and originals remain preserved. No protected merge or push is approved by this review.

## Addendum: bounded native cancellation race fix

Read-only follow-up on 2026-10-04. Base candidate HEAD is `db8bd82b2010cd79bfd148108c7e190c99cd4013`; the reviewed fix is an uncommitted five-line addition to `request_runtime/native_sessions.py`, accompanied by `test_cancellation_during_active_validation_preserves_observed_interrupt` in `test_native_sessions.py`. No repository source was changed or tests executed by this reviewer.

**Verdict: approve the bounded fix and its regression test. No actionable defect found in this change.**

`RequestRuntime.cancel` persists the cancellation-requested state and sets the request token while holding its runtime lock. The native guard first checks that token, then calls canonical `validate_active_request`, which acquires the same lock. Cancellation can complete between these two observations: the first token read sees false, but validation subsequently refuses the now-cancelled request. Previously, that refusal selected `scope_interrupt`; the matching native interrupted terminal then produced an interrupted record instead of the user's requested cancellation.

The added token recheck occurs only after canonical validation refuses. It maintains refusal and stops continuation in either case; it changes the cause to `cancellation_requested` only when the host token is now set. This is consistent with token precedence already present at guard entry. With the token unset, revoked/expired/retargeted scope continues to raise `scope_interrupt`. Simultaneous cancellation and scope change still forbid disclosure and tools. Shutdown's frozen request record also remains authoritative against late completions.

The terminal evidence rules are untouched. `ProviderCancelled` still requires a matching observed native `interrupted` terminal and the cancellation stop cause. A token, interrupt request, timeout, identity mismatch or absent terminal alone does not prove cancellation: submitted work without a terminal continues to become `outcome_unknown`. A completed native terminal still takes precedence over the interruption request and validates current context before returning content. No grant, retry, provider, credential, SDK policy or tool authority changes are introduced.

The regression test uses the real request runtime, journal and cancellation method. It wraps canonical validation only to deterministically perform cancellation after the guard's first token read, then delegates to the original validator. The fake native backend waits for host interruption and supplies a matching interrupted terminal; the test asserts cancelled status/error, backend interruption/cleanup, and absence of host observations. This exercises a real state transition rather than mocking the final outcome. The preserved `evidence/native-race-baseline.txt` shows the exact test fails against the old runtime source with `interrupted` / `scope_interrupt` (**1 failed**).

The integrator's completed focused rerun at `evidence/native-cb1701638c36408b8ae61745d02f7335` records **81 passed, no skips, exit 0** in 78.66 seconds. This reviewer inspected that output; execution remains owned by the integrator. The runner now checks for the sibling installed `qmb.exe` where required and places candidate sources before read-only dependency paths. The fixed native dependency visibility resolves the earlier optional-native omission for this focused run. Full component/release acceptance and real authenticated native providers remain outside this addendum.

Reviewed file SHA-256 identities (working-tree bytes, before final commit):

| File | SHA-256 |
|---|---|
| `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_sessions.py` | `475770D7549B3A2F293CFF7BC71240DAF8FCFD629044E93A0CF8AD0C79B07932` |
| `qmx-agents/packages/qma-daemon/tests/test_native_sessions.py` | `F502E990AEA705ACBA6D5C11E33CD781B1027A49D2D2EF10BD2312708C1F58BC` |

The current ledger is `_docwork/backend-integration-ledger-draft.md`; the next ownership seams are `_docwork/backend-next-seams-draft.md`. Earlier references to the workspace ledger describe its location at the initial review. This addendum authorizes no merge, push, publish or deployment.
