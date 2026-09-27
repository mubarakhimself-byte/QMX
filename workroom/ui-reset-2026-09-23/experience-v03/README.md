# App and Library study 03

**WITHDRAWN / REJECTED BY USER.** The layout departs materially from the original storyboard and its OpenBB/VS Code references. It is retained as history, not a baseline to refine or implement. Read [layout-fidelity-reset.md](../layout-fidelity-reset.md). BMAD is excluded from the rest of this UI session. The older draft description below is historical.

**Working interaction proposal, 2026-09-23. Aesthetics deferred by the user.** Open [app-and-library.html](app-and-library.html) directly in a browser. Single file, no installation or service dependencies. All contents/state are simulated and reset on reload.

## What changed in direction
The user rejects study 02's visual treatment and attachment picker, likes the idea of attached-item chips, finds the question pattern workable, and accepts the preview concept while preferring Codex's tabbed work area. Broad layout came from the user's original storyboard. Study 02 is historical, not a visual baseline. Color, typography, spacing and component-system selection remain open.

The five new screenshots are preserved exactly in [references/](references/) with hashes and observations in [manifest.json](references/manifest.json). They show a tabbed work area, a panel launcher, source/task context, image attachments and a red-circled conversation navigator. **None shows the expanded plus menu.** Native Codex UI control is disabled in the available computer-use tool. Screenshot observations and local plugin research are not live menu verification.

## Try the model
1. **App overview:** Research desk has its own pages, two widgets and an optional copilot. Expand Data coverage, discuss a resource, close the detail and return. These controls model behavior, not backend operations.
2. **Browse Library:** filter/search Apps, Widgets, Workflows, Datasets, Results, Tools or Files. Select an item to inspect its source/version/availability and intended meaning. This unified catalogue is proposed; final taxonomy is not settled.
3. **Dataset → conversation:** inspect Snapshot D3, then choose Reference in Research copilot. The chip carries dataset identity/version. No entire data table is implicitly sent.
4. **App vs tools:** compare Research desk with Research tools. Open app restores its workspace. Reference app contributes its identity/declared context. Select tools adds a capability chip without installing, connecting, granting access or invoking anything.
5. **Plus menu:** use + in the Research copilot. It separates Files & images, Library references, and Tools & plugins. This category structure is a QMX proposal; it is not a recreation of an observed Codex menu.
6. **Tabbed work area:** preview Research review. Switch between its object details and document. Dock below or beside the work on wide screens; side layout stacks on narrower screens. Close the work area without clearing app/conversation state.

The wireframe intentionally represents just one example app; the page names and catalogue entries do not set the required default app roster. Home, Main copilot and Authoring rail labels retain the overall layout but do not navigate in this study.

## Documents
- [Interaction rules](interaction-rules.md): what each attachment/action means, library boundaries and preview proposal.
- [Plugin reference](plugin-reference.md): locally observed packaging facts separated from inference.
- [Design-system status](design-system-status.md): BMAD UX findings and division of later design/implementation work.
- [Review notes](review-notes.md): source checks, known gaps and manual scenarios. No live browser/Reticle verification claimed.

This is a design checkpoint. We still need real plus-menu evidence, detailed Library taxonomy/search/save/version rules, cross-app tool behavior, authoring, long-conversation navigation, component-system selection and later reconciliation with Grok's updated SDK. User corrections are stored in the main decision log; a working prototype does not ratify them as requirements.
