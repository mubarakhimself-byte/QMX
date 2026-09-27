# Reference research — initial pass

Checked 2026-09-23. Public web text and supplied local images/video are different evidence types. This pass does not claim hands-on verification of reference-product interactions.

**Historical first pass.** The afternoon browser work supersedes the access limitations and next-step proposal below. Read `live-research/grounding-summary.md`, `openbb.md`, `xynth-prime.md`, and `quantx-lse-minara.md` for current findings. All seven links plus OpenBB were visited in the browser; access to their public material is not equivalent to authenticated testing.

| Reference | Evidence accessed | Relevance / limitation |
|---|---|---|
| [json-render](https://json-render.dev/) | Current official landing/docs material | Catalog-constrained component/action descriptions, JSON UI, progressive rendering and data binding. Candidate for QMX widget presentation; QMX must still define its own catalog and backend actions. It does not select the workspace hierarchy for us. |
| [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview) | Current official overview | Interactive HTML resources rendered inside a host, isolated in a sandbox, with host-mediated communication and capabilities. Candidate for embedded app views. QMX-specific authority, session identity, and storage still need explicit integration. |
| [Xynth](https://xynth.com/) | Current first-party public page | Describes question → research plan → dashboard findings. Worth inspecting as a research-to-result journey. Marketing descriptions do not establish exact UI behavior or research quality. |
| [Prime Terminal](https://prime-terminal.com/) | User URL `primemarket-terminal.com` redirects here | Public page describes modular widgets, custom workspaces, macro/news context, and research files. Useful dashboard/workspace reference; widget expansion/persistence behavior still needs browser evidence. |
| [QuantX](https://quantx.es/) | Page title only | Web text extraction returned no body. Product flow not inspected. |
| [Minara agent docs](https://minara.ai/docs/agent) | Attempted | Web tool could not access this page. No feature claims derived. |
| [London Strategic Edge terminal](https://www.londonstrategicedge.com/terminal) | Web tool inaccessible; supplied local demo inspected | Local frames show Markets, Workspace and Backtest areas, datasets/IDE, and docked assistant; see `video-reference.md`. No completed training or backtest outcome established. |

## Technical distinction to preserve

json-render and MCP Apps address different concerns: a constrained UI description/rendering approach versus a protocol/host mechanism for embedded interactive interfaces. They may coexist, but that is a design hypothesis rather than a selected architecture. Neither alone determines which QMX commands an agent is allowed to execute or which product entity owns an artifact.

The inspected backend describes both as presentation candidates and explicitly defers a UI contribution contract. That source describes QMX's current boundary, not a universal restriction on what these external projects can do.

## Next research

Prioritize one real journey each for OpenBB-like widget expansion/context attachment, LSE's dataset-to-strategy workflow, and multi-app workspace restoration. See `browser-research-brief.md` for a prepared Grok/browser-agent prompt. It has not been dispatched.
