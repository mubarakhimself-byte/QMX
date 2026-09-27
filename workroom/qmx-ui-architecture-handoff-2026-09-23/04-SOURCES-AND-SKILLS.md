# Source map and staged skill use

## Required source reading

Read the current direction first; the evidence below contains historical proposals and rejected work. Summaries are navigation aids, not substitutes for the underlying dictation, images and transcripts.

| Source | Packet location | Why/when to use |
|---|---|---|
| Current visible conversation | [session export](evidence/session/session-visible-messages.md), [audit](evidence/session/handoff-working/session-audit.md) | All 15 visible turns available at capture. Includes current steering and prior corrections. The active turn is partial after the latest request. |
| Latest captured Excalidraw | [source](evidence/session/live-research/board-current/qmx-ui-storyboard.source.md), [text](evidence/session/live-research/board-current/scene-text.json), [scene](evidence/session/live-research/board-current/scene.json), [dictation audit](evidence/session/live-research/dictation-audit.md) | 141 live elements, 20 text elements, 23 arrows. Read full bottom text `JHZj5SdT`, not just brief labels. Afternoon snapshot supersedes the earlier morning copy. |
| Original visual assets | [10 source images](evidence/session/evidence/source-images/), [asset map](evidence/session/live-research/board-current/attachments.json) | All unique images behind 11 placements. OpenBB/VS Code govern app proportions/layout; inspect other images for their intended roles. |
| Layout correction | [fidelity reset](evidence/session/layout-fidelity-reset.md) | Shows the precise difference between source layout and rejected study 03. Its old broad BMAD wording is narrowed by current direction: UX excluded, architecture/epics allowed. |
| Original short video | [terminal-preview.mp4](evidence/terminal-preview.mp4), [observations](evidence/session/video-reference.md) | Original roughly 11-second reference plus sampled frames in the session. Report distinguishes samples from inferred behavior. |
| Origin brainstorm | [full transcript](evidence/session/evidence/origin-context/Explore-Node-Editor-Architecture.md), [reading report](evidence/session/evidence/origin-context/origin-reading.md) | Capability-building vision, typed nodes, app/workflow distinctions, app-use/authoring and experimentation. Original attached screenshot is in `images/image-001.png` alongside the transcript. |
| Historical Grok/Codex architecture | [full transcript](evidence/session/evidence/origin-context/grok-architecture-mimi0apps.txt), [reading report](evidence/session/evidence/origin-context/grok-reading.md) | Earlier architecture/review exchanges and user corrections. It is not today's implementation state. Original source path `architecture-mimi0apps` was a file. |
| Original reference research | [grounding summary](evidence/session/live-research/grounding-summary.md), [saved captures](evidence/session/live-research/screenshots/) | All seven storyboard-linked references plus OpenBB were investigated; 18 saved captures and source-specific reports record access limits. LSE UI is now explicitly rejected as the layout model. |
| Latest links | [final reference pass](evidence/session/live-research/final-reference-pass.md) | Svelte Flow showcase, n8n iteration and shadcn-svelte chart/code interactions; license checks; clear observation limits. No new screenshots were saved in that pass. |
| User's Codex screenshots | [five images and manifest](evidence/session/experience-v03/references/) | Preview tabs, context panel, work-area launcher and conversation navigation. The expanded plus menu was not captured or operated. |
| Existing BDD | [inventory](evidence/session/handoff-working/bdd-inventory.md), [portable sources](evidence/bdd/README.md) | Five canonical feature files, 85 IDs and supporting catalog/context. Specification, not executable acceptance proof. |
| Current nearby documentation | [snapshot note](evidence/current-context/README.md) | Includes a narrow current headless/optional-copilot scenario snapshot; shows this is already architectural subject matter. Refresh from the repository before proposing gaps. |
| Runtime proposals | [interaction draft](evidence/session/interaction-runtime-draft.md) | XR-01–08 are useful proposals, not accepted contracts. Current direction overrides historical framework/tool-choice statements. |

