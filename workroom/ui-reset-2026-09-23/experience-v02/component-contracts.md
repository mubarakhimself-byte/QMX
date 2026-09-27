# Reusable interaction component contracts (draft)

Status: **proposals for review; none are approved contracts or existing APIs.** These are behavior-level boundaries for the fresh experience pass. They intentionally avoid visual tokens, framework choices, renderer selection, and backend API names. Primary design work owns the HTML and aesthetic decisions.

## Contract shape

Each component states its user intent, visible states, expected behavior, accessibility needs, and an open capability question for later reconciliation with Grok's current backend/SDK. A UI reference communicates context; it does not grant access or authority. A component should explain missing capability at the point of use and preserve enough identity to recover or inspect work.

The QMX design system includes behavior as well as presentation: stable interaction semantics, state language, keyboard/focus behavior, contribution rules, and renderer boundaries. Contributions should declare the meaning and supported views/actions of an item; a renderer presents those declared capabilities and gives an honest fallback when unsupported. json-render is a candidate way to describe/render selected interfaces against a QMX component catalog, while MCP Apps concern tool-associated interactive interfaces hosted in a client. They are distinct integration boundaries and may coexist with native/custom views. This document chooses neither and does not make either a backend requirement.

## Session switcher

- **Intent:** enter or resume the intended conversation while retaining separate app/object scopes.
- **States:** current session; recent/available sessions; new-session action; loading; unavailable or failed restore; empty history.
- **Behavior:** identify session and scope before entry. Switching restores that conversation without merging histories or changing its authority. Starting a new conversation leaves existing work discoverable. A visible view/session switch does not start, stop, or reauthorize a run. If restore is unavailable, explain what is known and offer a safe return/retry path.
- **Accessibility:** keyboard-operable list and actions; announce selected session and scope; preserve focus on return; do not rely on color or position alone.
- **Backend capability to check:** stable session identity, scope/ownership, history discovery, and supported restoration semantics. What is durable across restart/reconnect, and what can the UI truthfully report when history is unavailable?

## Composer and reference chip

- **Intent:** compose a message and know exactly which files, images, or QMX objects the copilot will receive as context.
- **States:** empty/drafting; reference being prepared; ready; unsupported; stale/unavailable/inaccessible; send pending; send failed; sent. Reference chip distinguishes at least **this message** from **conversation context**; the final retention model remains open.
- **Behavior:** add files, images, and app/workflow/widget/library references through an explicit action. Show identity/source and preparation outcome; let the user inspect/remove each reference. Make context scope visible and changeable before send. Sending a reference does not switch workspace ownership, choose a mutation target, or expand tool permissions. Never silently replace a failed reference with empty context. Preserve the draft on recoverable failure.
- **Accessibility:** labelled composer and attach/send/remove controls; chip name includes item and scope; keyboard insertion/removal and predictable focus; announce preparation/failure without interrupting text entry.
- **Backend capability to check:** supported reference types, stable identity/snapshot and freshness, preparation/access outcome, and context retention scopes. Which can be attached by reference versus uploaded copy, and what lifecycle can the product promise?

## Unavailable source

- **Intent:** explain that a referenced or requested item cannot currently be used, without implying it was empty or deleted.
- **States:** loading; stale; missing; unsupported; inaccessible/permission denied; disconnected; recovered; permanently unavailable only when authoritative evidence supports that claim.
- **Behavior:** retain the requested item's known identity and source, distinguish unknown from empty, and say whether retry, reconnect, locate, remove, or choose another item is available. Do not suggest access can be obtained merely by attaching again. If a fallback preview exists, label its age/source and keep the original reference understandable.
- **Accessibility:** announce state in text; expose recovery action names and status updates to assistive technology; use no color-only distinctions.
- **Backend capability to check:** authoritative error categories, freshness/version information, and whether a retry or alternate representation is supported. Which distinctions can the service actually guarantee?

## Question card: clarification or approval

- **Intent:** answer a question that blocks or informs work, while understanding whether the agent needs information or authorization.
- **States:** clarification requested; approval requested; answered; declined; expired/cancelled; awaiting result; unavailable. Show the waiting task/run and question origin when known.
- **Behavior:** label **clarification** (information needed) separately from **approval** (permission for a stated action). Offer concise relevant choices plus free text when supported. For approval, summarize the proposed action, target and scope using backend-supplied meaning; do not treat a clarification answer as approval. Show whether answering resumes work and what happened after the answer. Avoid asking users to provide details already present in visible context.
- **Accessibility:** question and purpose announced; choices usable by keyboard/screen reader; selected state explicit; free-text alternative available where appropriate; focus returns to the waiting context.
- **Backend capability to check:** question/wait identity, answer options and free-text support, approval semantics, expiry/cancellation, and resume/result state. What action details and target can the service authoritatively expose?

