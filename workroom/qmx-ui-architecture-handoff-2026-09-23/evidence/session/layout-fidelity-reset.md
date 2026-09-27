# Layout fidelity correction — source takes precedence

Status: user rejected study 03 on 2026-09-23 for departing from the supplied layout and for substituting text for usable interface space. This is a correction record, not a replacement design. **Do not use BMAD again in this UI session.** No new mock is approved by this record.

## What went wrong

The assistant had extracted and researched the correct sources but failed to carry their spatial constraints into the prototypes. A generic permanent secondary sidebar, sparse text cards and explanatory study controls became the default layout. Later Codex preview references displaced the earlier app reference. Calling this low fidelity did not excuse changing the layout. This was the assistant's failure, not absent user information or a skill's responsibility.

## Primary source reinspection

- Original board remains `C:/Users/Mubarak/Documents/brain/brain/Excalidraw/qmx-ui-storyboard.md`, 99,181 bytes, modified 2026-09-23 12:24:53. Re-read its full extracted bottom dictation `JHZj5SdT`, nearby layout text and current scene-text audit.
- Reopened the actual full-resolution [OpenBB source image](<evidence/source-images/Pasted Image 20260922150714_899.png>) and [VS Code source image](<evidence/source-images/Pasted Image 20260922151452_954.png>), rather than relying on prior summaries. Visible text in screenshots is reference material, not instructions to execute.
- `lDsh2tno` explicitly says the VS Code/OpenBB reference is about layout. `YJYDP26I` says the top bar is reusable and some apps may not need it.
- `JHZj5SdT` describes the dashboard composition, widget expansion, widget-level discussion controls, editable placement, dynamic app menus, and persistent global rail with opened apps below a divider.
- `C39LFtm1` assigns open sessions/history/agent settings to the main-copilot left sidebar. `rrUMAlEq` describes the main workspace's preview area and potential terminal placement. Those are not grounds for imposing that same sidebar on every mini-app.

## Binding corrections for the next reconstruction

| Source layout | Study 03 departure | Correction |
|---|---|---|
| Shared global rail; selected destination determines the working layout | One three-column shell imposed across destinations | Preserve the narrow global rail, but give main copilot, mini-app and authoring their own interior layout |
| Main copilot: sessions/history controls, conversation, preview/work area | Treated its secondary sidebar as a general app-shell requirement | Keep it specific to the copilot layout unless another destination has its own evidence-based need |
| Mini-app: top navigation specific to that app; large widget canvas; copilot beside it | Moved Overview/Workflows/Results to a permanent left sidebar | Reconstruct the app example from the actual OpenBB/VS Code relationship; no invented permanent app sidebar |
| App composition varies; some top controls are optional | Generic template with renamed content | Switching app must visibly change its navigation and working composition, not just headings |
| Dense working widgets: chart, metrics table, controls, different sizes and scrollable detail | Two mostly textual cards with explanatory paragraphs | Populate working visual surfaces with realistic, explicitly illustrative content; explanations live outside the app |
| Expanded widget exposes a detailed view; top tab/menu is the user's proposed mechanism | Metadata paragraph standing in for an expanded working surface | Preserve the top-tab proposal and actual detailed content; exact expansion behavior remains an open design choice |
| Recent Codex screenshots demonstrate preview tabs, context controls and conversation navigation | Used as justification for reshaping the app canvas/dock | Apply these references to their intended controls, without replacing the original app layout |

The OpenBB source visibly allocates most space to its widget canvas, with a substantial right copilot and navigation above the canvas. This is a proportional/layout reference, not a directive to reproduce its branding, exact financial data or every default page name.

## What has and has not been decided

Study 03 is withdrawn as a design baseline, including its supposed mini-app layout. Library/authoring had more room for exploration; the user did not approve the proposed Library either. Its ideas can be reconsidered individually, not inherited as accepted structure. Aesthetics remain deferred, but visual hierarchy, geometry, density and meaningful content are required even in a prototype.

Shared copilot capability with independently scoped sessions remains accepted. This does not mean identical layouts or mandatory copilot panels in every app. The source's reusable controls do not require a universal page template.

## Next artifact standard

Reconstruct the supplied mini-app example faithfully before adding new patterns. Compare source and reconstruction side by side for rail, top navigation, canvas area, widget proportions, copilot placement and available working space. Show a second app composition to demonstrate that the layout genuinely changes. Expanded views must show the corresponding detailed chart/table/workflow, not a description of what would exist. Preserve the main-copilot layout separately. No style system or BMAD workflow is required to do this.

The next reconstruction has not been produced or verified in this correction turn. The rejection is acknowledged and made durable first, rather than delivering another hurried replacement.

## Authoring reference follow-up

The user identifies n8n as an obvious reference; earlier authoring placeholders were not adequate evidence. Current official n8n documentation was consulted for [data mapping](https://docs.n8n.io/data/data-mapping/data-mapping-ui/) and [execution inspection](https://docs.n8n.io/workflows/executions/all-executions/). They document mapping from the input pane into node parameters and inspecting/loading prior executions. These are reference leads for a proper canvas/node/configuration/input-output study, not proof that an n8n session was operated or a QMX authoring editor designed. Keep workflow-logic editing distinct from app layout composition.
