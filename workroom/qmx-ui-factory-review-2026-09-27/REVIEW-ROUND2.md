# UI factory repair review — round 2, 27 September 2026

**Verdict: NOT READY for unattended product execution.** The repairs are meaningful, but the normal workflow still cannot reliably complete verification and promotion. Do not recreate architecture, Documentation Factory output, or epics/stories to fix these defects.

Reviewed clean factory worktree: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory`, HEAD `d3c6e1234b3dbf865e78179bc262cbbe90b1cc90` (repair c5f0f192 after previous c6717df7). Installed run-ui-epics SKILL.md and ui-epic-build.rhai match their source byte-for-byte.

Also read the installed backend run-epics skill and merge instructions, and parsed the completed shared-checkout `_bmad-output/planning-artifacts/epics-UI-2026-09-27.md`. This is a factory-readiness and backlog-routing review, not a full acceptance-criteria audit of all 36 stories.

## Verification actually performed

- Five factory helper test modules: **32 passed, 1 skipped**, 10.36 seconds. Command: `PYTHONPATH=tools` (PowerShell environment assignment), then `uv run --no-project --with pytest python -m pytest -q -o addopts='' tools/tests/test_ui_factory_evidence.py tools/tests/test_ui_factory_merge.py tools/tests/test_ui_factory_quality.py tools/tests/test_ui_factory_skylos.py tools/tests/test_ui_factory_validate.py`. Skylos executable coverage probe remains skipped; do not count it as verified scanner coverage.
- Direct CI helper probe: newest Skylos failure followed by older Skylos success returns **success**. A missing headSha also matches a supplied full SHA.
- Real backlog parsing: 8 epics, 36 stories; 66 has 8 stories. Bare planner selects **66–73**, despite frontmatter restricting the UI factory to 66. Selecting story 66.1 plans all eight stories of Epic 66.
- Validation with an explicitly empty completion set blocks all eight Epic 66 stories on FEAT-0058, with no required-field issues. This checks parser behavior; it does NOT establish whether FEAT-0058 is actually complete.
- Isolated temporary-directory quality-cache probe (command/toolchain results stubbed): first run without Reticle evidence fails; second run with a new yes-shaped input at the same identity still returns cached `Reticle evidence missing`. This is control-flow verification, not real Reticle proof.
- Source review of promotion, workflow metadata, evidence, dependency discovery, CI triggers and closure report.

No product factory launched. No GitHub push, merge, branch movement, installed-skill changes, active-state changes, source repairs or epic/story changes. No live GitHub or running-product positive proof claimed. Only review/continuity documents saved. The factory worktree remained clean.

## Remaining findings

### F1 — P1: Candidate CI cannot complete reliably, and the waiter can select a stale success

`tools/ui_factory/merge_gate.py:174–190` waits before promotion, but neither that function nor the installed normal workflow publishes a candidate ref first. Skylos and UI quality accept candidate tags; `.github/workflows/battery.yml:19–22` does not. QA Battery is nevertheless required. An ordinary new candidate therefore cannot obtain all required pre-promotion results through the documented route. The skill and `references/merge-gate.md` still instruct merge → destination push → CI wait, contradicting the code.

`tools/ui_factory/ci_wait.py:45–50` overwrites each workflow-name entry with later list entries. With newest-failure / older-success rows it returns success (reproduced). `:39` also accepts empty/prefix SHA matches rather than exact full identity. The branch parameter is unused.

**Close by:** publishing an immutable candidate before promotion, triggering every required workflow for that candidate, tracking the relevant workflow/run attempt deterministically, requiring exact repository/ref/full SHA identity and completed successful results, and reconciling prose with code. Missing, queued, failed, cancelled, timed-out or ambiguous results cannot promote. Add regression cases for stale success, reruns, absent SHA and missing required workflow. Do not require local Skylos on Windows to solve a GitHub waiting defect.

### F2 — P1: Real workflow still drops contract metadata and Reticle evidence

`.grok/skills/run-ui-epics/references/ui-epic-build.rhai:187–188` sends the story ID as `--story-hash`. It never supplies `--needs-backend` or `--reticle-evidence`. Its template lacks these inputs. The CLI now correctly rejects missing Reticle, so a compliant user-facing verification remains red through the normal route unless an agent invents undocumented extra steps. UI/backend contract tests are not selected from the missing metadata.

`quality.py:240–252` returns cached evidence before applying a new Reticle result. The isolated probe reproduced a failed proof remaining failed even after a replacement result is supplied. Conversely, cache identity does not bind proof identity or the command-profile definitions. `evidence.py:150–160` accepts the claimed verdict/tool strings without binding a retained tool result to the candidate and journey; rejecting only source='forced' is insufficient provenance validation.

**Close by:** carrying canonical story content hash, acceptance criteria/source references, required capabilities, backend-contract requirements and retained genuine Reticle act/assert result through dispatch, verification and merge. Bind evidence to candidate, running app and journey. Refresh proof independently of reusable command results. Unknown/no/missing/stale proof blocks. Test a real successful user-facing path as well as rejection paths.

### F3 — P1: Completed backlog lane and dependency rules are not enforced by the planner

Backlog lines 73–74 and 97–104 explicitly route **66 → UI / ui-integration**, **67–73 → backend / integration**. `story_parse.py` discards this routing. `schedule.py:45–64` selects all parsed epics and all stories in a selected epic. The bare plan reproduced 66–73; selecting only 66.1 reproduced all eight stories. `cli.py:95–106` computes a validation report but plans without its runnable set.

`cli.py:341–346` combines state with `gitops.py:98–112`, which treats IDs mentioned in recent current-checkout commit subjects as completed. A build commit is not proof of a dependency's accepted completion on its designated destination. Backend completion may also live on a different branch and be invisible to this lookup.

**Close by:** enforcing explicit lane ownership at validation, scheduling, dispatch and merge; respecting exact story selection; scheduling only eligible units; using destination-reachable accepted completion records with feature-to-story coverage. Preserve separate destinations and dependency waits. Do not rewrite the completed backlog to fit a parser. Transfer the approved planning snapshot into factory inputs deliberately: the UI factory worktree currently lacks this newly completed epic file; the shared checkout contains uncommitted planning work and must not be bulk-staged.

### F4 — P1: Promotion can bypass CI and can merge a different ref from the tested candidate

`cli.py:458` exposes `--no-wait-ci`; `merge_gate.py:174–176` bypasses CI for every non-product mode without restricting promotion to an isolated fixture repository. The destination can remain real ui-integration. At `merge_gate.py:206`, promotion merges the caller-supplied mutable branch, while quality and CI were measured against worktree HEAD. There is no branch/HEAD equality check or locked recheck of candidate identity. Destination checking uses cached origin refs rather than a fresh authoritative comparison at promotion. A mismatched or advanced branch can therefore differ from the reported SHA.

**Close by:** making production gates mandatory, isolating fixture tests from real destinations, binding promotion to the exact verified commit, and rechecking candidate and destination under the promotion lock. Refuse a dirty/unowned destination checkout; record partial local-merge/push failures distinctly. Test branch mismatch, candidate movement and destination movement.

### F5 — P1 for backend execution: The installed backend factory still has the reported Skylos gap

`C:/Users/Mubarak/.grok/skills/run-epics/SKILL.md:41–42` explicitly says Skylos is a post-push gate and not to block a local merge on it. Lines 115–118 and `references/merge-gate.md` merge, push, and remove the worktree with no awaited CI verdict. This is existing behavior, not a regression introduced by the UI repair, which intentionally left the backend skill alone. However, new Epics 67–73 are assigned to this lane, so the user's current concern is real.

**Close by:** applying the corrected candidate publication/wait/promotion/completion protocol to both factories, with lane-specific required checks. Backend retains Python checks, QA Battery and Skylos; UI adds frontend checks and required runtime evidence; genuinely mixed changes require all applicable profiles. Coordinate changes to a running backend factory at a safe boundary, without interrupting builders or replacing a skill beneath an active orchestrator. Do not enable the new backend batch using the old completion rule.

### F6 — P2: Claimed lifecycle closure is narrower than the required operational proof

`CLOSURE-R1-R8.md` honestly reports a live Grok **negative** Reticle control and synthetic helpers, but no positive end-to-end factory run. `lifecycle.py` calls ff_merge directly after checking separate helper facts; it does not execute the real positive promotion boundary. Passing helper tests therefore does not close the above integration defects.

**Close by:** running a bounded FACTORY-TEST lifecycle in an isolated test destination: normal dispatch, build, contract-profile selection, actual browser/Reticle proof, deliberate failure and repair, restart/resume, candidate CI wait and exact-commit promotion. Preserve the real workflow/run IDs and logs. If live GitHub cannot be exercised, report it explicitly as unverified and keep the production-readiness verdict incomplete. Simulated tests remain useful but must not become production authorization.

## Earlier fixes acknowledged

Frontend profile selection now includes user-facing intent; production host resolution no longer accepts the fixture fallback. Missing Reticle is rejected in fresh quality and merge evaluation. Exit-code zero survives deserialization, dirty-file contents contribute to cache identity, observed toolchain is recorded, Windows log names are sanitized, and ordinary pytest counts are captured. Occupied-destination merging and safe temporary-worktree handling improved. Named CI polling and simulated-result separation exist. State path and doctor honesty improved. These are genuine improvements; partial workflow wiring, routing and end-to-end proof remain open.

Prior R1/R2/R3/R4/R5/R6/R8 are therefore only partially closed by this packet; R7's setup-vs-runtime distinction is improved in the reviewed source. This is not a demand to redo already-correct work.

## Execution recommendation

One shared verification/promotion protocol, two explicit execution lanes. Preserve Epic 66 on ui-integration and 67–73 on integration. Share an accepted-dependency ledger so completed backend capabilities can unblock UI work without merging UI into backend. Select checks by story requirements plus actual changed surfaces; language alone does not establish runtime coverage. Later combine accepted branch tips in a dedicated deployment candidate and prove end-to-end operation there. The architecture/planning investment remains useful; the unresolved problem is factory control flow and proof.

This review does not require pausing planning agents. Repair of an actively used backend factory must be staged separately and activated at a safe boundary.
