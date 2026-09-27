---
id: LENS-UI-DESIGN-SYSTEM
title: QMX UI design system seed
type: lens
status: ratified
component: COMP-QMA-WIRE
depends_on: [COMP-QMA-WIRE]
decisions: [DEC-0469, DEC-0470, DEC-0472, DEC-0510]
sources: [DEC-0469, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# QMX UI design system seed

Working visual seed for the Svelte host. Not a brand freeze (DEC-0510 A12). Neutral dark shadcn-svelte Rhea compact is the seed. Study 02 mint tokens and study 03 grayscale scaffolding stay dead (DEC-0508).

## Rail

Four product destinations sit above the divider: Home, Copilot, Library, Authoring (DEC-0470). Settings is chrome, not a fifth product destination. Opened-app icons stay below the divider. WidgetFrame expand/return is an interior layout change, not a rail destination (DEC-0474).

## Density

Rhea-compact: tighter padding than default Luma. Mini-app canvas is dense working widgets, not cards of prose (DEC-0470). Expand/return lives in WidgetFrame and is not a fifth rail destination (DEC-0474). Rail is narrow (icon-primary, label on hover or expanded). Copilot column is substantial when present.

## Typography

Use the shadcn-svelte / Rhea type stack. UI chrome 14px. Widget titles 13–14px. Code in the editor face, not the chrome face. Do not invent a display serif.

## Color

Semantic tokens only: background, surface, border, foreground, muted, primary, destructive, warning, success. Chart series use the shadcn chart tokens. Financial up/down remain distinguishable under deuteranopia (pair with +/− text) (DEC-0483).

## Focus and motion

Visible focus rings. Motion short and optional (`prefers-reduced-motion`). Expand/return is a layout change, not a page fade that loses graph viewport (DEC-0474).

## Spacing

8px grid via Tailwind 4. Widget gaps tight. Do not add study-control gutters inside the canvas.

## Readable states

Loading skeletons inside the same widget frame. Empty: one action. Unavailable: identity plus reason. Failed: typed refusal text. Stale: badge on the snapshot. Reconnecting: distinct from failed (DEC-0479).

## Stack pins

Svelte 5.57.1, SvelteKit 2.70.3, bits-ui 2.19.3, shadcn-svelte 1.7.0 Rhea, Tailwind 4.3.3 (DEC-0469). Paid dashboard kits refused.

## What this file refuses

A second style authority. Copying OpenBB, VS Code, Hermes, or Codex branding. Custom hex palettes until a later aesthetic pass. Treating this seed as operator-accepted visual identity beyond sitting machinery (DEC-0510 A12).
