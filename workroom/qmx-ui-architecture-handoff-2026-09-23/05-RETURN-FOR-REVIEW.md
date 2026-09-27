# What Grok returns for focused review

This is the completion contract for the research/architecture stage. Keep one concise entry point with paths to supporting detail. Output file names may follow the architecture skill; map them to the requirements below rather than creating redundant documents.

| Deliverable | Reviewable evidence |
|---|---|
| Reading and evidence ledger | Current session and both origin transcripts covered; every storyboard text/image role accounted for; layout decisions linked to sources; external observations distinguished from inference and inaccessible areas. |
| Current-state baseline | Repository, branch/commit and dirty-document snapshots; actual versus specified/stubbed capabilities; current core architecture version; API/SDK terminology verified or left unresolved. |
| Architecture candidate | Ownership and invariants across frontend/host/integration/core/workers/data; actual dependency choices and compatibility; local/VPS and visual/headless combinations; justified alternatives and consequences. |
| Experience and component contracts | Differentiated layout diagrams; graph/node/code/detail/return flow; attachments/scoped sessions; Library lifecycle; first-run/provider flow; loading/failure/recovery; reusable component inputs/events/state ownership; provisional visual conventions. |
| Change-impact map | Each requirement's current owner and evidence, then reuse/adapt/add/unresolved classification; affected contracts/storage/migrations/ops; explicit dependencies and unresolved assumptions. No screen-to-service invention. |
| BDD reconciliation | Retain/map the original 85 IDs; relate current scenario docs; add missing UI/headless/mixed journeys; trace outcomes to intended tests. Mark written, executable and executed evidence separately. |
| Delivery and verification plan | Representative real vertical slices; integration compatibility/cadence; independent backend review; combined deployment candidate; clean install/update/recovery and performance evidence; applicable trading evaluation only. |
| Decision/open-issue record | Accepted inputs, new recommendations, alternatives rejected with reasons, conflicts, defaults and consequential user decisions; no silent ratification. |
| Independent challenge | Record independent reviewers' findings, what changed, unresolved findings, and why the candidate is ready or not ready for the next stage. |

## The Codex review will ask

1. Does the proposed UI preserve the actual source layouts and latest ML/headless corrections?
2. Are observations and existing implementation distinguished from proposals and historical claims?
3. Can a user journey be traced through component state, an identified contract, its backend owner and recovery?
4. Does the component/extension model allow evolution without duplicating core infrastructure or forcing all capabilities into one shape?
5. Are local/remote lifecycle, version/authority boundaries, compatibility and installed-product behavior concrete enough to test?
6. Can Documentation Factory ingest this without filling major behavioral or architectural holes from guesswork?

The result of review may be “ready for Documentation Factory,” “ready after listed corrections,” or “not ready because of named unresolved decisions.” It is not production-readiness or implementation approval by itself. Dedicated full code review remains a separate task.

## Final response expected from Grok

Give the user the candidate directory, entry file, source/decision ledger, any material unresolved decisions and a short summary of changes recommended to the core. State whether any experiments/tests were actually run and their limits. Preserve/export the Grok session using the user's normal process. Stop before Documentation Factory, epics or coding unless the user subsequently directs that stage.

The user can then return to the existing Codex task with: “Review Grok's QMX UI/full-application architecture candidate at [path] against the handoff packet. Give a focused readiness verdict for Documentation Factory; do not start a whole backend code review.”
