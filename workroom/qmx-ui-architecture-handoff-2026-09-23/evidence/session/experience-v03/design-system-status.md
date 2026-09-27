# Visual system deferred; component behavior continues

The user explicitly rejects study 02's palette/rendering and will look for a preferred design system. Do not reuse its tokens as approved QMX defaults. Study 03's grayscale styles are disposable wireframe scaffolding, not a proposed brand direction. The layout relationship is primarily the user's storyboard contribution.

## What BMAD UX provides

Inspected the current local BMAD UX skill (`C:/Users/Mubarak/Desktop/QMX/.agents/skills/bmad-ux/SKILL.md`), its resolved customization/configuration and design-spec reference. It separates two peer contracts:

- **DESIGN.md:** visual identity, tokens, typography, spacing, shapes and component appearance.
- **EXPERIENCE.md:** information architecture, behavior, states, accessibility and journeys.

It also supports inheriting an existing UI system and documenting QMX-specific differences. It is a specification workflow, not a ready-made visual component library. User-specific instructions take precedence: no new palette, no lengthy discovery questionnaire, no archived UX revival, and no premature finalization. This was a scoped guidance check, not a completed formal BMAD UX run. No spines have been marked final.

## Practical division of work

1. Capture interaction anatomy and states now: app/widget frames, Library inspector, context chips, typed pickers, questions and preview tabs.
2. Once the user supplies or chooses a visual system, map these patterns to its existing components and identify missing pieces. Do not assume custom means rebuilding basic controls.
3. Define QMX-specific components and contribution requirements: what an app/widget must expose, fallback states, keyboard behavior and upgrade compatibility. Keep renderer choices, including json-render and MCP Apps, distinct from visual styling.
4. Grok implements against those contracts when the user is ready; verify rendered results against the agreed behavior and visual source, using the project's running-app proof requirements. Reconcile the updated backend/SDK before promising capabilities.

The useful outcome for future agents is a small entry point, accepted decision record, component/state catalogue and examples. The current packet supplies drafts of those; selecting a UI system and creating its actual component implementation remain unfinished work.