## Preview panel

- **Intent:** inspect an artifact/result in the workspace and continue related work without losing the source context.
- **States:** loading; ready; stale snapshot; unsupported renderer with fallback; unavailable; error; focused/open; closed. The panel identifies artifact plus relevant version/run/snapshot when known.
- **Behavior:** opening/focusing/closing a preview does not itself edit or stop work. Keep source app/session and a return path visible. A newer result is a distinct snapshot; do not silently mix it with the displayed one. Offer discuss/reference or edit actions only when contribution and authority support them. Unsupported rich views use a meaningful labelled fallback when available.
- **Accessibility:** focus enters and leaves predictably; panel has a descriptive title and close control; content remains navigable; changes in run state do not steal focus.
- **Backend capability to check:** artifact identity, version/run provenance, freshness, available view capabilities/fallbacks, and independent run lifecycle. What can be previewed safely while a run continues?

## Status indicator

- **Intent:** distinguish where an item is open, whether work is executing, and whether the connection/source is healthy.
- **States:** opened/viewing; running; waiting for user; completed; failed; disconnected/unknown; stale. Only show states supported by authoritative evidence.
- **Behavior:** separate app-open state from run state and connection/execution-location information. A disconnected or unknown status is not idle; an opened app is not automatically running. Pair concise text with any icon and provide last-known freshness where useful. Actions such as stop/retry appear only when supported and clearly identify their effect.
- **Accessibility:** status conveyed in text and announced when it changes meaningfully; icons have names; avoid rapid noisy announcements and color-only status.
- **Backend capability to check:** run lifecycle/status, freshness, connection health, execution location, and supported stop/retry actions. Which are separate facts, and which does the current backend expose reliably?

## Optional app copilot panel

- **Intent:** discuss the current app or selected object through a shared copilot capability, with the app context and scope visible.
- **States:** hidden/closed; open with selected app session; object reference attached; new or restored conversation; waiting; unavailable. App panel availability/default is configurable and is not required for every app.
- **Behavior:** retain the main workspace as the broad entry point and allow an app panel to resume its own separately scoped conversation. Opening an app panel does not create an isolated platform service, merge histories, or grant broader tools. Object context is an explicit removable reference. A request to change the app is routed through a supported authoring/change path and shown as a proposal before activation.
- **Accessibility:** labelled panel and scope; open/close and conversation controls work by keyboard; focus returns to the invoking app control; waiting state remains discoverable outside the panel.
- **Backend capability to check:** shared copilot/session model, app/object scopes, independent history restoration, grants/tool visibility, and supported change-request lifecycle. Reconcile with Grok's current SDK/core work before implementation.

## Wider design work still open

These contracts seed the main workspace only. The broader experience remains in scope: Home and active-work overview; mini-app pages and dynamic sections; compact/detail widget and workflow views; library locate/save/reuse; app composition and workflow authoring; scoped settings and history; expanded browser/video/code/diff/terminal/model/result views; and local/server/execution-location status. The exact layout, visual system, renderer catalog, contribution schema, and acceptance journeys still need design. See the source drafts and decision record below; no new decisions are implied here.

## Source trail

- [Experience storyboard v0.1](../experience-v01/experience-storyboard.md): scene rules S-01–S-08 and open questions O-01–O-08.
- [Main workspace next pass](../experience-v01/main-workspace-next-pass.md): states M-01–M-05; attachment scope and source distinctions; json-render/MCP Apps distinction; no backend transport choice.
- [Design system and authoring rules](../experience-v01/design-system-and-authoring.md): proposed behavior, contribution rules R-01–R-09, authoring and renderer boundaries.
- [Decisions](../decisions.md): D-015–D-019 and P-009–P-011 establish shared platform destinations, explicit json-render/MCP Apps discussion, optional app panels, independently scoped sessions, and main-workspace interaction scope. These contracts elaborate proposals; they do not ratify them.
- [Grounding summary](../live-research/grounding-summary.md): scope of the whole experience and evidence limits.
