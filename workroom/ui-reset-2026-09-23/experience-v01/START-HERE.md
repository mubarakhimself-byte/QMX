# QMX experience design v0.1

Status: discussion draft, 2026-09-23. The user accepted experience-first work and the broad six-area direction. Individual behaviors below remain proposals until recorded as accepted in the decision log. This folder is a design packet for the user and eventual Grok implementation, not an instruction to begin coding.

The user has now accepted the shared copilot/multiple-session direction. The [next UI pass](main-workspace-next-pass.md) has been drafted as [portable study 02](../experience-v02/README.md), covering main-workspace attachments, references, questions and previews. Backend/SDK implementation remains with Grok and has not been re-audited here. Resume the session from [CURRENT.md](../CURRENT.md).

**Latest clarification:** read [Copilot and extensible platform](copilot-and-platform-clarification.md) for the proposed shared agent capability, optional app panels, json-render/MCP Apps roles and platform/app dependencies. Grok's core architecture is changing now; the backend inventory and final handoff structure are not frozen.

## Working agreement

- Codex helps develop the experience, compare options, document decisions and preserve evidence. Grok will implement. The user intends to use BMAD architecture later; it has not been invoked for this packet.
- The supplied layout is a strong starting point. The user's “about 70%” is a qualitative assessment, not a measured completion score. Preserve its rail/work-area/copilot relationship while testing behavior.
- Work in this single ongoing task. Prefer lower-end agents for bounded evidence/review. Exclude archived BMAD UI/UX designs.
- Show a small, concrete design for discussion, update the decision record, then deepen the agreed area. Do not silently ratify the whole packet from permission to draft it.

## Read in this order

1. [Current decisions](../decisions.md): accepted direction, proposals and superseded ideas.
2. [Experience storyboard](experience-storyboard.md): screens, transitions, context and failure states.
3. [Design system and app-building rules](design-system-and-authoring.md): how consistent interfaces and future agent-created apps could work.
4. [Backend questions and implementation handoff](grok-handoff.md): existing foundations, open contracts and the later implementation sequence.
5. [Visual evidence index](../live-research/visual-evidence-index.md), [original text audit](../live-research/dictation-audit.md), and [backend inventory](../backend-grounding.md) when checking a claim.

The [conversation snapshot](conversation-evidence.md) preserves the reasoning and the user's actual corrections through this kickoff. It includes superseded assistant suggestions; it must not override the current decisions. Future handoffs should refresh this snapshot and state the capture boundary.

## Packet status

| Available now | Still to develop together |
|---|---|
| Complete experience map and eight proposed scene descriptions | Agreed interaction behavior and priorities |
| Saved source screenshots, text, local video evidence and research limitations | QMX screen designs and responsive behavior |
| App-building and change-management proposal | Versioned schemas, component implementations and a tested SDK |
| Backend questions tied to inspected code | Current backend review and BMAD architecture decisions |
| Local conversation evidence snapshot | Final implementation slices with accepted checks |

An inline interaction model accompanies this draft in the conversation. It uses illustrative Research and ML workspaces to explain navigation. Those labels do not settle the default app roster, and its visual styling does not settle the QMX design system.

The original inline fragment remains in the task's visualization storage. A [standalone export](whole-experience.html) is now in this folder, with local style primitives replacing its host styling dependency. It opens without Codex; no backend connection or persistence is required. The original fragment was browser-checked as documented below; the standalone export's styling is not visually verified. This is a portable working draft, not an agreed final Grok bundle.

A [saved capture of the draft preview](visuals/authoring-preview-1024.png) is included for visual context. It is our proposed QMX interaction model, not a competitor screenshot or an implemented QMX screen. [Review notes](review-notes.md) record checks and limits.

## Change discipline

Every substantive revision should name the affected scene/rule, source or decision, status, backend implication and observable acceptance check. A future agent starts here, reads only the linked material relevant to its change, and records what it changed. It must check the actual backend revision before treating this September inventory as current.
