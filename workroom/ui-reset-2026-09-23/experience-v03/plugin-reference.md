# Plugin, app, skill, and attachment reference

Research date: 2026-09-23 (Africa/Nairobi)

## Verified from local metadata

- A **plugin** is a package/manifest with a name, version, descriptions, and optional references to bundled components. The `plugin.json` manifest may reference skills, an app definition (`.app.json`), or an MCP server definition. Examples: `visualize` declares `skills`; Figma declares both `apps` and `skills`; Linear declares `apps` and `mcpServers`; `codex-app-tools` declares `mcpServers`. This is evidence of packaging structure, not a full runtime specification.
- An **app/connector** is declared separately in `.app.json` under an `apps` map, with an app key, connector ID, and `required` boolean. In the inspected examples Figma, Linear, and Sites set `required: true`; GitHub sets `required: false`. The IDs differ in shape (`connector_…` and `asdk_app_…`). Metadata alone does not explain how credentials, authorization, or a live connection are acquired.
- A **skill** is a directory of instructions/workflows the assistant can apply. The plugin manifest points to a skill directory; `plugin-creator` also documents optional plugin folders for skills, scripts, assets, MCP, and apps. A skill is not itself the external app connection.
- An **MCP server/tool** is another possible plugin component: the manifest points to an MCP server config. Its presence is distinct from an app declaration; some packages declare both (Linear), while others declare only one (Codex app tools).
- **Capabilities and suggested prompts** are presentation metadata. For example, the Visualize and Sites manifests list capabilities and starter prompts, while Linear lists no capabilities and one starter prompt. These fields are not proof of what the runtime will permit in a particular conversation.

## Attachments and context: what these sources establish

The inspected manifests and plugin-creator skill do **not** define composer attachment behavior for files, datasets, connected apps, or plugins. They do not establish that attaching a file installs a plugin, that mentioning an app connects it, or that a connected app’s data becomes automatically available. I did not inspect the Codex composer UI, so no claim here is based on a tested plus-menu flow.

Practical distinction for QMX: a user-provided file/dataset is an input artifact; a connected app is an integration that may provide data or actions subject to connection and permissions; a plugin is the discoverable package that can bundle skills and/or integrations; and a skill is reusable instructions. These labels are a proposed explanatory model for QMX, not a statement about an existing QMX backend.

## QMX miniapp UX proposals (inference)

- Let a miniapp declare its type and dependencies visibly: **Miniapp**, **Skill**, **Connected app**, and **MCP tool**. Show which components are included, and which external connection is required or optional.
- Keep “add a file/dataset” separate from “connect an app” and “add a miniapp.” After a file is added, show its name and how the miniapp will use it. After an app is selected, show connection/permission state before enabling app-backed actions.
- Model data as explicit context the user can inspect and remove. Show source, scope, and whether it is a one-time uploaded artifact or a connected source. Do not imply that adding a plugin automatically grants access to any app data.
- Give miniapps a concise description, owner, category, capabilities, and example prompts. The sampled manifests already use those kinds of discoverability metadata; QMX can make dependencies and access state more explicit.
- Provide clear states for **available**, **added/installed**, **needs connection**, and **ready**. This follows from plugin metadata distinguishing a package from its separately declared app dependency, but the exact state model is a QMX design proposal.

## Local sources inspected

- `C:\Users\Mubarak\.codex\plugins\cache\openai-bundled\visualize\1.0.39\.codex-plugin\plugin.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-bundled\codex-app-tools\0.1.4\.codex-plugin\plugin.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-curated-remote\figma\12.0.0\.codex-plugin\plugin.json` and `.app.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-curated-remote\github\0.1.12-5f7cd798dc99\.codex-plugin\plugin.json` and `.app.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-curated-remote\sites\0.1.71\.codex-plugin\plugin.json` and `.app.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-curated-remote\linear\5.0.1\.codex-plugin\plugin.json` and `.app.json`
- `C:\Users\Mubarak\.codex\plugins\cache\openai-curated-remote\plugin-management\0.1.0\.codex-plugin\plugin.json` and `.app.json`
- `C:\Users\Mubarak\.codex\skills\.system\plugin-creator\SKILL.md`

No official web docs were needed for this bounded reference; composer attachment behavior remains unverified.
