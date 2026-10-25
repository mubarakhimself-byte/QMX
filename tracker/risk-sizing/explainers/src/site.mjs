// Site shell: CSS, navigation, page template, small flat-diagram helpers.
import { readFileSync } from "node:fs";
import { k } from "./parts.mjs";

const KIT_JS = readFileSync(new URL("file:///C:/Users/Mubarak/.claude/skills/anatomy/kit/iso-kit.mjs"), "utf8").replace(/^export /gm, "");
const CLIENT_JS = readFileSync(new URL("./client.js", import.meta.url), "utf8");
export const SITE_JS = KIT_JS + "\n" + CLIENT_JS;

const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
export { esc };

// ---- CSS -------------------------------------------------------------
function kitCss() {
  let css = k.ISO_CSS;
  const darkM = css.match(/\.iso\{([^}]*)\}/);
  const lightM = css.match(/\.iso\[data-theme="light"\]\{([^}]*)\}/);
  css = css.replace(darkM[0], "").replace(lightM[0], "");
  return { dark: darkM[1], light: lightM[1], rules: css };
}
const KC = kitCss();
const DARK = `--bg:#0d0e10;--panel:#141619;--panel-2:#191c20;--line:#2a2e34;--text:#b3b8c0;--strong:#eef0f3;--muted:#7d838c;
--accent:#6cc4ff;--t-found:#a3acb7;--t-proposed:#7fb0ff;--t-open:#f2b65c;--t-improve:#6fd6a2;--ok:#5fd88f;--warn:#f4bb4c;--bad:#ff6f6f;`;
const LIGHT = `--bg:#f2f2ee;--panel:#fbfbf9;--panel-2:#f4f4f1;--line:#d8d8d3;--text:#4a4d53;--strong:#16171a;--muted:#7f838a;
--accent:#0b6fc4;--t-found:#5f6670;--t-proposed:#2a5fd6;--t-open:#a96a07;--t-improve:#1d8552;--ok:#1d9a52;--warn:#c4860a;--bad:#d4353d;`;

