# Review — Currency / Reality lens

**Spine:** `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md` (draft 2026-09-23, local AD-1..AD-8)
**Companions consulted:** `CONTRACTS.md`, `COPILOT-AND-APPS.md`, `research/INVESTIGATION-SYNTHESIS.md`
**Lens:** every named technology and factual version claim must be web-current or brownfield-checked, not asserted from training memory. This sitting adds **no required runtime**.
**Inherited pin source:** workspace `docs/architecture/stack.md` (`verified: 2026-09-19`)
**Brownfield cite:** spine `integration@34c148b`
**Reviewer gate date of checks:** 2026-09-23

Web (primary sources, this sitting): python.org downloads + 3.14.7 release page + PEP 745; github.com/vercel-labs/json-render releases + npm `@json-render/core` + json-render.dev/docs/catalog + json-render.dev/docs/changelog; github.com/modelcontextprotocol/ext-apps specification table + `specification/2026-01-26/apps.mdx` + npm `@modelcontextprotocol/ext-apps`; modelcontextprotocol.io specification/2026-07-28 (latest); pypi.org/project/opentelemetry-sdk; docs/components/qma-daemon.md AD-23; stack.md QMA application stack.

Nothing below is from training data. Every version and “still exists / still fits” claim was fetched or read on 2026-09-23.

---

## Verdict

**PASS.**

Named technologies still exist and still fit the roles this sitting assigns them. Presentation candidates (json-render, MCP Apps SEP-1865) are real and correctly left unpinned. CPython 3.14 remains the inherited series pin; 3.14.7 is still the latest stable. OpenTelemetry remains an export-port adapter in inherited QMA, not a daemon-core SDK, and Python `opentelemetry-sdk` 1.44.0 is still the upstream tip. This sitting adds **no required runtime**.

One low finding: the Stack table copies the parent’s json-render snapshot (`v0.20.0 as of 2026-08-18`). Upstream tip as of this gate is **v0.21.0** (2026-09-18). That is snapshot drift on an unpinned candidate, not a wrong pin and not a role change.

---

## What I verified on the web (primary sources)

### CPython — Stack row: `3.14 inherited`

- **Latest stable = 3.14.7, released 2026-08-05.** Confirmed: python.org “Latest: Python 3.14.7”; python.org/downloads/release/python-3147/; python.org/downloads/latest/. No 3.14.8 today.
- **PEP 745 (fetched 2026-09-22):** 3.14.7 actual 2026-08-05. **Expected:** 3.14.8 Tuesday 2026-10-06. Not shipped.
- **3.15 is not stable.** python/cpython has an active `3.15` branch; 3.15.0rc2 exists (2026-09-01). Spine does not claim 3.15. Correct.
- **Brownfield:** `docs/architecture/stack.md` QMF row `CPython | 3.14 (3.14.7 current)` (DEC-0099); QMA row `3.14 (3.14.7 re-verified 2026-08-28)` (DEC-0334). Root `pyproject.toml` `requires-python = ">=3.10"` is a packaging floor, not the runtime pin.
- **Fit:** inherited DEC-0099 pin of the **3.14 line** still holds. This sitting restates the series, not a patch. “Inherited, not upgraded here” is the right posture.

### json-render — Stack / AD-8: not pinned; `upstream v0.20.0 as of 2026-08-18`

- **Exists:** https://json-render.dev live. Catalog-constrained generative UI: catalog is the vocabulary (components, actions, functions); schema is the grammar; AI emits JSON inside the catalog (`json-render.dev/docs/catalog`, fetched today).
- **Upstream tip today:** github.com/vercel-labs/json-render **v0.21.0** (released 2026-09-18; changelog dated September 18, 2026). npm `@json-render/core` **0.21.0** (Apache-2.0). New in 0.21.0: `@json-render/tanstack-start`, experimental Jev composition, Vue named slots, React streaming stability, Labs status badges. Catalog/action model is unchanged.
- **Historical snapshot:** v0.20.0 **was** the GitHub release of 2026-08-18 (github-actions, 18 Aug 18:23). Parent 09-18 currency review recorded it as tip that day. Copying that “as of” into a 2026-09-23 spine without re-dating is the drift in L-1.
- **Not a PyPI package.** Correct that this sitting does not invent a Python pin.
- **Fit:** AD-8 “JSON Render is a catalog-constrained generative view” and Prevents “json-render as runtime” still match the catalog-guardrail model. CONTRACTS §7 “json-render catalog `action` names an existing `op_id`” is a QMX overlay, not an upstream json-render rule — currency-ok, architecture-owned. Native QMX panes remain first. Unpinned presentation candidate remains the correct currency posture. v0.21.0 Labs badges reinforce “do not pin `@json-render/*` here.”

