# QMX experience study 02

**Historical proposal:** the user subsequently rejected this visual treatment and attachment picker. Its tokens are not approved QMX defaults. Continue from [study 03](../experience-v03/README.md). Attached-item chips, questions and preview concepts remain useful subject to the recorded corrections.

**Open `main-workspace.html` in a browser.** It is one self-contained file: no installation, server, external fonts, libraries or Codex runtime needed. Everything is simulated and stays in memory until the page closes/reloads. This is a disposable design study, not QMX application code.

## What to explore

Use the scene shortcuts to examine Start, Attach, Cross-app, Question and Preview. An additional scene covers an unavailable server source. Then try free interaction: attach a sample item, change its context lifetime, compose/send a message, answer the question, switch conversations, return, and close/reopen the preview. Scene shortcuts intentionally reset the sample conversations. The design-system sheet preserves the current state when you return.

The rail preserves the storyboard's global destinations, divider and opened apps as layout context. In this focused study those destinations are labels, not working navigation. `../experience-v01/whole-experience.html` is the portable version of the earlier wider navigation model.

## What this proposes

- New context defaults to **next message**, with an explicit **this conversation** choice. Earlier messages keep their sent-reference record when context is removed later.
- Referencing ML studio leaves ownership with the main-workspace conversation; it neither changes an execution target nor grants access.
- A question belongs to its conversation. Switching preserves the question, draft, references and preview state independently for as long as the page is open.
- The demonstrated task waits for a source choice. The second conversation remains usable. This does not settle general parallel-task behavior within one conversation.
- Closing a preview only hides it. It does not cancel work.
- An unavailable reference is not silently skipped. This draft blocks sending until that reference is removed; reconnect/retry/explicit exclusion are further design options.

These details and the dark palette are **unapproved proposals**. Accepted broad session direction is recorded in `../decisions.md` (D-017); it does not approve all these details.

## Files and portability

- `main-workspace.html`: interactive model and design-system sheet using the same CSS primitives.
- `tokens.json`: draft semantic colors/spacing/type, extracted from the model's CSS; a handoff aid, not an SDK schema or selected token standard.
- `component-contracts.md`: reusable behavior, states, accessibility needs and backend questions.
- `review-notes.md`: actual checks and verification gaps.
- `source-map.md`: which original/reference evidence informed this study.

The root `qmx-design-session-2026-09-23.zip` includes this study, the earlier wider model, Markdown specifications, full original dictation/source snapshot, images/research with provenance, decision records and a copy of the Wayfinder map. It is a working-session checkpoint, **not a final Grok handoff**. `CURRENT.md` is the short resume entry.

## Limits

All inputs/resources/questions/results are fixtures. Every sent message follows the same sample source-selection question; there is no language model. No uploads, local/server reads, live analyses, real persistence, tool permissions, approvals or task execution are implemented. Real-browser verification of this revision is outstanding; see review notes. Prior v0.1 browser checks do not establish v0.2 behavior.

The next design work adapts these patterns to app panels and expanded widgets, then deepens Library and authoring. Browser/video/code/diff/terminal previews, models/apps views, scoped settings, Home's running-work overview, risk/position sizing and execution-location indicators remain in the broader map. The design system develops alongside those scenes, then gets consolidated.
