# Grok handoff plan and backend questions

Status: design discussion packet, not implementation-ready. The user will use Grok to code and BMAD architecture later. Codex has not invoked that architecture skill or selected a frontend framework.

User's later clarification: Grok is already expanding core architecture. The handoff contents and sequence below are provisional; reconcile them with that work rather than requiring Grok to follow this outline. Read the [early copilot/platform coordination note](copilot-and-platform-clarification.md) first. Current backend capabilities must be checked again when integration is planned.

## What Grok should receive

The eventual handoff is a linked, versioned packet: accepted experience decisions; QMX screen/storyboard references; interaction/state specifications; a design-system component catalogue; app/widget/workflow contracts; backend mapping; and executable acceptance scenarios. The conversation transcript and competitor screenshots are supporting evidence, not a replacement for these specifications.

For now, provide this session folder locally so relative links resolve. [START-HERE.md](START-HERE.md) is the read entry. [conversation-evidence.md](conversation-evidence.md) is a bounded snapshot through the design kickoff, with historical/superseded statements retained. [Visual evidence](../live-research/visual-evidence-index.md) records capture types and limits. Nothing has been uploaded or sent to Grok by this task.

For a portable archive later, include the whole session folder, relative assets and hashes, the final transcript snapshot and the specific repository/commit references. Verify that linked files resolve after moving the packet. Do not rely on this machine's absolute paths as the only references.

## Existing source foundations versus questions

Code inventory: integration commit `34c148be404a375cbfd79fd4ce6997452e4f1d20`, inspected in `.worktrees/integration-inspect`. It has not been refreshed against Grok's concurrent observability/logging work. See [full source paths and limits](../backend-grounding.md). Reinspect current code before answering a gap.

| Question ID | Experience need | Inspected foundation | What later architecture must establish |
|---|---|---|---|
| B-01 | Home aggregates active work | Mission/taskgraph projections and wire queries | Available activity/freshness aggregation, subscriptions and identity links; avoid assuming a new endpoint |
| B-02 | Switch and restore app views | Durable product sessions; tabs are chrome only | Owner/storage for workspace layout and view state, reconnect policy, restoration of unavailable objects |
| B-03 | Render widgets and app pages | Explicit deferred UI contract and widget-contribution refusal | Contribution schema, renderer registry, compact/detail contracts, inputs/actions and error boundaries |
| B-04 | Scope a copilot and attach objects | Wire scopes, app-use/authoring profiles, principal/grant checks | Mapping between UI context and backend references without granting extra authority |
| B-05 | Locate/save/reuse through Library | Knowledge/artifact/contribution discovery and domain-owned records | Correct owners for each displayed type; definition/instance/result distinctions; supported writes |
| B-06 | Build workflows through graph/code | Graph Templates, Skills, Routines, compiler/dispatcher | Editable graph representation, validation, custom-code boundaries and any compiler integration needed |
| B-07 | Preview and update apps | App-use change-request **fixture**, not CT-40 production operations | Production lifecycle, concurrency checks, permissions, activation and recovery; reuse-or-extension decision |
| B-08 | Keep agent-generated apps consistent | No implemented UI SDK found in the inspected snapshot | Versioned app-building contract, allowed components/actions, compatibility, example fixtures and checks |
| B-09 | Show useful status/logs | Existing ledger/trace reads; new observability work is concurrent | Latest supported observability surface, correlation IDs, redaction/access and user-facing status meanings |

These are questions, not nine backend features automatically scheduled for development. A response should classify each as existing/reuse, adapter needed, enhancement needed, deferred or still unknown, with current source evidence.

## How experience becomes implementation

1. **Agree the experience.** Review scene cards and visual alternatives; record decisions rather than treating every draft as binding.
2. **Specify the shared language.** Finalize terminology, object identities, navigation/lifetimes and common states. Develop the design system and app contribution contract together.
3. **Architecture pass with Grok/BMAD.** Use current code to resolve B-01–B-09 and select technology. Preserve the existing backend boundaries and concurrent work.
4. **Create implementation slices.** Each slice names prerequisite contracts, affected scenes, visual references, required states and acceptance checks. Choose the sequence after architecture and user priorities; the storyboard is not a forced research-to-trading wizard.
5. **Implement and demonstrate.** Grok works in an isolated checkout from an agreed current base. It returns changed files, scenario results, actual UI screenshots, supported Reticle verdicts, remaining gaps and a refreshed decision record.

## Initial observable scenarios to refine

- AC-01 / S-01,S-03: opened apps and running jobs remain distinct in labels and behavior.
- AC-02 / S-03,S-04: switching away and back retains the app's selected page/detail in the agreed persistence scope.
- AC-03 / S-04: expansion preserves object/run/snapshot identity; closing detail returns without stopping a job.
- AC-04 / S-05: context attachment is visible/removable and does not widen permissions.
- AC-05 / S-06: locate selects an existing library object; transient results follow an explicit save path.
- AC-06 / S-07: a draft can be inspected and previewed without changing the active version; invalid drafts explain errors.
- AC-07 / S-08: an incompatible upgrade reports the conflict and follows the agreed recovery path.
- AC-08 / all: keyboard/focus, loading/error/stale/disconnected/denied states work for the delivered scope.

These are draft acceptance intentions. They still need precise fixture setup and expected outcomes before becoming implementation tests. The conversation's inline model demonstrates selected navigation ideas only; it is not backend validation or a Reticle verification of QMX.
