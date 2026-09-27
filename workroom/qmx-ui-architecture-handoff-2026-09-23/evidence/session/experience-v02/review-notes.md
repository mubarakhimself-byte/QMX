# Review notes — study 02

2026-09-23. **Design proposal; real-browser visual and interaction checks outstanding.**

## Completed
- Source review against the five-state main-workspace brief and original shell/agent-layout evidence.
- Independent lower-end agent review against component contracts. Three findings addressed in source: question focus transfer, visible unavailable-source recovery limits, and explicit sample source/snapshot labels in sent references and preview.
- Extracted inline JavaScript from both self-contained studies; Node `--check` returned exit 0 for each. This establishes syntax only.
- Draft tokens exported directly from CSS custom properties. Companion JSON uses a study-specific structure, not a selected standard.
- Portable checkpoint: 95 files, including a SHA-256 manifest. ZIP integrity and every manifested file hash checked successfully; local links in six entry/companion documents resolved. These package checks do not verify UI behavior.

## Browser limitation
The browser tool refused navigation to the local `file:///C:/.../main-workspace.html` URL under its URL policy. It explicitly prohibited workaround/alternate routes to the same blocked action. No workaround was attempted. No screenshot or interaction success is claimed for study 02, and no Reticle verdict is available. The prior inline v0.1 model's recorded browser checks do not verify this new revision or its standalone stylesheet.

## Review scenarios still to exercise
1. Attach ready sample image/result; change one to conversation scope; send. Next-message chips leave the composer while sent context remains readable.
2. Attach ML studio workflow; current conversation/ownership remains main workspace. Source version is visible.
3. Send a prompt, answer via radio or free text, inspect generated fixture. No answer submits before the explicit button. Keyboard focus reaches the new question and result action.
4. Leave a question/draft open; switch to App planning and back. Histories, drafts, context and preview stay separate. Opening a new conversation leaves old ones available.
5. Load unavailable source; sending explains the blocker and preserves the draft. Remove it and send; no source is silently omitted.
6. Close/reopen preview; conversation/question/result remain. Toggle design-system sheet and return without resetting the current scene.
7. Attachment dialog traps focus natively, Escape closes and focus returns to Attach; all controls have visible focus. Check reading order and announcements with assistive technology.
8. Inspect wide, 1024 px and narrow screens for clipped text, overflow and usable stacked previews. Responsive CSS exists; it is not visually validated.

No automated behavioral suite was added for this disposable design study. Before QMX implementation is called done, the project requires a successful Reticle action/assertion verdict against the running app. These drafts do not satisfy or replace that requirement.
