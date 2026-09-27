# QuantX, LSE, Minara, and technical references

Observed 2026-09-23 through the real browser. These are UI research findings, not evaluations of trading results, security claims, or model quality. No account creation, prompt submission, training, workflow execution, trade, or installation was performed.

## QuantX: dense analysis, node authoring, scoped document chat

Source: [public product showcase](https://quantx.es/signup#das). Read its page and inspected full-size product images loaded from the page. [App login](https://app.quantx.es/login) required authentication; no live authenticated editor was used.

- The dashboard image combines a narrow global rail, scanner/master list, alerts/news, charts and ticker context in a dense multi-column canvas. Controls include Customize, Full Analysis and Full View, but their behaviors were not tested.
- The strategy-builder image shows a searchable component catalogue, a node canvas arranged into named processing stages, warnings, a bottom toolbar, and node/edge counts. Catalogue entries include data inputs, computed values and logic. This is a valuable visual reference for the code/node authoring part of the dictation, not proof that every shown feature works.
- A results image shows comparative curves, an equity/drawdown choice and a bucket selector. This suggests related summary and diagnostic views; the image's controls were not interactive.
- The filing image places a document beside an “ASK THE FILING” assistant with focused prompts. The visible document makes the assistant's intended scope understandable.
- Public DAS-bridge copy advertises explicit destination choices, including latest/all/locked montage. This is a vendor claim and an interesting scope-design example, not an integration requirement for QMX.

Saved visual evidence: [dashboard](screenshots/quantx-dashboard.png), [node builder](screenshots/quantx-strategy-builder.png), [results](screenshots/quantx-results.png), [filing assistant](screenshots/quantx-filing-assistant.png). These are browser captures of official product images. The extra `quantx-builder-results-comparison.png` is a partial page capture, not a complete builder view.

Image sources: [builder](https://quantx.es/platform/cmp-builder.webp?v=20260531e), [results](https://quantx.es/platform/backtester-results.webp?v=20260531e), [filing assistant](https://quantx.es/platform/talk-zoom.webp?v=20260531e).

QMX inference: distinguish composing a workflow from operating its dashboard, and make the scope of an embedded assistant explicit. Do not copy the vendor's processing-stage taxonomy into QMX without checking QMX's actual graph model.

## London Strategic Edge: actual task-specific workspace changes

Sources: [terminal landing](https://www.londonstrategicedge.com/terminal/) and [public ML Studio](https://www.londonstrategicedge.com/machine-learning-studio/). The landing plays the same short terminal demo as the supplied local video, links public tools, and offers a desktop download. No download/install was performed.

Actual interactions in ML Studio:

1. Inspected Train: left model catalogue, central data/training form, right Model Guide, and an empty result region.
2. Opened the dataset picker, searched EUR, and selected EUR/USD. The form visibly changed from BTC/USD to EUR/USD.
3. Switched to Optimise. The left rail changed from models to optimisation methods; the center required a completed model and showed a disabled run control; the right guide changed with the selected method.
4. Selected Walk Forward. Fold controls appeared and the disabled action reflected five folds. No completed model existed and no run was launched.

Saved: [training workspace](screenshots/lse-ml-studio.png), [selected dataset](screenshots/lse-dataset-selected.png), [Walk Forward empty state](screenshots/lse-walk-forward.png). The selected-dataset capture was initially named `lse-optimise-empty-state.png`; visual review showed screenshot timing had retained the previous Train state, so it was renamed accurately.

QMX inference: a mini-app can retain its shell while changing its navigation, central controls and help to suit the task. A missing prerequisite should be visible where the next action would happen. Dataset selection, model execution and subsequent optimisation are different user states, not just differently titled dashboards. The current public interaction does not prove training or backtesting correctness.

## Minara: global rail, local history, distinct creation surfaces

Sources: [agent docs and use cases](https://minara.ai/docs/agent), [compare strategies](https://minara.ai/docs/agent/start-here/use-cases/compare-strategies), [public chat app](https://minara.ai/app/chat), [Strategy Studio](https://minara.ai/app/strategy-studio).

Actual app observations and interactions:

- Chat opens with a persistent narrow rail for Chat, Agent, Trade, Strategy and Workflow; an adjacent mode-specific history panel; and a main composer with suggestions, mentions and shortcuts.
- Selecting Workflow retains the global rail but changes the history panel, page purpose, example prompts and quick templates. Selecting Wallet Monitor reaches a login gate. No workflow was created.
- Strategy Studio has its own Time-Series/Cross-Sectional organization, a strategy-specific composer, and alternate entry cards for a form, image/video and existing code. It also displays templates and performance figures. These are displayed product content, not results we verified.
- The strategy page visibly separates Strategy Studio, Top Strategies and Marketplace in its top navigation. No marketplace purchase, strategy generation or deployment was attempted.
- Some accessibility output contains hidden trading-panel elements. They were not visibly rendered in the inspected workspace screenshots and are not counted as observed UI.

The agent docs describe working with an active asset and comparing strategies across metrics and evaluation windows. The asset-copilot embedded image failed to load; `minara-asset-copilot-doc.png` records a docs page with a missing image and must not be cited as a successful visual inspection of that product surface.

Saved actual-app screenshots: [chat](screenshots/minara-chat-workspace.png), [workflow](screenshots/minara-workflow-home.png), [strategy](screenshots/minara-strategy-home.png).

QMX inference: the user's global rail plus app-specific organization has a useful real-world comparison here. A shared shell need not make every app use the same central screen. History should identify the kind of work being resumed. Creation can expose multiple entry methods without making operating a saved app feel like editing its source.

## Technical references revisited in the browser

- [json-render](https://json-render.dev/): read the visible catalogue/component/action examples and progressive-rendering explanation. It describes generating interfaces from a defined component/action catalogue. No implementation or reliability test was performed. QMX must supply its own allowed components and action bindings.
- [MCP Apps overview](https://modelcontextprotocol.io/extensions/apps/overview): read the resource, host, sandbox and communication model. It describes embedded interactive HTML resources and host-mediated capabilities. No QMX host integration was performed.

These solve different problems and remain candidates. A renderer does not decide a user's permissions, durable session ownership, library identity, workspace navigation, or the authoring/app-use boundary.
