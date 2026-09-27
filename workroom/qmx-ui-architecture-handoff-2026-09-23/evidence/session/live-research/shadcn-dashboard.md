# Shadcn Dashboard reference: live interaction pass

Date: 2026-09-23. User explicitly supplied the browser tab and asked to click through dashboards, layout variations and applications. No authentication, purchase, installation, generated code or external data submission.

## Observed interactions

| Surface | Action and observation | Possible QMX use |
|---|---|---|
| [Reference home](https://shadcndashboard.dev/) | Opened Dashboard variations, then Layout variations, then Applications. The site exposes distinct example groups rather than only changing dashboard titles. | Compare working compositions deliberately; preserve QMX's original global/app/detail hierarchy. |
| [Analytics](https://demos.shadcndashboard.dev/) | Opened Analytics through its preview link and visually inspected the page. It has a sidebar, compact header controls, mixed-size chart/metric regions, filters, campaign statuses and a paged product table. | Chart and metric hierarchy, compact controls, mixed widget proportions; not its generic commerce content or complete sidebar structure. |
| [Horizontal SaaS/AI](https://demos.shadcndashboard.dev/dashboards/saas-ai?layout=horizontal) | Clicked Horizontal Version. The result actually moved category navigation above the content and removed the permanent left sidebar. Visually inspected its KPI row, chart and secondary distribution panel. Clicked 7D; control became active. Data accuracy or actual range recomputation was not established. | Direct reference for left/top layout variation. Test navigation placement while preserving context; it does not authorize copying these global menu categories into every QMX mini-app. |
| [Notes](https://demos.shadcndashboard.dev/apps/notes) | Opened Notes from the demo navigation; selected the second note. The editor visibly changed from the first note's content to the selected note's content. List/search and detail/editor areas remain distinct. No note was edited/deleted/created. | Library browse/select/inspect pattern, although QMX needs typed resources, provenance and version behavior beyond a notes list. |
| [Chats](https://demos.shadcndashboard.dev/apps/chats) | Opened Chats, then selected Maria Hernandez. The conversation header/messages changed and the attachment panel changed from five to four items. No message was sent. | Conversation navigation, compact composer and contextual resource panel. This is a human-chat demo, not evidence for QMX agent execution or permissions. |

Screenshots of Analytics, horizontal layout, Notes and Chat were visually inspected and emitted in the task. They were not saved as new local screenshot files in this pass. The browser's content-export command was unsupported; no successful export is claimed. Existing storyboard and earlier reference captures remain preserved separately. These notes preserve the observed actions and limitations.

## Implementation and cost distinctions

This site is a separate dashboard kit, not the core shadcn-svelte project. It advertises React/Next.js/TypeScript; its free [GitHub repository](https://github.com/shadcndashboard/shadcndashboard) describes React/Vite. Its [MCP page](https://shadcndashboard.dev/mcp) advertises a free component registry integration and React/TypeScript output. That does not demonstrate a Svelte-compatible installer or authorize installation.

Its [download page](https://shadcndashboard.dev/download) distinguishes Free and Pro, with different dashboard/application coverage. A publicly viewable demo is not proof every demonstrated component is available in the free source. Respect the user's zero-spend constraint: use suitable free Svelte components, consult the available source where useful, and adapt general interaction patterns. No paid assets were acquired, copied from restricted areas, or bypassed.

## Design inference

The useful lesson is the amount of existing component work we can reuse while varying page composition. QMX still needs its own resource and execution semantics, source-faithful mini-app layouts, and dense technical content. Do not inherit generic overview cards as a substitute for charting, ML runs, code diffs, Library detail or observability. User now accepts a neutral dark shadcn-like working baseline; that is a new allowance, not retroactive approval of the rejected studies.
