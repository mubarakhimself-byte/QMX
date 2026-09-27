# Backend assurance: current decision and next work

Updated 2026-09-27. This records the user's latest direction and supersedes earlier proposals to continue independent feature work during reconciliation.

## Decision

All new product coding is paused. First establish confidence in the existing backend core, then address middleware, then resume UI work. CI/factory infrastructure repairs may proceed now. A large Codex implementation audit is explicitly not authorized because the user wants to conserve its usage. No external reviewer has been installed, activated, subscribed to, or given a paid audit job in this sitting.

“Backend first” is a release sequence, not permission to ignore its interfaces: backend contracts with brokers, persistence, workers, local/VPS execution and future UI remain part of backend assurance. Existing visual, headless and mixed mini-app/workflow capabilities all belong in the scope. A functional backend candidate is not established merely by passing static checks.

The user estimates the repository is large and that substantial code may already be sound. No percentage-quality estimate or exhaustive coverage claim has been verified.

## Work started

- Separate Codex chat **Repair QMX CI and factory enforcement**, ID `01a0e2ad-ed5b-7913-b591-81b4034274f7`, local, configured default model. [Exact dispatched prompt](../ci-reconciliation-2026-09-27/REPAIR-TASK.md). It may repair CI/factory infrastructure in isolated branches and create reviewable repair PRs. It may not start product epics, conduct the full backend audit, or merge product branches into main/deployment.
- Two lower-cost `gpt-6-luna` agents researched [reviewer services and current pricing](SERVICES.md) and [installed skills](SKILLS.md). These are research artifacts, not operational validation or endorsements of vendor quality claims.
- Existing diagnosis: [CI evidence and frozen references](../ci-reconciliation-2026-09-27/START-HERE.md). Existing reproduced factory defects: [F1–F6](../qmx-ui-factory-review-2026-09-27/REVIEW-ROUND2.md).

## Baseline and acceptance scope

The last verified remote backend tip was `7b65732fc03683476c3221889d62d23ae8ccf88e`, through Story 65.6. Refresh refs before the audit, freeze the chosen tip, and record it. The local integration-inspect checkout is stale and must not stand in for the current product.

Separate these categories before judging conformance:

1. Approved obligations claimed implemented in the frozen backend candidate.
2. Approved future work, including the currently unbuilt Epic 66 UI and Epics 67–73 backend additions.
3. Superseded architecture, historical brainstorming and optional examples.
4. Conflicting or ambiguous obligations that need a recorded decision.

The current authoritative documentation and accepted architecture determine intended behavior; epic/story IDs identify delivery claims. `_docwork` and origin transcripts supply provenance and context. Do not convert every historical idea into a mandatory feature. Do not hide a completed-story gap by relabelling it future work.

## Audit method to hand to the selected external worker

Start read-only with an inventory and coverage ledger, not a repair swarm. Map architecture responsibility to actual package/module, contracts, completed stories and evidence. Use subsystem clusters as working units and retain epic links. The first bounded pilot should include mini-app/workflow lifecycle and one adjoining contract because this was the largest product shift; exact files and dependencies must come from the inventory.

For each scoped obligation, record: requirement/source section, claimed delivery, owning implementation, supporting tests, observed behavior, and status (verified, partial, missing, conflicting, unverified, or out of scope). Record what was not examined. Separate functional correctness, architecture fit, maintainability, security, performance and deployment evidence.

Review cross-cluster behavior explicitly: authority/grants, mailbox and session identity, nested work/cancellation, durable artifacts and retries, failure recovery, broker/data boundaries, and local versus remote execution. ML checks must distinguish framework capability from availability/training/validation of particular models. An untrained model is a readiness limitation if required by the release claim; it is not automatically proof the whole ML framework is defective. Trading-specific paper operation applies to trading capabilities, not every mini-app.

Every proposed issue needs a concrete expected-versus-actual result, approved source when asserting a requirement mismatch, exact code/commit evidence, a reproduction or explicit verification gap, impact, confidence, dependency/scope and repair acceptance criteria. Classify scanner output as a lead until validated. Deduplicate and independently validate evidence before creating GitHub issues. Automated validation is the default; escalate genuine unresolved product/policy ambiguity rather than asking the user to adjudicate every warning. Do not require a minimum number of findings.

An external model can perform these scoped read-only tasks without consuming Codex quota. Model choice alone does not provide coverage: the coverage ledger, isolated tools, evidence checks and bounded cost controls still matter. No underlying-model benchmark or API-budget comparison has been performed in this study.

## Repair and promotion discipline

The CI repair task must publish a candidate, wait for required checks bound to its full commit identity, then allow only that tested commit to advance. Queued is not passed; missing or stale success is not passed. Record run links and resume state. A failed product baseline remains visibly blocked and cannot be made green by silent suppression or threshold increases.

For product repair later, Grok receives bounded validated issue batches with allowed scope and acceptance checks. Newly discovered unrelated defects become separate issues. A retry limit and a clear blocked report replace the previous unbounded 19-hour scanner-cleanup loop. Resolving infrastructure checks does not certify backend behavior.

Only after the read-only audit, prioritized repairs, meaningful automated tests, clean-install/runtime checks and explicit residual-risk disposition should a backend deployment candidate be considered. The user has not authorized merging to deployment or resuming feature factories in this sitting. A later release decision must state what is supported and what remains planned.

## Service selection

Use the service study to pick a small pilot before committing to a subscription. PR review, whole-repository conformance audit, and live API/UI verification are different jobs. Repository indexing does not prove every module was reviewed; a green scan does not prove every requirement was implemented.

The practical first shortlist is a free public-repository CodeRabbit review path or Greptile's individual allowance for change review, and a limited Qodo trial to assess its claimed linked-spec gap detection. None is accepted as the full backend auditor. TestSprite is a later live API/UI option; Reticle remains required by the user's project instructions for user-facing changes. Evaluate trials within their published terms and use spending caps.

Wayfinder is available for genuinely unresolved decision tracking. It is unnecessary to restart an interview or redesign already-approved architecture. The smallest useful skill combination is traceability plus bounded evidence-led review, adding test-quality/NFR analysis where the evidence map calls for it. See SKILLS.md for installed paths and actual limitations. No skill workflow was executed during this discovery.