export const SITE_CSS = `
/* Layout: one mobile-first column; figures are cards that fill the column; flat diagrams sit between them. */
:root{${KC.dark}${DARK}color-scheme:dark;
--font-display:"Archivo","Segoe UI",system-ui,sans-serif;--font-body:"Archivo","Segoe UI",system-ui,sans-serif;--font-mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
--anatomy-mono:var(--font-mono);--lit-top:color-mix(in srgb,var(--accent) 26%,var(--anatomy-top));--lit-shade:color-mix(in srgb,var(--accent) 16%,var(--anatomy-shade-1))}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){${KC.light}${LIGHT}color-scheme:light}}
:root[data-theme="light"]{${KC.light}${LIGHT}color-scheme:light}
:root[data-theme="dark"]{${KC.dark}${DARK}color-scheme:dark}
${KC.rules}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:15.5px/1.55 var(--font-body);-webkit-font-smoothing:antialiased}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--bg)}
a{color:var(--accent)}
.wrap{max-width:720px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:8px 32px}
.top{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.top-in{max-width:720px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:10px;display:flex;align-items:center;gap:12px}
.brand{font:700 15px/1 var(--font-display);letter-spacing:.01em;color:var(--strong);text-decoration:none;white-space:nowrap}
.brand span{color:var(--muted);font-weight:500}
.menu{margin-left:auto;position:relative}
.menu summary{list-style:none;cursor:pointer;font:600 13px/1 var(--font-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--strong);padding:9px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel)}
.menu summary::-webkit-details-marker{display:none}
.menu[open] summary{border-color:var(--accent)}
.menu nav{position:absolute;right:0;top:calc(100% + 8px);width:min(300px,calc(100vw - 32px));max-height:min(70vh,560px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:6px;box-shadow:0 12px 40px #0006}
.menu nav a{display:flex;gap:10px;align-items:baseline;padding:9px 10px;border-radius:9px;color:var(--text);text-decoration:none}
.menu nav a b{font:600 11px/1 var(--font-mono);color:var(--muted);min-width:22px}
.menu nav a[aria-current]{background:var(--panel-2);color:var(--strong)}
.menu nav a:hover{background:var(--panel-2)}
.eyebrow{font:600 11.5px/1.3 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:22px 0 6px}
.eyebrow .pill{margin-left:6px}
h1{font:800 clamp(28px,7.5vw,40px)/1.05 var(--font-display);letter-spacing:-.015em;color:var(--strong);margin:0 0 10px;text-wrap:balance}
h2{font:750 21px/1.2 var(--font-display);color:var(--strong);margin:34px 0 8px;text-wrap:balance}
h3{font:700 16px/1.3 var(--font-display);color:var(--strong);margin:18px 0 6px}
.lede{font-size:16.5px;color:var(--text);margin:0 0 6px;max-width:60ch}
p{margin:6px 0 10px;max-width:62ch}
.note{font-size:13.5px;color:var(--muted)}
/* figure card */
.fx{margin:18px 0 8px;background:var(--anatomy-card);border:1px solid var(--line);border-radius:16px;overflow:hidden;--anatomy-paper:var(--anatomy-card)}
.fx-head{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;padding:12px 14px 0}
.fx-name{font:600 11px/1.2 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.fx-modes{display:flex;flex-wrap:wrap;gap:4px;background:var(--panel-2);border:1px solid var(--line);border-radius:16px;padding:3px}
.fx-modes button{font:600 12.5px/1 var(--font-body);color:var(--text);background:none;border:0;border-radius:999px;padding:8px 12px;cursor:pointer}
.fx-modes button[aria-pressed="true"]{background:var(--strong);color:var(--bg)}
.fx-stage{padding:4px 6px 0}
.fx-stage svg{display:block;width:100%;height:auto;max-width:560px;margin:0 auto;overflow:visible;touch-action:manipulation}
.fx-bar{border-top:1px solid var(--line);padding:10px 14px 12px;display:grid;gap:8px}
.fx-say{margin:0;min-height:2.9em;font:600 15px/1.4 var(--font-body);color:var(--strong);max-width:none}
.fx-ctl{display:flex;align-items:center;gap:6px}
.fx-ctl button{font:600 13px/1 var(--font-body);color:var(--strong);background:var(--panel-2);border:1px solid var(--line);border-radius:10px;min-width:44px;height:38px;padding:0 12px;cursor:pointer}
.fx-ctl button:focus-visible,.fx-modes button:focus-visible,.chip:focus-visible,.menu summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.fx-ctl [data-step]{margin-left:auto;font:500 12px/1 var(--font-mono);color:var(--muted);font-variant-numeric:tabular-nums}
.fx-dots{display:flex;flex-wrap:wrap;gap:5px}
.fx-dots button{width:22px;height:8px;border-radius:4px;border:0;background:var(--line);padding:0;cursor:pointer}
.fx-dots button.on{background:var(--accent)}
.fx-hint{font:500 11.5px/1.3 var(--font-mono);color:var(--muted);letter-spacing:.03em}
.fx [data-hot]{cursor:pointer}
.fx [data-hot].lit .iso-edge,.fx [data-hot].lit .iso-crease,.fx [data-hot].lit .iso-bevel{stroke:var(--accent)}
.fx [data-hot].lit .iso-top{fill:var(--lit-top)}
.fx [data-hot].lit .iso-shade{fill:var(--lit-shade)}
.fx [data-hot].lit .iso-face-text{fill:var(--accent)}
.fx [data-hot].lit .iso-line[data-tone]{stroke:var(--accent)}
.fx .qx-needle{stroke:var(--accent);stroke-width:1.3}
.fx [data-show]{transition:opacity .45s var(--anatomy-ease)}
.fx [data-show][data-off]{opacity:0;pointer-events:none}
.lamp>.iso-solid:last-child .iso-top,.lamp>.iso-solid:last-child .iso-shade{transition:fill .3s}
${["ok", "warn", "bad"].map((s) => `.fx [data-lamp][data-state="${s}"]>.iso-solid:last-child .iso-top{fill:var(--${s})}
.fx [data-lamp][data-state="${s}"]>.iso-solid:last-child .iso-shade{fill:color-mix(in srgb,var(--${s}) 55%,var(--anatomy-shade-0))}
.fx [data-lamp][data-state="${s}"]>.iso-solid:last-child .iso-edge{stroke:var(--${s})}
.fx [data-lamp][data-state="${s}"]>.iso-solid:last-child{filter:drop-shadow(0 0 3px var(--${s}))}
.fx [data-cls][data-state="${s}"] .iso-top{fill:color-mix(in srgb,var(--${s}) 40%,var(--anatomy-top))}
.fx [data-cls][data-state="${s}"] .iso-shade{fill:color-mix(in srgb,var(--${s}) 25%,var(--anatomy-shade-1))}
.fx [data-cls][data-state="${s}"] .iso-edge{stroke:var(--${s})}
.fx [data-cls][data-state="${s}"] .iso-face-text{fill:var(--${s})}`).join("\n")}
.fx [data-cls][data-state="dim"]{opacity:.28}
.fx [data-cls]{transition:opacity .4s}
/* chips */
.chips{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:6px}
.chip{display:flex;gap:10px;align-items:baseline;padding:9px 12px;border:1px solid var(--line);border-radius:12px;background:var(--panel);font-size:14.5px;line-height:1.4;color:var(--text)}
.chip[data-for]{cursor:pointer}
.chip.lit{border-color:var(--accent);color:var(--strong)}
.pill{flex:none;display:inline-block;font:700 10px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;padding:4px 6px 3px;border-radius:5px;border:1px solid currentColor;min-width:74px;text-align:center}
.pill[data-tag="found"]{color:var(--t-found)}
.pill[data-tag="proposed"]{color:var(--t-proposed)}
.pill[data-tag="open"]{color:var(--t-open)}
.pill[data-tag="improve"]{color:var(--t-improve)}
.chip b{color:var(--strong);font-weight:650}
/* flat diagrams */
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px;margin:14px 0}
.panel h3{margin-top:0}
.bars{display:grid;gap:9px}
.bar{display:grid;grid-template-columns:minmax(84px,34%) 1fr auto;gap:10px;align-items:center;font-size:14px}
.bar .lbl{color:var(--strong);min-width:0}
.bar .trk{height:12px;border-radius:6px;background:var(--panel-2);border:1px solid var(--line);overflow:hidden}
.bar .fil{height:100%;background:var(--accent);border-radius:6px}
.bar .fil[data-c="ok"]{background:var(--ok)}.bar .fil[data-c="warn"]{background:var(--warn)}.bar .fil[data-c="bad"]{background:var(--bad)}.bar .fil[data-c="mute"]{background:var(--muted)}
.bar .val{font:600 13px/1 var(--font-mono);color:var(--strong);font-variant-numeric:tabular-nums}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.flow .st{padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--panel-2);font:600 13px/1.2 var(--font-body);color:var(--strong)}
.flow .st small{display:block;font:500 11px/1.3 var(--font-mono);color:var(--muted);margin-top:2px}
.flow .ar{color:var(--muted);font:600 14px/1 var(--font-mono)}
.flow .st[data-c="qmb"]{border-color:color-mix(in srgb,var(--t-proposed) 60%,var(--line))}
.flow .st[data-c="node"]{border-color:color-mix(in srgb,var(--t-improve) 60%,var(--line))}
.flow .st[data-c="you"]{border-color:color-mix(in srgb,var(--t-open) 70%,var(--line))}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:8px}
.card{border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--panel-2);min-width:0}
.card .k{font:600 10.5px/1.2 var(--font-mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.card .v{font:700 17px/1.25 var(--font-display);color:var(--strong);margin:3px 0}
.card p{font-size:13.5px;margin:2px 0 0}
.tbl{overflow-x:auto;margin:6px -2px 0}
.tbl table{width:100%;border-collapse:collapse;font-size:13.5px;min-width:320px}
.tbl th{font:600 10.5px/1.2 var(--font-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);text-align:left;padding:6px 6px;border-bottom:1px solid var(--line)}
.tbl td{padding:7px 6px;border-bottom:1px solid var(--line);vertical-align:top;color:var(--text)}
.tbl td:first-child{color:var(--strong);font-weight:600}
.y,.n,.h{font:700 13px/1 var(--font-mono)}
.y{color:var(--ok)}.n{color:var(--bad)}.h{color:var(--warn)}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;font-size:12.5px;color:var(--muted);align-items:center}
.legend .pill{min-width:0}
/* hub list */
.pages{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:8px;margin-top:10px}
.pages a{display:block;text-decoration:none;border:1px solid var(--line);background:var(--panel);border-radius:14px;padding:12px 14px;color:var(--text)}
.pages a:hover{border-color:var(--accent)}
.pages a b{display:block;font:700 16px/1.25 var(--font-display);color:var(--strong)}
.pages a i{font:600 10.5px/1 var(--font-mono);font-style:normal;color:var(--muted);letter-spacing:.06em}
.pages a span{display:block;font-size:13.5px;margin-top:3px}
/* questions */
.qa{border:1px solid var(--line);border-radius:14px;background:var(--panel);margin:10px 0;overflow:hidden}
.qa summary{cursor:pointer;list-style:none;padding:13px 14px;display:flex;gap:12px;align-items:baseline}
.qa summary::-webkit-details-marker{display:none}
.qa summary .n{font:700 13px/1 var(--font-mono);color:var(--t-open);min-width:22px}
.qa summary b{font:700 16.5px/1.3 var(--font-display);color:var(--strong)}
.qa .body{padding:0 14px 14px 48px}
.qa .rec{border-left:3px solid var(--t-proposed);padding:6px 0 6px 12px;margin:8px 0;color:var(--strong)}
.qa .rec em{font:700 10.5px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--t-proposed);font-style:normal;display:block;margin-bottom:4px}
@media (max-width:480px){.qa .body{padding-left:14px}}
/* prev/next */
.pn{max-width:720px;margin:10px auto 0;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 40px;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.pn a{border:1px solid var(--line);border-radius:14px;padding:12px 14px;text-decoration:none;background:var(--panel);min-width:0}
.pn a small{display:block;font:600 10.5px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.pn a span{font:700 15px/1.25 var(--font-display);color:var(--strong)}
.pn a.next{text-align:right;grid-column:2}
.foot{max-width:720px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 48px;font-size:12.5px;color:var(--muted)}

.tree{display:grid;gap:10px}
.tnode{border:1px solid var(--line);border-radius:12px;background:var(--panel-2);padding:9px 12px;min-width:0}
.tnode b{display:block;font:700 15px/1.25 var(--font-display);color:var(--strong)}
.tnode small{display:block;font:500 12px/1.3 var(--font-mono);color:var(--muted);margin-top:2px}
.tnode.root{border-color:var(--accent)}
.tkids{display:grid;gap:8px;padding-left:16px;border-left:2px solid var(--line);margin-left:12px}
.tgroup{display:grid;gap:6px;border:1px dashed color-mix(in srgb,var(--t-proposed) 70%,var(--line));border-radius:14px;padding:8px}
.tlabel{font-size:12.5px;color:var(--text);display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.nrows{display:grid;gap:8px}
.nrow{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:center;border:1px solid var(--line);border-radius:12px;padding:9px 12px;background:var(--panel-2)}
.nwhen{font-size:14px;color:var(--text);min-width:0}
.nar{color:var(--accent);font:700 16px/1 var(--font-mono)}
.nwhat{min-width:0}.nwhat b{display:block;font:700 15px/1.2 var(--font-display);color:var(--strong)}.nwhat small{display:block;font-size:12.5px;color:var(--muted)}
.span3{display:grid;grid-template-columns:2fr 3fr 2fr;gap:4px}
.span3 span{border-radius:8px;padding:10px 8px;font:700 13.5px/1.2 var(--font-display);color:var(--strong);border:1px solid var(--line);min-width:0}
.span3 span small{display:block;font:500 11px/1.3 var(--font-mono);color:var(--muted);margin-top:3px}
.span3 [data-c=ok]{background:color-mix(in srgb,var(--ok) 18%,var(--panel))}.span3 [data-c=warn]{background:color-mix(in srgb,var(--warn) 18%,var(--panel))}.span3 [data-c=bad]{background:color-mix(in srgb,var(--bad) 18%,var(--panel))}
.cloud{display:flex;flex-wrap:wrap;gap:6px}
.cloud span{font:600 12.5px/1 var(--font-mono);padding:7px 9px;border-radius:8px;background:var(--panel-2);border:1px solid var(--line);color:var(--text)}
.clash{display:grid;gap:10px;margin-top:14px}
.cl{display:grid;gap:4px;border:1px solid var(--line);border-radius:14px;padding:10px 12px;background:var(--panel)}
.cl em{display:block;font:700 10px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;font-style:normal;margin-bottom:4px}
.cl .old{color:var(--text);text-decoration:line-through;text-decoration-color:color-mix(in srgb,var(--bad) 70%,transparent)}
.cl .old em{color:var(--bad);text-decoration:none;display:block}
.cl .new{color:var(--strong);font-weight:600}.cl .new em{color:var(--t-proposed)}
.cl .arrow{color:var(--muted);font:700 14px/1 var(--font-mono)}
ol.steps{margin:0;padding:0;list-style:none;counter-reset:s;display:grid;gap:6px}
ol.steps li{counter-increment:s;display:flex;gap:10px;align-items:baseline;padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:var(--panel-2);cursor:pointer}
ol.steps li::before{content:counter(s);font:700 12px/1 var(--font-mono);color:var(--accent);min-width:20px}
ol.steps li b{font-weight:600;color:var(--strong);flex:1;min-width:0}
ol.steps li.lit{border-color:var(--accent)}
.sz{font:600 11px/1 var(--font-mono);color:var(--muted)}
@media (max-width:420px){.nrow{grid-template-columns:1fr;gap:4px}.nar{transform:rotate(90deg);width:max-content}}
@media (prefers-reduced-motion: reduce){.fx [data-show],.fx [data-cls]{transition:none}}
`;

