# Research result

**Status: Partial**

As of 2026-09-23, pin MIT or Apache-2.0 libraries that run in Svelte 5 / Vite without a React runtime, and skip paid dashboard kits. Dedicated canvas OHLC kits cover financial candlesticks; a separate Svelte graphics trio covers ordinary line/bar/area analytics without first-party candles. Virtualized tables, CodeMirror 6 (editor and merge) or Monaco, git-diff-view, xterm.js, and a Svelte command menu are all available on that license/runtime footing. Inspected table packages and CodeMirror have no Tauri issue hits; Monaco worker/clipboard wiring and xterm WebGL transparency on WKWebView are the known WebView problems.

### Financial candlestick charts

Dedicated financial canvases sit beside uPlot (a tiny time-series chart that includes OHLC), ECharts (general visualization that still has a candlestick series), and liveline-svelte (the only native Svelte 5 candle component here). The Svelte 3-era Lightweight Charts wrapper is the compatibility outlier.

| Library | Latest | License | Svelte 5 / Vite | Workers | Unmount / dispose | Accessibility |
|---|---|---|---|---|---|---|
| TradingView Lightweight Charts | 5.2.1 | Apache-2.0; NOTICE attribution plus a tradingview.com link | Framework-agnostic HTML5 canvas. Community lightweight-charts-svelte 0.0.1 (MIT) peers svelte ^5 and lightweight-charts >=5, with Vite in package scripts. Older svelte-lightweight-charts 2.2.0 peers svelte >=3.44 and lightweight-charts >=4.0.0 (repo pins 3.55.1 / 4.0.0) | — | IChartApi.remove() irreversibly removes the chart and DOM | Official @tradingview/lwc-plugin-accessibility 1.0.0 (2026-09-16): keyboard, ARIA-live, WCAG table [S1] |
| KLineChart (klinecharts) | 10.0.3 | Apache-2.0 | Zero-dependency HTML5 canvas; Vite is the repo debug/dev server; no first-party Svelte 5 package (community SvelteKit v10 demo only) | — | init on mount; dispose(HTMLElement / Chart / string) on unmount | — [S2] |
| uPlot | 1.6.32 | MIT | ~50 KB Canvas 2D for lines, areas, OHLC, and bars. svelte-uplot 0.1.0 (MIT) peers svelte ^5.29.0 and uplot ^1.6.25, Vite; option changes destroy() then new uPlot(...) | No first-party Web Worker renderer | destroy() destroys DOM and removes resize/scroll listeners | — [S3] |
| Apache ECharts | 6.1.0 | Apache-2.0 | Canvas default or SVG; candlestick series (6.1.0 adds candlestick cursor and fixes horizontal-layout encode) | Init opts include renderer, ssr, useDirtyRect, useCoarsePointer — not an official OffscreenCanvas worker mode (third-party experiments only) | chart.dispose() after renderToSVGString to release memory | — [S4] |
| liveline-svelte | 0.0.3 | MIT | Native Svelte 5 (peer svelte ^5), Vite-built, no runtime deps beyond svelte; line, multi-series, and candlestick/OHLC via an internal ~60fps requestAnimationFrame loop | No Web Worker or OffscreenCanvas path documented | — | Root div forwards aria-* [S5] |

### Ordinary analytics charts

These are the non-OHLC pin: headless or composable Svelte graphics for line/bar/area (and similar), not first-party financial candle kits. Flarecharts is the accessibility-heavy SVG outlier and the only MIT-plus-Attribution license in this set.

| Library | Latest | License | Svelte 5 / Vite | Chart types | Accessibility |
|---|---|---|---|---|---|
| LayerCake | 11.0.0 | MIT | Headless Svelte graphics framework; requires svelte >=5.40 (v11 changelog 2026-09-05) | Ordinary analytics (not a first-party OHLC kit) | Svg layout sets role=img when label, labelledBy, or describedBy is passed [S6] |
| LayerChart | 2.5.0 | MIT | peer svelte ^5 | Composable Cartesian Area, Bar, Line, Scatter — no candlestick | — |
| Flarecharts (@faintshadow/flarecharts) | 26.3.1 | MIT + Attribution | Svelte 5 runes-first SVG (peer svelte ^5) | Line, Area, Bar, Stack, Donut, Sparkline — not candlestick | Visually-hidden data tables, aria-live, and arrow-key point navigation |

