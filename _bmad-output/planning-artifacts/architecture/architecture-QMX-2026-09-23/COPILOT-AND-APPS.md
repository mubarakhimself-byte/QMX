---
name: Copilot and apps — 2026-09-23 delta
sitting: architecture-QMX-2026-09-23
---

# Copilot and apps (delta)

Parent `architecture-QMX-2026-09-18/COPILOT-AND-APPS.md` stands. This sitting adds:

| Seat | Profile | Instance | Copilot panel |
| --- | --- | --- | --- |
| Main / general / home | authoring | optional (absent = nothing selected) | the main workspace — not a panel inside an app |
| In-app assistant | app-use | required | **optional** |
| Engine run | QMA `sess:` | n/a | none — not a chat |

One product identity. Independently scoped resumable `psess:` sessions. UI panels are not sessions. Permissions stay GrantRecords. Context transfer is `selected_refs` or `change_request`. MCP Apps / JSON Render are views the host may mount; they cannot grant.
