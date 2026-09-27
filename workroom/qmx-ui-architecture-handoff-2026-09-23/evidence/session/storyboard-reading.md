> Afternoon correction: This is the initial reading. Use `live-research/grounding-summary.md` and `live-research/dictation-audit.md` for the complete current text and broader scope. The earlier one-journey-first suggestion was superseded after the user requested full reference grounding.

# Initial storyboard reading

Status: source-grounded interpretation, not an approved design specification. Read alongside `decisions.md` and `backend-grounding.md`.

## Source coverage

Read the complete Markdown text, decoded the compressed Excalidraw scene, inspected all 10 unique referenced images, and reviewed five reconstructed spatial views. The scene has 141 elements: 20 text blocks, 11 image placements, one video embed, and connecting shapes/annotations. One OpenBB image is used twice. The local video is 11.1 seconds; four sampled moments were reviewed at higher resolution by the video agent. See `video-reference.md` for what those frames establish.

The reconstruction in `evidence/*.png` preserves coordinates, attached images, text, and major shapes. It approximates Excalidraw fonts, rough strokes, line curvature, and arrowheads; it is a reading aid, not a pixel-exact export or a new QMX design. `scene.json` retains the original decoded structure.

## What the board is proposing

The strongest reading is a workspace that hosts both agent-led work and domain-specific mini apps. They share navigation and access to artifacts, while their panels and agent capabilities differ. The screenshots supply layout and interaction references; they do not specify that QMX must copy their product structure, features, or visual branding.

| Topic | User intent preserved | Source anchor | What is still unresolved |
|---|---|---|---|
| Overall shell | Use the layout relationship seen in OpenBB and VS Code: navigation, work area, adjacent copilot | `lDsh2tno`, `viURg15y`, top board sketch | Which regions persist across modes; exact proportions |
| Top bar | Favored, reusable, possibly absent for some apps | `YJYDP26I` | What the bar represents and when it appears |
| Main agent workspace | Broad access; sessions, history, agent settings, and a flexible preview area | `rrUMAlEq`, `C39LFtm1`, `JHZj5SdT` | How many previews, whether they dock/split, default arrangement |
| Preview types | Mini apps, widgets, workflows, browser/video, strategy/model cards, code, diffs, terminal, sub-agent work | `rrUMAlEq` | A shared viewer contract and type-specific interactions |
| Authoring | Previewing a workflow is distinct from authoring it; node-based and code paths are under discussion | `rrUMAlEq`, `JHZj5SdT` | Where authoring opens and how edits are saved/applied |
| Mini apps | Composition of widgets and workflows; many present as dashboards | `JHZj5SdT` | Definition, packaging, defaults, ownership, supported composition |
| Widget actions | Repeated controls for expansion, history, editing, and attaching context to copilot | `nLB3FO70`, `Y3XcLbSh`, `Ibr804Se`, `w6Wra1LH` | Exact action semantics and what every widget must support |
| Expanded view | More detail than the dashboard summary; could open a browser-like tab | `hoGJ6iaL`, `JHZj5SdT` | Tab, overlay, split pane, or replacement; return behavior |
| Global library | Preference for a shared QMX library reachable from previews | `NJidF6Tg`, `JHZj5SdT` | Locate existing item vs save generated result; sidebar vs tab |
| Agent access | Main copilot and mini-app copilot have different permissions, tools, and access | `JHZj5SdT` | Product scopes, context attachment, and mapping to backend authority |
| Multiple open apps | Persistent main menu, a separator, then active/open mini-app icons | `JHZj5SdT` | Open vs running vs selected; background activity and restore |
| App navigation | Overview/Financials/etc. inspire dynamic navigation within an app | `JHZj5SdT` | Distinguish app pages from open detail tabs and widgets |
| Settings | A global settings reference with possible app-specific configuration | `qhuD191N` | Global/app/widget/agent settings boundaries |
| Domain organization | Research/hypothesis and ML/coding are examples of placement | `JHZj5SdT` | Categories vs folders vs navigation destinations |
| Visual vocabulary | Reuse patterns for risk/BMS and execution location/status | `C2K3xORn`, `JHZj5SdT` | Exact domain meaning and verified data sources |
| Rendering technology | Consider json-render for widgets and MCP Apps for embedded/scoped interactions | `JHZj5SdT` | Suitability and responsibilities; neither selected yet |

