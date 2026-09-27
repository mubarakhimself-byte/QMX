# Optional browser research handoff

Prepared because the storyboard proposes using Grok/browser agents for navigation. Not dispatched. Use this for the next evidence pass once the desired journeys are selected; avoid paying for an exhaustive tour of every site.

## Prompt

Investigate reference interactions for a fresh QMX UI/UX design. Use a real browser and record what you actually observe. The goal is to understand navigation and behavior, not copy branding or endorse financial claims. Do not read old QMX UI/UX documents.

QMX's current design input distinguishes a broad main agent workspace (sessions/history plus browser, terminal, code, media and app previews) from mini-app dashboards with a copilot whose tools/access are scoped differently. Mini apps may compose widgets and workflows. Important unresolved choices are multiple open apps, widget summary/detail views, app pages versus opened tabs, sending widget context to copilot, and opening or saving artifacts in a shared library. Backend implementation is being examined separately: do not invent QMX APIs or declare code gaps from competitor behavior.

References: https://www.londonstrategicedge.com/terminal, https://xynth.com/, https://prime-terminal.com/ (the user's old URL redirects here), https://quantx.es/, https://minara.ai/docs/agent. The supplied OpenBB image is branded pro.openbb.co; use official OpenBB documentation/demos or an available read-only workspace to investigate it. Record exact pages visited and redirects.

Prioritize these journeys:

1. Open a dashboard, inspect one widget's header actions, expand it, and return. Does detail replace the dashboard, open a tab, open a dialog, or create another pane? Does state remain?
2. Attach that widget/result to an assistant, if supported. Record the visible context indicator and what is actually attached. Do not infer permissions from an icon.
3. Find an existing result in a library or save a generated result if a harmless sandbox permits it. Distinguish locating, copying, exporting and saving; do not treat these as interchangeable.
4. In LSE, trace an existing dataset through preview, code/notebook, strategy editing and result display using already available examples. Identify navigation changes, whether the assistant remains, and the distinction between generated code and completed execution.
5. Inspect workspace/app switching: which panels remain, what the tab levels mean, where background activity is shown, and whether closing a visible tab stops work. Only claim close/restore behavior if observed safely or explicitly documented.

Prefer existing examples and read-only actions. Do not purchase, trade, publish, alter account settings, or submit paid compute/training/backtest jobs. If login is required, report the boundary and use public docs/demos; do not pretend a landing page proves the signed-in journey. Avoid capturing credentials or personal account data.

For each inspected journey return: URL and date; short click sequence; screenshots of before/action/after states with filenames; visible labels; observed behavior; separately marked inference; blocked steps; one useful QMX implication; and the backend capability the proposed interaction would require, phrased as a question for the backend inventory. Report missing/disabled/loading/error states if encountered naturally.

Conclude with a small comparison table across the observed products for app navigation, internal pages, expanded detail, assistant context, library handoff, and state restoration. Leave cells “not observed” where appropriate. Deliver Markdown and screenshot files in one evidence folder. Stop after useful evidence for the prioritized journeys; do not produce a generic marketing feature list or a finished QMX design.
