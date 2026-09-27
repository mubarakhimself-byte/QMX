---
name: Provisional visual conventions
sitting: architecture-QMX-UI-2026-09-23
status: working-baseline — refine later
---

# DESIGN.md — provisional

Not a brand system. Neutral dark shadcn-svelte **Rhea** (May 2026 compact product style) is the working seed. Study 02 mint tokens and study 03 grayscale scaffolding stay dead.

## Density

Rhea-compact: tighter padding than default Luma. Mini-app canvas is **dense working widgets**, not cards of prose. Rail is narrow (icon-primary, label on hover or expanded). Copilot column is substantial when present, not a 200px leftover.

## Typography

Use the shadcn-svelte / Rhea type stack. UI chrome 14px. Widget titles 13–14px. Code in the editor face, not the chrome face. Do not invent a display serif.

## Color

Semantic tokens only (background, surface, border, foreground, muted, primary, destructive, warning, success). Chart series use the shadcn chart tokens. Financial up/down must remain distinguishable under deuteranopia (not green/red alone — pair with +/− text).

## Focus and motion

Visible focus rings. Motion short and optional (`prefers-reduced-motion`). Expand/return is a layout change, not a page fade that loses graph viewport.

## Spacing

8px grid via Tailwind 4. Widget gaps tight. Do not add study-control gutters inside the canvas.

## Readable states

Loading skeletons inside the **same** widget frame. Empty: one action (as Voices empty-state). Unavailable: identity + reason. Failed: typed refusal text. Stale: badge on the snapshot. Reconnecting: distinct from failed.

## What this file refuses

A second style authority. Paid dashboard kits. Copying OpenBB, VS Code, Hermes, or Codex branding. Custom hex palettes until a later aesthetic pass.