### Virtualized tables

All five are Svelte-native or Svelte adapters rather than React shims. Only TanStack Table documents an experimental row-model worker; only SvGrid labels old WebViews as best-effort. Inspected LICENSE files are MIT (none Apache), and inspected package.json dependency lists do not include React. [S12]

| Library | Latest | License | Svelte 5 / Vite | Virtualization / workers | Unmount / dispose | Accessibility | Tauri WebView |
|---|---|---|---|---|---|---|---|
| @svgrid/grid | 3.0.5 | MIT | Svelte 5-native runes grid (peer svelte ^5.0.0), not a React shim; Vite 5/6/7; runtime dep esm-env only | Virtualizes rows and columns | — | WAI-ARIA 1.2 grid roles, keyboard, aria-live; old WebViews best-effort | GitHub issues search for “tauri”: no results [S7] |
| @humanspeak/svelte-headless-table | 6.2.0 | MIT | peer svelte ^5.30.0; SvelteKit/SSR-compatible | addVirtualScroll renders visible rows plus a buffer; no worker API documented | Sparse-mode onRangeChange AbortSignal is aborted on a newer range or when the scroll container is destroyed | — | GitHub “tauri” issues: no results [S8] |
| @tanstack/svelte-table | 9.2.4 | MIT | peer svelte ^5.0.0; Svelte 5 adapter over @tanstack/table-core (no React) | Virtualization is a separate rendering strategy via @tanstack/svelte-virtual. Experimental worker plugin offloads row-model stages to a Web Worker; TableWorker.terminate() exists but is not called automatically | — | — | — [S9] |
| @tanstack/svelte-virtual | 3.13.39 | MIT | peer svelte ^3.48.0 \|\| ^4.0.0 \|\| ^5.0.0; store wrapper around virtual-core | Use with the table adapter for windowed rendering | Store subscribe start calls Virtualizer._didMount(); returned cleanup unsubscribes observers and disconnects ResizeObserver | — | virtual-core special-cases iOS WebKit scrollTo during momentum. GitHub TanStack/virtual “tauri” issues: no results [S10] |
| svelte-tably | 1.6.1 | MIT | peer svelte ^5.50.1; depends on runic-reorder | Built-in Virtualization class slices a viewport window; no worker API documented | ResizeObserver actions return destroy() disconnects | Table.svelte sets aria-rowcount / aria-rowindex and some expand/panel ARIA | GitHub “tauri” issues: no results [S11] |

### Code editor (Monaco vs CodeMirror 6)

monaco-editor 0.56.0 (MIT) is framework-agnostic. Vite/ESM integration must implement MonacoEnvironment.getWorker (not getWorkerUrl) so language workers load; language services create web workers, and the editor is not supported in mobile browsers. Editors and models should be disposed: IStandaloneCodeEditor.dispose() and writeScreenReaderContent() exist in the current API. [S13]

CodeMirror 6’s current view package is @codemirror/view 6.43.13 (MIT). EditorView.destroy() removes the element, unregisters handlers, and notifies plugins; the view is then unusable. The content DOM is a textbox (role=textbox, aria-multiline, aria-readonly when read-only) with a visually hidden aria-live=polite announcer, and setTabFocusMode disables Tab / Shift-Tab bindings so focus is not trapped. [S14]

svelte-codemirror-editor 2.1.0 (MIT) targets Svelte 5 runes (v2.x) and peers svelte ^5.0.0 and codemirror ^6.0.0. Vite/SvelteKit needs optimizeDeps.exclude for the wrapper and CodeMirror packages. The component calls view?.destroy() in onDestroy. [S15]

### Unified diffs

@codemirror/merge 6.12.2 (MIT) is the CodeMirror unified/side-by-side diff package: MergeView hosts two EditorViews; unifiedMergeView is an extension that highlights changes against an original document. MergeView.destroy() destroys both editors, cancels measure RAF, and removes the merge DOM. [S16]

