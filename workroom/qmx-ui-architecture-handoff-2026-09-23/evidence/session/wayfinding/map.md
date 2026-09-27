# QMX experience design map

## Destination
Transferable, source-grounded UI designs and behavior specifications for QMX, with a reusable design system and contribution rules. Grok implements later. Preserve the full storyboard, not just chat.

## Notes
- Canonical evidence and decisions: [workroom entry](../README.md).
- User authorizes design drafts and prototypes within this session. Execution of those drafts is in scope; production/backend implementation is not.
- Adapt Wayfinder to existing grounding: no new discovery questionnaire. Ask only when evidence cannot resolve a consequential choice. A draft remains a proposal until reviewed.
- Open work is in `issues/`; this map does not duplicate ticket status. Scan those files on resume.
- This scratch tracker is copied into portable deliveries; the workroom remains the lasting session record.

## Decisions so far
- D-001/D-003/D-005/D-007: fresh UX, one session, original dictation and observed references are the grounding.
- D-012/D-015: preserve broad layout; platform destinations exist independently of opened apps.
- D-017: shared agent capability, separately scoped sessions, histories restored rather than merged.
- D-018/D-019: UI/specifications now; include attachments and user questions. Backend coordination later.
- D-021–D-025: study 02 visual treatment rejected; aesthetics deferred. Revise attachment semantics, explore Codex plugin logic and preview/nav references, and show mini-app plus Library now. BMAD UX guidance checked; no formal finalization or new theme.
- D-026–D-028 supersede the latest draft direction: study 03 rejected for layout/source-fidelity failure; stop BMAD in this UI session. Read `workroom/ui-reset-2026-09-23/layout-fidelity-reset.md`. Main-copilot and mini-app interiors differ. Reconstruct the source before inventing another generic shell. No ticket resolved.

## Not yet specified
Component behavior in practice; visual foundations; expanded-widget return/placement; Library identity and locate/save; composition versus workflow authoring; settings/runtime feedback; responsive density; contribution contracts reconciled with updated backend.

## Out of scope
Production code, backend/SDK architecture changes, selecting a final rendering stack, trading actions, reviving archived UX, declaring the packet final for Grok.


Checkpoint copy, 2026-09-23. In the active repository, the canonical tracker is `.scratch/qmx-design-wayfinding/`.