// ---- pages ---------------------------------------------------------------
export const PAGES = [
  { file: "index.html", name: "The whole system", short: "Hub", blurb: "One bench, every part. Tap a part to open its page." },
  { file: "unit.html", name: "The unit", short: "Unit", blurb: "One complete trading algorithm, and the three things outside it." },
  { file: "lifecycle.html", name: "A unit's life", short: "Lifecycle", blurb: "From idea to live, the family of siblings, and when something is new." },
  { file: "journal.html", name: "The journal", short: "Journal", blurb: "One journal per unit. Who writes which part." },
  { file: "testing.html", name: "Testing in QMB", short: "Testing", blurb: "What QMB has today, what is missing, and the small test set." },
  { file: "judging.html", name: "Judging fairly", short: "Judging", blurb: "Counting tries, sealed months, enough trades: the maths in pictures." },
  { file: "sizing.html", name: "Risk and sizing", short: "Sizing", blurb: "Shrink fast, grow back on evidence, the floor that only rises." },
  { file: "decay.html", name: "Fast stops, slow checks", short: "Decay", blurb: "Loss points act today. The nightly check spots a dying edge." },
  { file: "router.html", name: "The router", short: "Router", blurb: "A planner on the PC, a cheap gate on the node, and what happens offline." },
  { file: "instruments.html", name: "Markets and gaps", short: "Markets", blurb: "What each market type needs, and what the backend lacks." },
  { file: "library.html", name: "The unit library", short: "Library", blurb: "QML upgraded: six verbs, two files, the hard parts hidden." },
  { file: "old-rules.html", name: "Old rules in the way", short: "Old rules", blurb: "Written rules that clash with the new design." },
  { file: "build-path.html", name: "Build order", short: "Build order", blurb: "Ten foundations, ending with one unit on the cTrader demo." },
  { file: "questions.html", name: "Your 8 questions", short: "Questions", blurb: "Each with a recommended answer. Yes accepts it." },
];

