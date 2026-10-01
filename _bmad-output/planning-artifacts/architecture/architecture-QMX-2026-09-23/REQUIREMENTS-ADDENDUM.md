---
name: Requirements addendum — pack-and-grant kit
sitting: architecture-QMX-2026-09-23
---

# Requirements addendum

Adds the forgotten **relationship** on top of ADR-0024 / Workflows AD-1..AD-31. Does not reopen Book, ATC, fencing, or UI chrome.

## Must

- A pack author can declare operations, optional views, requested access, and an optional copilot profile without rewriting QMX.
- Installing is not granting. Enabling after validate is not granting. A session GrantRecord is granting.
- Some packs, widgets, and workflows have **no copilot**. The main authoring session can still reference them.
- Every public run is diagnosable headless: what, when, why, which of grant / workflow / widget / dependency / host failed.
- Ordinary failures retry in the **host** by default. Implementation repair is a change-request. App-use cannot apply it.
- Weaker models build and operate through schemas and grants.
- Apps compose via operations (one-to-one, one-to-many, many-to-many). Nested calls do not stack permissions.
- JSON Render and MCP Apps paint. They do not grant.

## Must not

- Sixth COMP, second scheduler, second telemetry store, QMN alert-allow-list reuse.
- Widget owning invoke. Merged live Task Graphs.
- Requiring a screen or a copilot to ship.
- Blind retry of `external-egress`.
- UI chrome in this sitting.