### MCP Apps — Stack / AD-8: `SEP-1865 2026-01-26 — presentation candidate, not storage`

- **SEP:** github.com/modelcontextprotocol/modelcontextprotocol `seps/1865-mcp-apps-interactive-user-interfaces-for-mcp.md` — **Status: Final**; Type: Extensions Track; Created 2025-11-21; PR #1865.
- **Dated spec still Stable:** github.com/modelcontextprotocol/ext-apps Specification table: **`2026-01-26` | Stable** (`specification/2026-01-26/apps.mdx`; Status: Stable (2026-01-26)). A `draft` folder exists beside it. Spine names the stable dated spec, not the draft. Correct.
- **Shape matches AD-8 wording:** tool + `ui://` resource (`_meta.ui.resourceUri`), HTML `text/html;profile=mcp-app`, **mandatory iframe sandbox**, JSON-RPC over `postMessage`. Hosts act as MCP servers that **proxy** the actual server. Interactive phase: View → Host `tools/call` → Host → Server `tools/call`. Host `serverTools` capability is “Host can proxy tool calls.” Host MAY block messages. Threat model includes unauthorized tool execution. CONTRACTS §7 “MCP App `tools/call` is intercepted by the host against the session GrantRecord” is a QMX overlay on that host-proxy rule — currency-ok.
- **SDK, unpinned:** npm `@modelcontextprotocol/ext-apps` **2.0.0** (2026-09-08). Release notes: wire protocol **unchanged** vs 1.x (2.x Views run in 1.x hosts). Breaking surface is TypeScript peers (`@modelcontextprotocol/client@^2`, zod 4.2+), not the Apps spec date. Spine “Do not pin `@modelcontextprotocol/ext-apps` here” remains correct.
- **Do not conflate with the QMA MCP adapter pin.** Inherited QMA stack pins **Model Context Protocol revision 2026-07-28** as the ToolAdapter surface. That is still the latest **core** protocol (modelcontextprotocol.io “Version 2026-07-28 (latest)”, page updated 2026-09-22). This sitting names the Apps **extension** only, as a presentation candidate, not a daemon dependency. Fit is correct.

### OpenTelemetry — Stack: `export-port adapter only, inherited QMA` / AD-5: `OTel remains export-port only`

- **Architectural role (brownfield, not a new pin):** `docs/components/qma-daemon.md` AD-23: “OpenTelemetry conformance happens at the export port as a swappable adapter, **never as an SDK imported into the daemon core**” (DEC-0322). `docs/architecture/stack.md` QMA row: “OpenTelemetry Python SDK (behind the export port) | 1.44.0”. QMN V1 has **no** OTel (DEC-0200); research synthesis plane table matches: QMN prometheus_client, QMA OTel-shaped export adapter.
- **Upstream Python SDK tip:** pypi.org/project/opentelemetry-sdk **1.44.0** (released 2026-07-16). GitHub open-telemetry/opentelemetry-python tag `v1.44.0`. No 1.45.x today. Inherited 1.44.0 is still current. This sitting correctly does **not** restate the patch number.
- **Fit:** AD-5 “harness-authored QMA telemetry (agents must not write it; OTel remains export-port only)” matches the inherited law. Daemon JSON-lines are stdlib, not an OTel logger. No fourth observability product. Role is unchanged.

### Inherited stores / tooling this sitting does not bump

