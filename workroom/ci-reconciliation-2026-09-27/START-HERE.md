# QMX integration reconciliation — 27 September 2026

## Current decision

**Latest instruction, 2026-09-27:** ALL new feature coding is paused, including independent backlog work. Sequence is existing backend core assurance, then middleware, then UI. Only CI/factory infrastructure repairs may proceed now. The user does not authorize a large Codex backend audit; external service/model selection comes first. No quality percentage or backend readiness has been established. Planned Epics 66–73 must remain distinct from the implemented baseline through Epic 65.

Dedicated repair chat: **Repair QMX CI and factory enforcement**, thread `01a0e2ad-ed5b-7913-b591-81b4034274f7`, local. [Dispatched scope and acceptance requirements](REPAIR-TASK.md). [Reviewer/skill study and audit staging](../reviewer-study-2026-09-27/START-HERE.md). This new instruction supersedes any earlier recommendation to continue independent feature work during reconciliation.

Pause new UI/product factory execution while establishing trustworthy integration quality. User authorizes Codex to take ownership of the factory fixes, but first requests Skylos documentation review, diagnosis, repository preservation on GitHub, and a concrete way forward. No factory repair, automatic finding cleanup, product coding, third-party reviewer activation or branch-protection change occurred in this diagnosis sitting.

The completed planning split remains Epic 66 → UI factory → ui-integration; Epics 67–73 → backend factory → integration. Backend prerequisites still apply. This document does not certify all story acceptance criteria or code correctness.

## Frozen baseline and repository state

- GitHub: https://github.com/MubarakHimself/QMX (public).
- Remote integration: **7b65732fc03683476c3221889d62d23ae8ccf88e**, latest commit Story 65.6.
- Local integration checkout: **34c148be404a375cbfd79fd4ce6997452e4f1d20**, 75 commits behind origin/integration, clean. Do not accidentally audit this old checkout as the current product or force-push it.
- UI factory branch: **d3c6e1234b3dbf865e78179bc262cbbe90b1cc90**, clean, already matches origin/ui-integration.
- Main before preservation: **92279dfe43922d60fabe38e29284ca52956ab75c**, matches origin/main but has pending architecture, documentation, completed epics, session evidence and the previously authorized UX archive relocation.
- integration is **unprotected** according to GitHub's branch API; repository rulesets API returned none. Failing Actions do not themselves prevent subsequent direct pushes.
- Research/mql5-article-library has unrelated untracked research; leave that separate workspace alone. Other inspected worktrees were clean.

## What the latest CI actually says

All three runs below evaluated the frozen remote integration SHA above.

| Check | Evidence | Actual result |
|---|---|---|
| Skylos | https://github.com/MubarakHimself/QMX/actions/runs/36274010671 | Scan and annotation steps succeed; Gate exits 1: **6,835 quality findings > 4,084 limit**, **137 dead-code findings > 80 limit** |
| QA Battery | https://github.com/MubarakHimself/QMX/actions/runs/36274010704 | `poe check` aborts at `fmt-check`: **51 files would be reformatted**, 445 already formatted. Later tasks in this sequence did not execute. Separate Vulture job succeeds. |
| QMN Linux | https://github.com/MubarakHimself/QMX/actions/runs/36274010736 | **10 Pyright errors** in qmn/src/qmn/bench/harness.py:133–134: Windows ctypes.windll/kernel32/psapi access under Linux typing. Later install/switch/rollback steps skipped. |

The latest successful Skylos and QA Battery runs returned by GitHub are dated **31 August 2026**, at **6e19f52d908e9ce772466830a5387eb2f874060d** (runs 33445431924 and 33445432355). No successful run was returned for the QMN Linux workflow on integration. The scanner configuration and workflows changed since the older green revision, so do not treat it as a directly comparable clean baseline without aligning tool versions and scope.

This evidence does not establish that all earlier code was perfect or all later code is defective.

## Scanner evidence and limitations

Downloaded artifact `skylos-report` from run 36274010671 (artifact ID 10917470014). Raw files kept outside the repository at `C:/Users/Mubarak/AppData/Local/Temp/qmx-ci-reconciliation-2026-09-27/`, including failed-step logs and `skylos-7b65732f/skylos-report.json`. The artifact contains code/context; this report records the useful aggregate facts rather than publishing a duplicate dump.

Read current Skylos documentation, then inspected and replayed the **pinned 4.33.2 PyPI wheel's gatekeeper.py**, rather than assuming the current website exactly describes the installed version. Using the retained scan report and the frozen integration pyproject configuration, its actual `check_gate` function returned:

```json
{"passed": false, "reasons": ["6835 quality issues (max: 4084)", "137 dead code issue(s) (max: 80)"]}
```

Replay process exited 1. This is a deterministic replay of the real gate against the recorded scan, not a fresh whole-repository scan. No source was changed to reproduce it.

Dead-code buckets: 1 unused function, 1 unused class, 5 unused variables, **130 unused parameters**, 0 unused imports and 0 unused files. A count of 137 does not mean 137 abandoned functional modules. Protocol signatures, overrides, plugin callbacks and public APIs need caller/contract evidence before edits.

Raw quality bucket contains 7,118 entries; the pinned gate excludes advisory quality rules from its blocking count, yielding 6,835. Largest raw rule groups:

- SKY-L027: 1,429 repeated-string findings.
- SKY-L028: 1,412 functions with many return statements.
- SKY-L009: 957 print/debug-output findings (including examples).
- SKY-C304: 877 long-function findings.
- SKY-Q301: 602 cyclomatic-complexity findings.
- SKY-Q306: 370 cognitive-complexity findings.

These are findings to classify, not 7,118 demonstrated runtime bugs. The scan covers **1,019 Python files**, records zero top-level analysis errors, and explicitly reports `complete_repository=false`. Exclusions include **qmx-agents**, qa, adws and the prose/archive trees. The qmx-agents workspace therefore needs its own quality/coverage investigation; this Skylos report cannot certify it. The report also describes AI verification as incomplete and SCA as complete_with_unresolved_versions; dependency coverage does not enumerate all transitive dependencies. Empty security/dependency finding buckets are not complete security assurance.

The repository's local CLI gate compares totals with configured ceilings. It does not identify which particular changes caused each finding. Current policy has max_quality=4084 and max_dead_code=80, with zero ceilings for security, secrets, reliability, AI-defect and dependency-vulnerability buckets. Do not silently raise these ceilings, reset a baseline or blanket-suppress rules to obtain a green run.

## Ordered recovery plan

1. **Preserve and freeze.** Save the current approved documentation/planning on main, keep code on its existing branches, retain the exact integration SHA and CI artifact identity. Do not merge integration to main as a backup operation. Stop admitting new product epics until reconciliation is complete; do not interrupt another active task without coordination.
2. **Restore meaningful deterministic feedback.** Reproduce and fix formatting/runner/type-check failures in an isolated branch. Execute the remaining checks which previously never ran. Inspect nested qmx-agents checks and scan scope separately. Resolve scanner execution/configuration problems separately from product-code defects.
3. **Build a classified finding inventory.** Each actionable item gets stable identity, rule/path/symbol, severity, supporting code and contract evidence, introduced/inherited/unknown classification, owner and a regression/acceptance test. Distinguish genuine defect, valid but lower-priority debt, documented intentional API/entry point, and scanner false positive. Do not delete code solely because a static scanner labels it unused.
4. **Give Grok bounded batches.** One owned component or rule family per repair batch, explicit evidence and allowed files, no unrelated refactors, no gate weakening, no baseline reset. Require fresh verification at the exact candidate SHA. Escalate ambiguity as a named blocked item rather than spending 19 hours chasing every red report from successive pushes.
5. **Repair factory enforcement before resuming it.** Local story checks → epic review → immutable candidate push → await all required checks for that exact SHA → verified promotion to the proper lane → cleanup. A red baseline is recorded separately from newly introduced findings; it does not become permission to add regressions or call a candidate green. Add branch-level protection only with a compatible candidate/PR flow, so no permanent deadlock is introduced.
6. **Add targeted independent review.** Review high-risk areas and bounded diffs with applicable contracts and user journeys. Repository-wide review needs a coverage ledger and several scoped passes; a giant PR is not exhaustive assurance. Keep mechanical checks in CI and semantic/runtime findings in review. Test clean installation, Linux/Windows behavior, failure recovery and realistic end-to-end operation before deployment.
7. **Reassess delivery after backend assurance.** Repair factory findings and demonstrate its positive and negative lifecycle, but keep ALL feature execution paused. The user now requires existing backend audit and bounded repairs first, middleware next, UI last. A repaired factory alone does not authorize Epic 66 or 67–73. Later combine accepted tips in a deployment candidate and validate them together after a separate readiness decision.

## Codex Review

Official documentation describes GitHub Code Review as review of a **pull-request diff**, using repository guidance and relevant context. It is useful as an additional reviewer, not evidence that an entire repository meets every specification. GitHub reviews count toward Code Review usage; local reviews count toward general usage. This diagnosis did not activate automatic reviews, purchase credits, post a review request, or establish the user's remaining review allowance.

Recommended first use: a bounded reconciliation PR with explicit contracts and changed-code scope, then expand based on findings and remaining allowance. Keep automatic review disabled until its trigger/cost behavior is deliberate. A separate broad repository audit, if chosen, should cover one subsystem at a time with a tracked matrix.

## Primary references

- Skylos getting started and output categories: https://docs.skylos.dev/
- Skylos CI/local versus cloud gates: https://docs.skylos.dev/ci-cd
- Skylos quality-gate/baseline model: https://docs.skylos.dev/quality-gate
- Dead-code confidence and cleanup behavior: https://docs.skylos.dev/dead-code-detection
- Installed-version source distribution metadata: https://pypi.org/pypi/skylos/4.33.2/json
- Codex GitHub review: https://learn.chatgpt.com/docs/third-party/github
- Codex usage categories: https://learn.chatgpt.com/docs/pricing

## Carry forward

User prefers Codex to own the remaining factory fixes instead of another Grok correction cycle. A separate scoped CI/factory repair chat is now started (see the latest decision above); its completion is not yet established. Grok remains the implementation worker for later well-scoped product repair batches. Grok 4.7 is excluded by user preference; respect 4.6/4.5 intent while honestly reporting any catalog restriction on per-agent model selection. The large backend audit must use separately selected external resources, not a broad Codex review in this chat.