Source hashes and original paths remain in each provenance file. [packet-manifest.json](packet-manifest.json) fingerprints the delivered files; [repository-snapshot.json](repository-snapshot.json) records the inspected repository state. Local original paths in old reports are provenance, not required portable dependencies.

## Historical material

`evidence/session/experience-v01`, `experience-v02` and `experience-v03` retain the assistant's earlier artifacts. Inspect them only to resolve a historical claim or understand a rejection. The original source images and user corrections supply the reconstruction baseline. Old BMAD UX archives are not included or authorized as a design baseline.

The session snapshot also preserves decisions, the work log and a Wayfinder tracker. Unfinished tickets are not implementation acceptance. The external code repository and complete currently evolving core architecture are intentionally not copied as though frozen; Grok must establish its current baseline.

## Reference index for targeted further research

- [Svelte Flow showcase](https://svelteflow.dev/showcase): graph-tool interaction leads; [Svelte Flow](https://svelteflow.dev/) for implementation documentation.
- [shadcn-svelte charts](https://shadcn-svelte.com/charts/bar#charts): working visual/component baseline; [Svelte TypeScript](https://svelte.dev/docs/svelte/typescript) for language support.
- [n8n AI agents](https://n8n.io/ai-agents/) and [data mapping](https://docs.n8n.io/data/data-mapping/data-mapping-ui/): graph/node/input/output and run-inspection mental models. Reference does not select n8n's runtime.
- [OpenBB Workspace](https://openbb.co/products/workspace/), [QuantX](https://quantx.es/signup#das), [Xynth](https://xynth.com/), [Prime Terminal](https://prime-terminal.com/), [Minara](https://minara.ai/app/strategy-studio): already researched in the included reports; inspect further only for a concrete unresolved question.
- [LSE ML](https://www.londonstrategicedge.com/machine-learning-studio/): capability vocabulary, not approved layout.
- [json-render renderers](https://json-render.dev/docs/renderers), [MCP Apps Svelte example](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte), [Tauri process model](https://v2.tauri.app/concept/process-model/): integration research leads; none proves QMX compatibility.

## Skills: use at the stage that needs them

The [skill inspection report](evidence/session/handoff-working/skill-selection.md) describes dependencies and prerequisites. No listed workflow was run while preparing this handoff. Local paths below are discovery pointers on this machine, not portable installed skills.

| Stage | Selected guidance | Local SKILL.md |
|---|---|---|
| Grok architecture now | BMAD architecture; deep-recon/research methods for unresolved facts and alternatives | `C:/Users/Mubarak/Desktop/QMX/.agents/skills/bmad-architecture/SKILL.md`; `C:/Users/Mubarak/Desktop/QMX/.agents/skills/bmad-deep-recon/SKILL.md` |
| Return review here | Focused architecture validation; codebase-design where module/contract boundaries need examination | `C:/Users/Mubarak/Desktop/QMX/.agents/skills/bmad-architecture/SKILL.md`; `C:/Users/Mubarak/.agents/skills/codebase-design/SKILL.md` |
| Fresh documentation session | Documentation Factory with the reviewed architecture, this design packet, source repository and exported Grok session | `C:/Users/Mubarak/.agents/skills/documentation-factory/SKILL.md` |
| Decomposition afterwards | BMAD epics/stories with reconciled requirements/architecture and UI contracts | `C:/Users/Mubarak/Desktop/QMX/.agents/skills/bmad-create-epics-and-stories/SKILL.md` |
| Implementation later | Appropriate tests, agentic-tdd for observable journeys, install-and-verify/Reticle for running UI | `C:/Users/Mubarak/.agents/skills/agentic-tdd/SKILL.md`; `C:/Users/Mubarak/.agents/skills/install-and-verify/SKILL.md` |

Keep installed skill directories intact; architecture/epics/Documentation Factory use companion scripts, templates and references. Copying only SKILL.md would create an incomplete workflow. If the Grok environment lacks a skill, say so and use the self-contained prompt instead of inventing successful invocation. BMAD UX and Figma are excluded. New paid tools or component subscriptions are not needed for this stage.
