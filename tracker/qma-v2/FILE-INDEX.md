# File index: agent-system planning files (2026-10-12)

What each planning file is for now that `tracker/qma-v2/PRD.md` exists. Nothing has been moved; this is a proposal for the cleanup.

**Verdicts**
- **CURRENT INPUT:** the architecture needs it tonight, next to the PRD.
- **REFERENCE:** keep where it is; rarely needed (traceability, later features, background).
- **SUPERSEDED:** should move to an archive folder, stamped, never deleted (FR-145).

**Totals:** 65 files. CURRENT INPUT 8 · REFERENCE 23 · SUPERSEDED 34.

---

## 1. `tracker/agent-system/` (top level)

| File | Verdict | Why |
|---|---|---|
| `map.md` | SUPERSEDED | Wayfinder destination and positions predate the two-SDK pivot (LangGraph, "Claude Code" as worker); its carried rules are now PRD §3 |
| `glossary.md` | SUPERSEDED | Says "Claude Code, never Agent SDK" and "QMX engine = LangGraph"; replaced by PRD §6 (conflict K-03) |
| `workflow.md` | SUPERSEDED | Skill order ships into `rebuild/base` and says "BMAD not needed"; branching is now integration → staging → main and BMAD PRD/architecture applies (K-20) |
| `backlog.md` | REFERENCE | Holds the out-of-scope items (Library v2, WF1/WF2, QMB review, post-P16 check) that PRD §2.2 names as seams |

## 2. `tracker/agent-system/tickets/`

| File | Verdict | Why |
|---|---|---|
| `01-agent-sdk-capability-audit.md` | REFERENCE | Resolved research ticket; its findings live in `research/01-…` |
| `02-harness-choice.md` | SUPERSEDED | Harness question settled by C-01 (two SDK engines); its lines on API keys, Codex and profiles are reversed (00 §4) |
| `03-organogram-and-errands.md` | SUPERSEDED | Questions now answered as FR-001-FR-019 and Q4 |
| `04-baseline-tool-surface.md` | SUPERSEDED | Now FR-132-FR-138 and FR-103 |
| `05-usage-limits-telemetry.md` | REFERENCE | Resolved; its usage-ledger decision feeds FR-048/FR-049 |
| `06-accounts-and-router.md` | SUPERSEDED | "One model per thread" and the proxy risk call are replaced by FR-038-FR-045 and FR-099 |
| `07-approvals-and-hooks.md` | SUPERSEDED | Now FR-102-FR-109 and Q1 |
| `08-memory-and-learning.md` | SUPERSEDED | Now FR-091-FR-095 and FR-142 |
| `09-long-running-and-server-agents.md` | SUPERSEDED | Assumes a Contabo box and a light QMX sandbox; now FR-110-FR-118 on rented compute |
| `10-context-caching-compaction.md` | SUPERSEDED | Now FR-096-FR-101 and NFR-004 |
| `11-chat-and-event-protocol.md` | SUPERSEDED | Candidates include LangGraph streaming; now FR-126-FR-131 |
| `12-ctrader-screen-automation-spike.md` | REFERENCE | A spike not yet run; it is FR-139's acceptance check (LATER) |
| `13-agent-folder-layout.md` | SUPERSEDED | Agent-as-a-folder is now the plugin layout (FR-030, A-16) |
| `14-firecrawl-alexandria.md` | REFERENCE | Research not yet done; needed for FR-135 (NEXT) |
| `15-skills-and-system-prompts.md` | SUPERSEDED | Now FR-035-FR-037, FR-096 and A-05 |
| `16-shipping-plan.md` | SUPERSEDED | Targets `rebuild/base` and the old ticket chain; the shipping plan now follows the architecture |
| `17-lab-workflow-engine.md` | SUPERSEDED | Built around the P10 LangGraph compiler; now FR-052-FR-069 on QMX's own runner |
| `18-building-and-reach.md` | SUPERSEDED | Now FR-056, FR-072, FR-103, FR-132 |

## 3. `tracker/agent-system/research/`