export const pill = (tag) => `<span class="pill" data-tag="${tag}">${tag}</span>`;
export function chips(figId, items) {
  return `<ul class="chips">${items.map(([tag, text, part]) => `<li class="chip"${part ? ` data-fig="${figId}" data-for="${part}" tabindex="0"` : ""}>${pill(tag)}<span>${text}</span></li>`).join("")}</ul>`;
}
export function figCard({ id, name, svg, modes, hint = "Tap a part · use the arrows to step" }) {
  const modeBtns = modes ? `<div class="fx-modes" role="group" aria-label="View">${modes.map(([m, label], i) => `<button type="button" data-mode="${m}" aria-pressed="${i === 0}">${label}</button>`).join("")}</div>` : "";
  return `<figure class="fx" id="${id}"><div class="fx-head"><span class="fx-name">${esc(name)}</span>${modeBtns}</div><div class="fx-stage">${svg}</div><div class="fx-bar"><p class="fx-say" data-say aria-live="polite"></p><div class="fx-ctl"><button type="button" data-act="prev" aria-label="Previous step">&#8249;</button><button type="button" data-act="play" aria-pressed="true">Pause</button><button type="button" data-act="next" aria-label="Next step">&#8250;</button><span data-step></span></div><div class="fx-dots" data-dots></div><span class="fx-hint">${esc(hint)}</span></div></figure>`;
}
export function bars(rows) {
  return `<div class="bars">${rows.map((r) => `<div class="bar"><span class="lbl">${r.label}</span><span class="trk"><span class="fil" data-c="${r.c || ""}" style="width:${Math.max(1.5, (r.value / r.max) * 100).toFixed(1)}%"></span></span><span class="val">${r.text ?? r.value}</span></div>`).join("")}</div>`;
}
export function flow(steps) {
  return `<div class="flow">${steps.map((s, i) => `${i ? '<span class="ar">&rarr;</span>' : ""}<span class="st"${s.c ? ` data-c="${s.c}"` : ""}>${s.t}${s.s ? `<small>${s.s}</small>` : ""}</span>`).join("")}</div>`;
}
export function cards(list) {
  return `<div class="cards">${list.map((c) => `<div class="card">${c.k ? `<div class="k">${c.k}</div>` : ""}<div class="v">${c.v}</div>${c.p ? `<p>${c.p}</p>` : ""}</div>`).join("")}</div>`;
}
export function table(head, rows) {
  return `<div class="tbl"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
export const Y = '<span class="y" title="yes">YES</span>', N = '<span class="n" title="no">NO</span>', H = '<span class="h" title="partly">PART</span>';

const FONTS = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600;700&display=swap">`;

export function pageHtml(page, { body, script = "", full }) {
  const i = PAGES.findIndex((p) => p.file === page.file);
  const prev = PAGES[i - 1], next = PAGES[i + 1];
  const title = page.file === "index.html" ? "QMX unit system" : `${page.name} · QMX`;
  const nav = PAGES.map((p, j) => `<a href="${p.file}"${j === i ? ' aria-current="page"' : ""}><b>${j === 0 ? "&#8962;" : String(j).padStart(2, "0")}</b>${esc(p.name)}</a>`).join("");
  const head = `<title>${esc(title)}</title><meta name="claude:viewport-fit-sides" content="cover">${FONTS}<link rel="stylesheet" href="site.css">`;
  const content = `<header class="top"><div class="top-in"><a class="brand" href="index.html">QMX <span>unit system</span></a><details class="menu"><summary>Pages</summary><nav aria-label="All pages">${nav}</nav></details></div></header>
<main class="wrap">${body}</main>
<nav class="pn" aria-label="Previous and next page">${prev ? `<a class="prev" href="${prev.file}"><small>&larr; Previous</small><span>${esc(prev.name)}</span></a>` : ""}${next ? `<a class="next" href="${next.file}"><small>Next &rarr;</small><span>${esc(next.name)}</span></a>` : ""}</nav>
<div class="foot"><div class="legend">${pill("found")} in code or docs today ${pill("proposed")} recommended, not agreed ${pill("open")} needs your call ${pill("improve")} fix or upgrade</div><p>Everything here is a proposal from the research of 24 and 25 October. Nothing is agreed. Every number is a configurable starting value.</p></div>
<script src="site.js"></script>${script ? `<script>${script}</script>` : ""}`;
  if (!full) return head + content;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">${head}</head><body>${content}</body></html>`;
}

export function figScript(id, fig) {
  const { P, dials, labels, modes, init, ease, extra, mode } = fig;
  return `QX.figure({id:${JSON.stringify(id)},P:${JSON.stringify(P)},dials:${JSON.stringify(dials || {})},labels:${JSON.stringify(labels || {})},init:${JSON.stringify(init || {})},ease:${ease || 0.35},${mode ? `mode:${JSON.stringify(mode)},` : ""}modes:${modes},${extra || ""}});`;
}