## Reading the images and annotations

- **OpenBB**, `Pasted Image 20260922150714_899.png`: top-level app page tabs above a dashboard; repeated widget headers; tables/charts; a right copilot with a rendered table. The board's second placement circles expansion, history, edit-layout and message controls. The blue annotation points to a control under an assistant result table. The user proposes borrowing it as a route to the library; the screenshot alone does not prove that this is what OpenBB's control actually does. Likewise the risk/BMS use is a proposed QMX adaptation of the revenue widget, not the source widget's semantics.
- **VS Code**, `...151452_954.png`: activity rail, editor tabs, central work, and a right agent panel. Its visible document/chat text is incidental to the screenshot; it is not current authority and was not followed as instructions. The user's explicit emphasis is layout.
- **Hermes**, `...153805_586.png`: sessions/history on the left, central agent composer, and a browser pane on the right. This supports the main-agent layout reference.
- **Codex**, `...153840_932.png`: task sidebar, conversation column, and a separate area offering review, terminal, browser, files, and side chat. Treat old chat contents as incidental image content.
- **Cowork-style home**, `...153920_566.png`: persistent navigation and a spacious starting composer, supporting an empty/start state variant.
- **Manus**, `...154128_267.png`: project/task organization and instructions/files/skills cards. This is an alternative organization reference, not a requirement to introduce all those nouns.
- **Voice library**, `...154153_959.png`: global tool navigation plus a second filter column and collection content. Useful for library browsing/filter layout, independent of the source voice domain.
- **Workspace selector**, `...154354_046.png`: local/remote choice and a list with a progression action. This demonstrates a selection form, not a QMX requirement for a compulsory wizard.
- **Settings**, `...154421_046.png`: category tabs and grouped configuration panels, with a table for remote workspaces.
- **Ticker crop**, `...155654_792.png`: compact summary and repeated header actions. Linked by the board to the message icon explanation.

## Questions to resolve in order

1. **Workspace behavior:** open mini-apps, durable backend sessions, running jobs, and the currently visible view need distinct meanings. Existing backend code separates tab closure from product-session lifetime. Visual restoration and clear, explicit stop actions still need design.
2. **One complete widget journey:** see summary → expand → attach to copilot → inspect/save/find result in library → return to original app. Establish this before multiplying page designs.
3. **Mini-app contract:** app pages, widget descriptors, detail views, allowed commands, settings, saved state, and reference identity. Map to implemented backend objects before declaring gaps.
4. **Copilot context:** show what is attached and what scope can act. Merely selecting a panel must not silently grant backend permissions.
5. **Authoring and activation:** editing a workflow, running it, packaging a mini-app, and changing a live instance are different operations. Match the backend's actual lifecycle.
6. **Reusable design system:** establish common controls and rendering rules after the preceding behaviors are clear enough to support them.

This order is a proposal for discussion. The initial user request was to look and understand first, not to settle all six choices immediately.

## Important uncertainties

- “Open Bloomberg” in the dictation is associated with an image visibly branded OpenBB. Do not substitute assumptions about Bloomberg Terminal behavior.
- BMS/BIMS and “market sentient” may be dictated product names or transcription errors. Preserve them until clarified rather than inventing modules.
- The board does not specify final widget, workflow, or library schemas, app categories, default apps, breakpoints, theme, or a final navigation hierarchy.
- A node editor was explicitly left for further design. There is no basis to claim its UX is already defined.