@git-diff-view/svelte 0.1.7 (MIT) peers svelte ^5.0.0 and is the kit’s Svelte UI, with split and unified views. @git-diff-view/core 0.1.7 (MIT) documents a worker/server pattern via DiffFile.getBundle() and DiffFile.createInstance(). [S17]

Known Tauri/WebView issues for Monaco are worker-setup and clipboard related: a 2024 Tauri+Vite report showed “Could not create web worker(s)” / missing MonacoEnvironment.getWorkerUrl or getWorker, and a 2025 issue filed a ClipboardService error against a Tauri Monaco reproduction. No equivalent CodeMirror or git-diff-view Tauri bug was found in the inspected primary pages. [S18]

### Terminal (xterm.js)

@xterm/xterm latest stable is 6.0.0 (MIT), with beta 6.1.0-beta.304; the stable package is self-contained, has zero runtime dependencies, and ships an ES module at lib/xterm.mjs. [S19] Call Terminal.dispose() after use (detaches from the DOM, removes listeners; do not reuse). ITerminalOptions includes screenReaderMode (NVDA / VoiceOver) and minimumContrastRatio (WCAG AA/AAA examples) and has no worker or OffscreenCanvas field. [S20]

@xterm/addon-webgl latest stable is 0.19.0 (MIT); call addon.dispose() on WebGL context loss. An open xterm.js bug reports partial-row ghosting with that addon on Tauri WKWebView when allowTransparency and a semi-transparent theme.background are used with @xterm/xterm 6.0. [S21]

@battlefieldduck/xterm-svelte 2.3.0 (MIT) peers Svelte ^5.55.7, depends on @xterm/xterm ^6.0.0 plus official addons including @xterm/addon-webgl ^0.19.0 and @xterm/addon-fit ^0.11.0, and lists Vite ^8 in its published devDependencies. [S22]

### Command palette

svelte-command-palette 2.0.2 (MIT) peers Svelte ^5.0.0 with no React dependency, and depends on fuse.js, tinykeys, lucide-svelte, and csstype; the package is built with Vite ^5 and @sveltejs/vite-plugin-svelte ^4. [S23]

bits-ui Command is a Svelte 5 command-menu primitive (not a React library) with ARIA attributes, keyboard navigation, grouping, and a Dialog-modal recipe. [S24]

