# CI and factory repair task

Created 2026-09-27 as Codex chat `Repair QMX CI and factory enforcement`.
Thread: `01a0e2ad-ed5b-7913-b591-81b4034274f7`. Host: local. Uses the user's configured task model; no model override was supplied.

This is the exact dispatched task prompt. Creation is not a claim that repairs are complete.

Repair QMX CI and coding-factory enforcement. This is an implementation task with a strict boundary: ALL new product/backlog coding is paused. The user wants backend core assurance first, middleware next, UI last. Do not start Epic 66 or 67–73, run either product factory, recreate epics/stories, run Documentation Factory, perform a repository-wide product audit, or merge product code into main/deployment. The large backend audit will be handled separately using non-Codex resources. Use Codex effort here only for reliable CI/factory control and bounded verification.

Start by reading:
1. C:/Users/Mubarak/Desktop/QMX/workroom/ci-reconciliation-2026-09-27/START-HERE.md
2. C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-factory-review-2026-09-27/REVIEW-ROUND2.md (F1–F6 are reproduced findings).
3. The previous REVIEW.md in that directory for history, then the actual current factory source and installed skills.
4. Applicable AGENTS.md and relevant CI/testing skills as needed. Do not invoke BMAD UX.

Verified starting references, which you must refresh before changing anything:
- Public remote https://github.com/MubarakHimself/QMX.git.
- Main documentation preserved/pushed at 03ad2f00ed585c8a2ba0ad564c566e74bf91dc49.
- origin/integration at 7b65732fc03683476c3221889d62d23ae8ccf88e, through Story 65.6.
- Local integration in .worktrees/integration-inspect is stale at 34c148be, 75 commits behind. Do not use it as the current baseline or force-push it.
- ui-integration at d3c6e1234b3dbf865e78179bc262cbbe90b1cc90 in C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory.
- Installed backend factory: C:/Users/Mubarak/.grok/skills/run-epics/SKILL.md. Installed UI factory: C:/Users/Mubarak/.grok/skills/run-ui-epics/SKILL.md. UI source under .grok/skills/run-ui-epics and tools/ui_factory on ui-integration.
- Completed backlog on main routes only Epic 66 to ui-integration and 67–73 to integration. Preserve this split.
- Parked 19-hour repair experiment is preserved locally/remotely at park/skylos-mill-2026-09-26, a2e8cf83. Restore commit 54f820dc has exactly the Epic 60 tree at 7223e1a6; later integration contains Epics 61–65. Do not revive or delete parked work wholesale.

Use an isolated checkout. Inspect attached artifacts and existing worktree ownership before reuse; otherwise create a managed worktree from the appropriate current remote ref. Keep shared main, unrelated research worktrees, and other agents' changes untouched. Use codex/ branches. Keep Python/backend and UI changes routed appropriately; share a promotion protocol without making backend depend on an unavailable UI checkout. Do not modify a skill under a running orchestrator: stage and verify changes, activate only at a safe boundary. Inspect activity rather than assuming no one is running.

Known CI at the frozen integration SHA:
- Skylos run 36274010671 scanned successfully, then failed its totals gate: 6835 quality >4084; 137 dead-code >80. 130 dead-code findings are parameters, not abandoned modules.
- QA Battery 36274010704 stopped at 51 formatting failures; later checks did not run.
- QMN Linux 36274010736 stopped at 10 ctypes Windows/Linux typing errors in qmn/src/qmn/bench/harness.py.
- qmx-agents is excluded from this Skylos scan and needs explicit coverage accounting.
- Integration was unprotected and repository rulesets were empty.
Retained scan artifact and logs are under C:/Users/Mubarak/AppData/Local/Temp/qmx-ci-reconciliation-2026-09-27/. The diagnosis already replayed pinned Skylos 4.33.2 gate logic against real artifacts. Do not rescan the whole product merely to rediscover these facts.

Deliver a working enforcement protocol for both factories:
1. Local story checks, applicable independent review and epic checks produce an immutable candidate.
2. Publish that candidate to a ref that triggers ALL required lane checks. Fix the trigger mismatch: some checks accepted factory-candidate tags, QA Battery did not. Test the real event/ref behavior.
3. Wait for exact repository/ref/full SHA/workflow identity and relevant latest run attempt. Never accept old success over newer failure, prefix/empty SHA, another branch, skipped/missing/cancelled/unknown results, or synthetic fixtures as production success. Queued/running means wait with bounded backoff and durable resume. Record run URLs, attempt, conclusion and candidate identity.
4. Completed success permits promotion of exactly the tested commit. Recheck candidate and destination under a lock, reject dirty or unowned destination checkouts, prevent mutable-ref substitution, and report local promotion/push partial failures accurately.
5. Remove product CI-bypass paths. Fixture mode must only operate in isolated fixture destinations. Cleanup happens only after verified completion; blocked work remains recoverable.
6. Enforce backlog lane ownership, exact story selection, runnable dependencies, and accepted completion records reachable on their proper destination. Mentioning a story ID in a commit is not accepted completion.
7. Wire story/content hashes, backend-contract requirements and genuine retained Reticle verdicts through normal dispatch, quality, cache refresh and promotion. Unknown/no/stale/missing runtime proof blocks user-facing changes. Reticle result must be tied to candidate, app and journey, not a self-written yes field.
8. Preserve Grok model policy (4.6 heavy, 4.5 lighter, no 4.7); report actual inherited model if workflow API cannot select per-child models.

Crucially, do not create another unbounded scanner-repair loop. Distinguish scanner/infrastructure failure, inherited finding, candidate regression and unclassified finding using comparable tool versions/config/scope and evidence. A pre-existing red baseline still blocks promotion unless a separate explicit policy decision is approved; it does not authorize broad repairs. Use bounded retries/repair attempts for in-scope factory defects. For unrelated backend findings, retain artifacts, deduplicate, create evidence-backed GitHub issues with expected/actual behavior, source contract if applicable, reproduction, severity, scope and verification steps, and stop that candidate with a clear report. Do not file thousands of raw scanner warnings as bugs. Do not lower thresholds, blanket-exclude directories, rename parameters mechanically, reset baselines, delete “dead” code, or apply parked refactors just to obtain green.

Repair workflow configuration and safe enforcement on both integration lanes, including applicable Python/frontend profiles and a clear account of excluded nested packages. Configure required branch checks where supported, using verified names/triggers and preserving existing policy. Avoid broad paid scans or new reviewer subscriptions. Source-level product formatting/type/logic findings outside CI infrastructure belong in bounded repair issues; do not drift into the backend audit.

Prove F1–F6 closed using focused regression tests plus a bounded isolated FACTORY-TEST lifecycle: normal dispatch and proof ingestion, intentional failed gate, repair/resume, live GitHub candidate checks and exact-commit promotion to a disposable test destination. Never use product epics as fixtures. Use Reticle for any user-facing fixture change. Synthetic tests cannot certify live GitHub or Grok/Reticle behavior; report unsupported/unavailable stages explicitly and keep readiness incomplete when required evidence is missing.

You may commit and push the scoped CI/factory repair branches and create reviewable PRs against the correct integration lane; attach created PRs with the app artifact tool. Do not merge to production branches or start feature execution automatically. Record any repository settings changed and how to reverse them. Keep a concise durable progress/closure report with tested SHAs, run links, remaining inherited blockers, installed-skill/source parity and exact agent wait/report instructions. Final response must distinguish “CI/factory enforcement repaired” from “backend product is green/ready”—the latter is not established by this task.
