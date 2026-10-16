---
title: Output methodology: animated explainer documents
type: prototype
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 7."
---

## Question

How every agent output becomes an animated, interactive explainer document that renders in the QMX UI, including what the agent did, so he never reads a block of text; and what chat widgets and preview modes the UI needs for it.

## Why it matters

Correction 10: not pictures; Kimi K3 research pages and Claude Motion or Design style, diagram-led. Correction J: chat needs widgets and preview modes. `11` proposes agents emit structured JSON, fixed QMX templates render it, a grader checks first. `10` §4 lists the rendering gaps: no Markdown, no diagram parts, no reveal format, no explainer viewer.

## Recommended answer

The rules in `12` section (f): JSON in, fixed templates out (dashboard card, explainer document, scrollytelling story, scorecard or funnel, short motion explainer later, one-line alert); a grader validates schema, sources, Mermaid and a headless render before display; the receipt rule folds tool calls into "What it did"; an inline widget mode and a drawer preview mode; play, scrub and "show all"; provenance on click; freshness stamps; refusal as a valid output with claim labels. UI work that can start today: the Markdown renderer and the catalog's diagram parts.

## What the session does

Prototype three variants of the explainer document (one funnel scorecard, one research note, one morning card) as inline widgets and as previews, switchable by a URL parameter, on demo data that shows shape only. He picks. Output: the report JSON schema, the template list, the widget and preview spec.

## Unblocks

Methodology umbrella; gives the UI session the renderer brief.

## Sources

`11-references.md` §4, output proposal; `10-ui-depth.md` §4; clipping "Post by @karpathy on X"; `02-pocock-pstack.md` HTML-REPORT, ketchup; corrections 10, J.