## Sources
- [S1] "lightweight-charts npm, GitHub README/releases, IChartApi docs, lwc-plugin-accessibility CHANGELOG, lightweight-charts-svelte and svelte-lightweight-charts package.json" — "https://registry.npmjs.org/lightweight-charts/latest ; https://github.com/tradingview/lightweight-charts ; https://github.com/tradingview/lightweight-charts/releases ; https://tradingview.github.io/lightweight-charts/docs/api/interfaces/IChartApi ; https://github.com/tradingview/lightweight-charts/blob/master/packages/lwc-plugin-accessibility/CHANGELOG.md ; https://registry.npmjs.org/lightweight-charts-svelte/latest ; https://raw.githubusercontent.com/trash-and-fire/svelte-lightweight-charts/master/package.json" (independently checked against "lightweight-charts npm, GitHub README/releases, IChartApi docs, lwc-plugin-accessibility CHANGELOG, wrapper package.json/README" — "https://registry.npmjs.org/lightweight-charts/latest")
- [S2] "klinecharts npm, KLineChart README and SKILL.md, klinecharts-demo-svelte README" — "https://registry.npmjs.org/klinecharts/latest ; https://github.com/klinecharts/KLineChart ; https://raw.githubusercontent.com/klinecharts/KLineChart/main/skills/klinecharts/SKILL.md ; https://github.com/anyongjin/klinecharts-demo-svelte" (independently checked against "klinecharts npm 10.0.3, KLineChart README/SKILL.md, official dispose API, klinecharts-demo-svelte" — "https://registry.npmjs.org/klinecharts/latest")
- [S3] "uPlot npm, GitHub README, uPlot.d.ts, svelte-uplot npm" — "https://registry.npmjs.org/uplot/latest ; https://github.com/leeoniya/uPlot ; https://raw.githubusercontent.com/leeoniya/uPlot/master/dist/uPlot.d.ts ; https://registry.npmjs.org/svelte-uplot/latest" (independently checked against "uPlot npm, GitHub README, uPlot.d.ts, svelte-uplot npm/README" — "https://registry.npmjs.org/uplot/latest")
- [S4] "echarts npm, apache/echarts README and 6.1.0 release, ECharts SSR handbook and API" — "https://registry.npmjs.org/echarts/latest ; https://github.com/apache/echarts ; https://github.com/apache/echarts/releases/tag/6.1.0 ; https://echarts.apache.org/handbook/en/how-to/cross-platform/server/ ; https://echarts.apache.org/api.html" (independently checked against "echarts npm 6.1.0, apache/echarts 6.1.0 notes, official init API and SSR handbook" — "https://registry.npmjs.org/echarts/latest")
- [S5] "liveline-svelte npm, GitHub README and LICENSE" — "https://registry.npmjs.org/liveline-svelte/latest ; https://github.com/VastBlast/liveline-svelte ; https://raw.githubusercontent.com/VastBlast/liveline-svelte/main/LICENSE" (independently checked against "liveline-svelte npm, GitHub README/LICENSE, useLivelineEngine.ts" — "https://registry.npmjs.org/liveline-svelte/latest")
- [S6] "layercake npm and CHANGELOG, layerchart npm and GitHub README, Flarecharts GitLab README and npm" — "https://registry.npmjs.org/layercake/latest ; https://raw.githubusercontent.com/mhkeller/layercake/main/CHANGELOG.md ; https://registry.npmjs.org/layerchart/latest ; https://github.com/techniq/layerchart ; https://registry.npmjs.org/@faintshadow/flarecharts/latest ; https://gitlab.com/FaintShadow/flarecharts/-/raw/main/README.md" (independently checked against "layercake/layerchart npm and CHANGELOG/README; Flarecharts npm and GitLab README" — "https://registry.npmjs.org/layercake/latest")
- [S7] "@svgrid/grid npm latest + SvGrid README/docs/LICENSE" — "https://registry.npmjs.org/@svgrid/grid/latest"
- [S8] "@humanspeak/svelte-headless-table npm latest + addVirtualScroll docs" — "https://registry.npmjs.org/@humanspeak/svelte-headless-table/latest" (independently checked against "@humanspeak/svelte-headless-table npm 6.2.0, addVirtualScroll docs, GitHub issues?q=tauri" — "https://registry.npmjs.org/@humanspeak/svelte-headless-table/latest")
- [S9] "@tanstack/svelte-table 9.2.4 registry + worker plugin + virtualization guide" — "https://registry.npmjs.org/@tanstack/svelte-table/latest"
- [S10] "@tanstack/svelte-virtual 3.13.39 + virtual-core lifecycle" — "https://registry.npmjs.org/@tanstack/svelte-virtual/latest" (independently checked against "@tanstack/svelte-virtual 3.13.39 npm, svelte-virtual adapter, virtual-core iOS/lifecycle" — "https://registry.npmjs.org/@tanstack/svelte-virtual/latest")
- [S11] "svelte-tably 1.6.1 registry + Virtualization/Table source" — "https://registry.npmjs.org/svelte-tably/latest"
- [S12] "MIT LICENSE files and npm latest dependency lists" — "https://raw.githubusercontent.com/sv-grid/sv-grid/main/packages/grid/LICENSE" (independently checked against "MIT LICENSE files and npm latest dependency lists for the inspected table packages" — "https://raw.githubusercontent.com/sv-grid/sv-grid/main/packages/grid/LICENSE")
- [S13] "monaco-editor - npm" — "https://www.npmjs.com/package/monaco-editor" (independently checked against "monaco-editor npm, README, integrate-esm.md, IStandaloneCodeEditor typedoc" — "https://registry.npmjs.org/monaco-editor/latest")
- [S14] "@codemirror/view - npm" — "https://www.npmjs.com/package/@codemirror/view" (independently checked against "@codemirror/view 6.43.13 npm and editorview.ts/theme.ts" — "https://www.npmjs.com/package/@codemirror/view")
- [S15] "svelte-codemirror-editor README" — "https://raw.githubusercontent.com/touchifyapp/svelte-codemirror-editor/main/README.md" (independently checked against "svelte-codemirror-editor npm, README, CodeMirror.svelte" — "https://registry.npmjs.org/svelte-codemirror-editor/latest")
- [S16] "@codemirror/merge - npm" — "https://www.npmjs.com/package/@codemirror/merge" (independently checked against "@codemirror/merge 6.12.2 npm, mergeview.ts and unified.ts" — "https://registry.npmjs.org/@codemirror/merge/latest")
- [S17] "@git-diff-view/core - npm" — "https://www.npmjs.com/package/@git-diff-view/core" (independently checked against "@git-diff-view/svelte and @git-diff-view/core npm + LICENSE" — "https://www.npmjs.com/package/@git-diff-view/core")
- [S18] "monaco-editor discussion #4486 (Tauri web workers)" — "https://github.com/microsoft/monaco-editor/discussions/4486" (independently checked against "monaco-editor discussion #4486 and issue #5056; git-diff-view issues?q=tauri" — "https://github.com/microsoft/monaco-editor/discussions/4486")
- [S19] "@xterm/xterm npm registry metadata" — "https://registry.npmjs.org/@xterm/xterm" (independently checked against "@xterm/xterm npm registry metadata and README" — "https://registry.npmjs.org/@xterm/xterm")
- [S20] "xterm.js public typings (xterm.d.ts)" — "https://raw.githubusercontent.com/xtermjs/xterm.js/master/typings/xterm.d.ts"
- [S21] "[webgl] Partial row ghosting with transparent theme background on WKWebView / Tauri" — "https://github.com/xtermjs/xterm.js/issues/5847"
- [S22] "@battlefieldduck/xterm-svelte 2.3.0 npm registry metadata" — "https://registry.npmjs.org/@battlefieldduck/xterm-svelte/latest"
- [S23] "svelte-command-palette 2.0.2 npm registry metadata" — "https://registry.npmjs.org/svelte-command-palette/latest"
- [S24] "Command - Bits UI" — "https://bits-ui.com/docs/components/command"