| File | Verdict | Why |
|---|---|---|
| `00-session-ledger-2026-10-12.md` | REFERENCE | Lowest-authority source; absorbed into 26 and the PRD; keep for message citations (`L[n]`) and Claude's process lessons |
| `01-agent-sdk-capability-audit.md` | CURRENT INPUT | Claude Agent SDK facts the Claude engine is built on: process per session, RAM, isolation, hooks |
| `02-how-current-agent-runtime.md` | SUPERSEDED | Its B/C options are dead and 24 rebuilds and corrects its code survey |
| `05-usage-limits-telemetry.md` | CURRENT INPUT | Documented usage sources and the ledger design behind FR-048-FR-050 |
| `19-two-sdk-study.md` | CURRENT INPUT | Capability facts and the `Engine` method mapping (§10-12); ignore its "keep LangGraph" advice (K-04) |
| `20-qma-v2-direction.md` | CURRENT INPUT | §2 page facts (dynamic workflows, system prompts) and §4 corrections; §1-3 positions are absorbed or overridden |
| `21-miniapps-and-workflows-seeds.md` | CURRENT INPUT | The 30-item complexity list (NFR-026) and the mini-app/workflow definitions |
| `22-cookbooks-and-templates.md` | CURRENT INPUT | Template catalogue (FR-066), system-prompt rules (A-05), cookbook refinements; facts only |
| `24-how-why-integration-surface.md` | CURRENT INPUT | Code facts: what to keep, rewrap, replace; the 16 risks the build must not miss |
| `26-requirements-from-today.md` | REFERENCE | Merged into the PRD; keep as the source of FR-T IDs and message citations |
| `27-requirements-from-audit-session.md` | REFERENCE | Merged into the PRD; keep as the source of FR-A IDs and the binding/superseded decision tables |

## 4. `rebuild/research/2026-10-12-agent-system/`

| File | Verdict | Why |
|---|---|---|
| `INDEX.md` | REFERENCE | Index of this research pass; update it when files move |
| `qmx-internal.md` | REFERENCE | UI screen by screen and the era contradictions; useful for event/UI shape, not core to tonight |
| `langchain-stack.md` | SUPERSEDED | LangChain, LangGraph and Deep Agents are out (C-06); port facts are in 24 and 27 §4 |
| `harnesses.md` | REFERENCE | Hermes, Codex, Eve, computer use; needed for NEXT items (FR-136, FR-137, FR-070) |
| `memory.md` | REFERENCE | Memory providers and bake-off plan for FR-092/FR-095 (NEXT/LATER) |
| `models-routing.md` | CURRENT INPUT | Vendor terms per account type (SIWC, Claude plan) and router facts; its per-role defaults on API keys are invalid for Claude/GPT |
| `cookbooks.md` | REFERENCE | Morning cookbook pass; 22 re-read the sources in full and supersedes it where they differ |
| `notes/cookbooks-index.md` | REFERENCE | One line per cookbook item; a lookup list |
| `notes/deepagents-core.md` | SUPERSEDED | Deep Agents is out |
| `notes/deepagents-extensions.md` | SUPERSEDED | Deep Agents is out |
| `notes/langchain-langgraph-core.md` | SUPERSEDED | LangChain/LangGraph are out |
| `notes/models/langchain-model-mechanics.md` | SUPERSEDED | LangChain model plumbing; not used by either SDK engine |
| `notes/models/cliproxyapi-notes.md` | SUPERSEDED | CLIProxy is replaced by the router (C-07); one SIWC-terms fact is repeated in `subscription-terms.md` |
| `notes/models/subscription-terms.md` | REFERENCE | Primary-source terms for Claude plans and SIWC behind A-01, A-02 and A-20; summarised in `models-routing.md` |
| `notes/models/pricing-2026-10-12.md` | REFERENCE | Dated price rows for key-based providers |
| `notes/models/model-ui-patterns.md` | REFERENCE | Model-picker patterns for FR-047 |
| `notes/harnesses/codex-notes.md` | REFERENCE | Codex tools and app-server shape; Codex is not a harness here, its UI ideas still help |
| `notes/harnesses/computer-use-notes.md` | REFERENCE | Input to A-11 (OpenCUA vs cua-driver) |
| `notes/harnesses/cordis-architecture.md` | REFERENCE | Lego-style harness reference |
| `notes/harnesses/eve-notes.md` | REFERENCE | Agent-as-a-folder reference for A-16 |
| `notes/harnesses/hermes-notes-core.md` | REFERENCE | Hermes memory, cron, provider resolution; reference for FR-070, FR-092 |
| `notes/harnesses/hermes-notes-extensions.md` | REFERENCE | Hermes plugins and self-improvement; reference for FR-142 |
| `notes/cookbook-batches/batch00.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch03.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch04.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch05.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch07.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch08.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch09.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch10.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch11.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |
| `notes/cookbook-batches/batch12.md` | SUPERSEDED | Working extract, consumed by `cookbooks.md` and 22 |

---

## 5. Suggested archive move (not done)

Move every SUPERSEDED file to `tracker/agent-system/archive/` (or `rebuild/research/2026-10-12-agent-system/archive/` for the research pass), adding a first line `SUPERSEDED 2026-10-12 by tracker/qma-v2/PRD.md`. Keep relative paths inside the archive so old citations still resolve. Needs the operator's go (FR-145).

**What the architect reads tonight:** `tracker/qma-v2/PRD.md`, then the eight CURRENT INPUT files above.