| Pin | Spine posture | Web / brownfield 2026-09-23 |
| --- | --- | --- |
| uv workspace + lockfile | inherited (`stack.md`) | Not restated here. QMF 0.12.5 / QMA 0.12.7 in stack.md. Informational only. |
| QMA daemon store | SQLite single writer inherited | Matches AD-6 sole-writer; stack.md 3.50.4 WAL floor. No new version claimed. |
| OpenTelemetry Python SDK | export-port only, inherited | **1.44.0 still latest** (2026-07-16). |
| MCP core (ToolAdapter) | not restated | **2026-07-28 still latest** core spec. Distinct from Apps 2026-01-26. |

### Named donor technologies — still exist, still fit the refuse/borrow split

Spine Stack: “Hermes / n8n / OpenBB / Salesforce / Bloomberg / GHL / Slack / VS Code | mental models only.” AD-1 Prevents n8n-as-runtime. This sitting does not import them.

| Named in spine | Exists? | Fit of the sitting’s use |
| --- | --- | --- |
| Hermes | Yes — prior sitting verified NousResearch/hermes-agent | Mental model only. AD-5/research: pack validate is a hard gate, not warn-and-continue. |
| n8n | Yes | Mental model for visibility / graphs. Not imported. AD-6 refuses n8n Retry-On-Fail as same-task mutation. |
| OpenBB | Yes | Mental model only. |
| Salesforce / Bloomberg / GHL / Slack / VS Code | Yes as products | Named as mental models only. No versions claimed. No pins. |

---

## Findings

### L-1 — json-render Stack snapshot is five days stale (Low)

- **Spine:** “json-render \| not pinned — presentation candidate; upstream v0.20.0 as of 2026-08-18”
- **Today:** github.com/vercel-labs/json-render latest release **v0.21.0** (2026-09-18). npm `@json-render/core@0.21.0`. Parent 09-18 currency review recorded 0.20.0 as tip; 0.21.0 shipped the same calendar day after that gate.
- **Not a fail:** the sitting does not pin `@json-render/*`. Catalog-constrained generative view still describes 0.21.0. Labs status in 0.21.0 strengthens “do not pin.”
- **Desk fix if the Stack table is restated:** `upstream v0.21.0 as of 2026-09-18` (or drop the snapshot number and keep “not pinned”). Do not promote 0.21.0 to a product pin.

### Informational (not findings)

- `@modelcontextprotocol/ext-apps` **2.0.0** (2026-09-08) exists. Wire protocol unchanged; spec date remains 2026-01-26 Stable. Unpinned is still right.
- CPython **3.14.8** expected 2026-10-06 (PEP 745). 3.15.0 final expected ~2026-10-01. Neither is adopted; neither is claimed.
- OTel Java SDK is on a different version line (1.65.0). Spine means the **Python** export-port adapter. Do not confuse the two.

---

## Training-data assertions

**None.** Every named-tech claim in the spine Stack / AD-5 / AD-8 was checked against a primary source or the inherited brownfield docs on 2026-09-23. Companion CONTRACTS §7 and COPILOT-AND-APPS adapter sentences are QMX overlays on verified upstream shapes, not invented protocol.

---

## Summary table

| Named tech | Exists? | Claimed version | Current 2026-09-23 | Posture |
| --- | --- | --- | --- | --- |
| CPython | Yes | 3.14 inherited | **3.14.7** latest stable; 3.14.8 expected 2026-10-06; 3.15 rc only | Series pin holds |
| json-render / `@json-render/*` | Yes | not pinned; snapshot v0.20.0 as of 2026-08-18 | **v0.21.0** (2026-09-18) | Unpinned; snapshot stale (L-1) |
| MCP Apps SEP-1865 | Yes | SEP-1865 2026-01-26 | Spec **2026-01-26 Stable**; SEP Final; SDK 2.0.0 unpinned | Unpinned presentation candidate |
| MCP core (inherited, not restated) | Yes | (QMA ToolAdapter 2026-07-28) | **2026-07-28 still latest** | Distinct from Apps extension |
| OpenTelemetry | Yes | export-port adapter only | Python SDK **1.44.0** still tip | Inherited role holds |
| Hermes / n8n / OpenBB / Salesforce / Bloomberg / GHL / Slack / VS Code | Yes | mental models only | n/a | Not imported |

---

## Gate

Currency gate **PASS**. One Low snapshot fix is optional if the Stack table is touched; it does not block freeze. No vanished library. No wrong required pin. No training-data version.