## Coverage and uncertainty
- "Question 1 uncertainty: No inspected source documented a current, library-specific Tauri/WebView bug for lightweight-charts, klinecharts, uPlot, ECharts, liveline-svelte, LayerCake, LayerChart, or Flarecharts. Related but non-specific: TradingView maintainers said Lightweight Charts can run in a webview with no native desktop port (discussion #762, 2021); a 2026 WebView2/Tauri 2 compositor-tile bug affects page-sized canvas/img after zoom in embedded WebView2 generally (MicrosoftEdge/WebView2Feedback#5642), not a named chart library."
- "Question 1 uncertainty: None of the official READMEs/APIs inspected for lightweight-charts, klinecharts, uPlot, or liveline-svelte document a first-party OffscreenCanvas or dedicated chart Web Worker. Lightweight Charts v5.1.0 data conflation can use the browser Prioritized Task Scheduling API (precomputeConflationPriority), which is not a Worker. ECharts official init has no worker flag; OffscreenCanvas ports are third-party."
- "Question 1 uncertainty: Apache ECharts official option.html#aria did not load in this sitting (site redirected to a docs-index interstitial), so built-in ARIA label generation was not verified from that page. Package exports include ./lib/component/aria, but that is not the same as a documented a11y contract."
- "Question 1 uncertainty: klinecharts has no first-party Svelte 5 component on npm; Svelte usage is documented only as generic init/dispose (or a community SvelteKit demo). Flarecharts extra Attribution terms beyond MIT were not fully read from LICENSE text—only the README label MIT + Attribution."
- "Question 1 uncertainty: uPlot GitHub Releases UI listed 1.6.32 as Latest while the fetched d.ts is from master and may include unreleased APIs; npm latest remains 1.6.32 (14 Mar 2025). LayerChart GitHub Releases page still showed 2.3.1 as Latest while npm latest was 2.5.0—version claims use the npm registry payload."
- "Question 1 uncertainty: Accessibility of canvas OHLC libraries without plugins (klinecharts, uPlot, liveline-svelte drawing surface, Lightweight Charts without lwc-plugin-accessibility) was not specified as WCAG-complete in the inspected primary docs; liveline-svelte only documents forwarding aria-* to the root div."
- "Question 2 uncertainty: No inspected source documents a Tauri WebView2/WKWebView-specific bug for these four libraries; absence of GitHub issue hits is not a compatibility guarantee."
- "Question 2 uncertainty: No inspected @svgrid/grid, @humanspeak/svelte-headless-table, or svelte-tably API documents a Web Worker / off-main-thread row-model path comparable to TanStack’s experimental-worker-plugin."
- "Question 2 uncertainty: No inspected SvGrid page documents an explicit destroy()/dispose() besides Svelte component unmount; SvGridApi is described as valid for the component lifetime via onApiReady."
- "Question 2 uncertainty: svelte-tably’s accessibility surface in Table.svelte is partial (row indices, expand/panel labels) and was not shown to implement a full WAI-ARIA grid pattern like SvGrid."
- "Question 2 uncertainty: @tanstack/svelte-virtual still uses Svelte stores and a Svelte 3/4/5 peer range; official table virtualization examples mix v8 createSvelteTable (writable stores) and v9 createTable (runes)."
- "Question 2 uncertainty: Humanspeak’s marketing site listed v6.2.0 while GitHub package.json snapshots elsewhere showed older 6.0.x; npm registry latest used here is 6.2.0."
- "Question 3 uncertainty: No Apache-2.0 in-browser editor or unified-diff viewer among the inspected current packages; named candidates are MIT (or BSD-3-Clause for @uwu/monaco-svelte, which also peers svelte ^3.48.0 and is not a current Svelte 5 option)."
- "Question 3 uncertainty: Monaco Accessibility Guide wiki pages did not return body text in this session, so integrator steps (ariaLabel, accessibilitySupport: 'on') could not be verified from those pages; only the README link, writeScreenReaderContent, and typedoc option names were inspected."
- "Question 3 uncertainty: svelte-monaco@1.0.4 exists with peer svelte >=4 and monaco-editor >=0.50.0 <1, but its SPDX license was not present in the inspected npm metadata, so it is not claimed as a current MIT Svelte 5 wrapper."
- "Question 3 uncertainty: Inspected git-diff-view and @codemirror/merge docs do not state WCAG/screen-reader guarantees or Tauri WebKit/WebView2 caveats; MergeView revert buttons do set aria-label in source, but that is not a full a11y claim."
- "Question 3 uncertainty: monaco.editor.createDiffEditor / inline unified diff was not confirmed from a successfully fetched typedoc function page, so Monaco is not claimed here as a current unified-diff viewer."
- "Question 3 uncertainty: CodeMirror 6 core packages inspected do not document a built-in language-service worker comparable to Monaco; off-main-thread highlighting would be integrator-owned and was not verified as a shipped option."
- "Question 4 uncertainty: @mateothegreat/svelte5-command-palette latest on npm is 0.0.10 with no license field, 0 weekly downloads, a self-dependency on ^0.0.9, and svelte ^5.0.0-next.264; GitHub has no LICENSE file—so it is not an evidenced current MIT/Apache candidate."
- "Question 4 uncertainty: GitHub Xterm.svelte at the 2.3.0 gitHead (1a1f465) constructs Terminal in onMount via import('@xterm/xterm') and does not call dispose/onDestroy; that unmount behavior is therefore host-managed, not wrapper-guaranteed."
- "Question 4 uncertainty: xterm.js issue #3368 (2021) said the library was \"100% main thread bound\"; later comments on that closed issue were not fully retrieved, so a post-2021 worker implementation is not confirmed beyond the absence of a worker option in current public typings."
- "Question 4 uncertainty: Issue #5818 (closed, milestone 7.0.0) reports Terminal instances leaking after dispose() due to unregistered WebGL cursor-blink timers; whether 6.1.0-beta.304 includes that fix was not verified."
- "Question 4 uncertainty: No Apache-licensed Svelte 5 command-palette package was found. svelte-hypercommands 0.1.6 is MIT with peer svelte 3.x||4.x||5.x on GitHub HEAD, but npm still shows 0.1.6 from about a year ago and GitHub package.json is 0.1.5."
- "Question 4 uncertainty: No inspected source documents Tauri/webview defects specific to svelte-command-palette or bits-ui Command. bits-ui npm latest is 2.19.3 (MIT, peer svelte ^5.33.0) on the registry; that version string is not printed on the Command docs page cited above."
