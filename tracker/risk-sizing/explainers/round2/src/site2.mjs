// Round 2 site shell. Reuses round 1's CSS, figure runner and flat helpers; adds its own page list, footer and a few blocks.
import { SITE_CSS as CSS1, SITE_JS, pill, chips, figCard, bars, flow, cards, table, figScript, esc } from "../../src/site.mjs";

export { SITE_JS, pill, chips, figCard, bars, flow, cards, table, figScript, esc };

export const ROUND1 = "https://claude.ai/artifact/CXKb3w5rsfm1zcUeNP7BXN";

export const PAGES = [
  { file: "index.html", name: "Round 2 at a glance", short: "Hub", blurb: "What changed since round 1, on one bench." },
  { file: "envelope.html", name: "The admission envelope", short: "Envelope", blurb: "Your click admits a unit with its markets, sessions and brokers." },
  { file: "router.html", name: "The router directs", short: "Router", blurb: "A load balancer that offers, never switches. Try the algorithms." },
  { file: "independence.html", name: "Units stand alone", short: "Independence", blurb: "Unplug the router, the PC or a feed: what a unit keeps." },
  { file: "feeds.html", name: "The feed pool", short: "Feeds", blurb: "One keeper per broker connection, fanning out to 200+ units." },
  { file: "journals.html", name: "Journals and logs", short: "Journals", blurb: "Four streams, one writer each, one id from source to trade." },
  { file: "ideas.html", name: "Ideas and lineage", short: "Ideas", blurb: "Where every unit came from, and moving parts between families." },
  { file: "data.html", name: "Data and lookback", short: "Data", blurb: "The memory bug behind the limit, and how far back data goes." },
  { file: "guard-pod.html", name: "Guard and pod", short: "Guard + pod", blurb: "Three shapes side by side, and what a copilot edit can reach." },
  { file: "papers.html", name: "Papers and the gold mine", short: "Papers", blurb: "What 8 papers and the old Hermes sessions add." },
  { file: "questions.html", name: "Your 8 questions", short: "Questions", blurb: "Each explained first, with its options. No answer picked." },
];

const EXTRA_CSS = `
/* round 2 additions */
.opts{display:grid;gap:8px}
.opt{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--panel-2);min-width:0}
.opt>i{grid-row:span 2;font:700 15px/1 var(--font-mono);font-style:normal;color:var(--t-open);width:26px;height:26px;border:1px solid currentColor;border-radius:8px;display:grid;place-items:center}
.opt b{font:700 15px/1.3 var(--font-display);color:var(--strong)}
.opt span{font-size:13.5px;color:var(--text);min-width:0}
.opt.lean{border-color:color-mix(in srgb,var(--t-open) 60%,var(--line))}
.opt.lean b::after{content:"your lean";margin-left:8px;font:700 9.5px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--t-open);border:1px solid currentColor;border-radius:5px;padding:2px 5px;vertical-align:2px}
.changes{display:grid;gap:8px;counter-reset:c}
.chg{display:grid;grid-template-columns:auto 1fr;gap:2px 12px;align-items:baseline;border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:10px 12px;cursor:pointer;text-decoration:none;color:var(--text)}
.chg::before{counter-increment:c;content:counter(c);grid-row:span 2;font:700 13px/1 var(--font-mono);color:var(--accent)}
.chg b{font:700 15.5px/1.3 var(--font-display);color:var(--strong)}
.chg small{font-size:13px;color:var(--muted)}
.chg.lit{border-color:var(--accent)}
.was{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.was>div{border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--panel-2);min-width:0}
.was em{display:block;font:700 10px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;font-style:normal;margin-bottom:5px}
.was .r1 em{color:var(--muted)}.was .r2 em{color:var(--t-proposed)}
.was .r1{color:var(--muted)}.was .r2{color:var(--strong)}
@media (max-width:420px){.was{grid-template-columns:1fr}}
.round1{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;border:1px dashed var(--line);border-radius:14px;padding:12px 14px;margin:14px 0;text-decoration:none;color:var(--text);background:var(--panel)}
.round1 b{font:700 15px/1.3 var(--font-display);color:var(--strong);display:block}
.round1 span.go{font:600 12px/1 var(--font-mono);color:var(--accent);letter-spacing:.06em;text-transform:uppercase}
.banner{border:1px solid color-mix(in srgb,var(--t-open) 55%,var(--line));background:color-mix(in srgb,var(--t-open) 8%,var(--panel));border-radius:14px;padding:12px 14px;margin:14px 0;color:var(--strong);font-weight:600}
.banner small{display:block;font-weight:400;color:var(--text);margin-top:4px;font-size:13.5px}
/* envelope builder */
.eb{display:grid;gap:12px}
.eb fieldset{border:1px solid var(--line);border-radius:12px;padding:8px 10px 10px;margin:0;min-width:0}
.eb legend{font:600 10.5px/1 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:0 4px}
.ticks{display:flex;flex-wrap:wrap;gap:6px}
.ticks label{display:inline-flex;gap:6px;align-items:center;border:1px solid var(--line);border-radius:999px;padding:7px 11px;background:var(--panel-2);font:600 13px/1 var(--font-body);color:var(--text);cursor:pointer;min-height:36px}
.ticks label:has(input:checked){border-color:var(--accent);color:var(--strong)}
.ticks input{accent-color:var(--accent);margin:0}
.ticks label.home{border-style:dashed}
.offers{display:grid;gap:6px}
.offers button{display:flex;justify-content:space-between;gap:10px;align-items:center;text-align:left;font:600 14px/1.3 var(--font-body);color:var(--strong);background:var(--panel-2);border:1px solid var(--line);border-radius:12px;padding:10px 12px;cursor:pointer;min-height:44px}
.offers button small{font:500 11px/1.2 var(--font-mono);color:var(--muted)}
.offers button[aria-pressed="true"]{border-color:var(--accent)}
.verdict{border-radius:12px;padding:12px 14px;border:1px solid var(--line);background:var(--panel-2);min-height:72px}
.verdict b{display:block;font:700 16px/1.3 var(--font-display);margin-bottom:3px}
.verdict[data-v="in"] b{color:var(--ok)}.verdict[data-v="out"] b{color:var(--warn)}
.verdict p{margin:0;font-size:14px}
.algo{display:flex;flex-wrap:wrap;gap:6px}
.algo span{font:600 12.5px/1 var(--font-body);padding:8px 10px;border-radius:999px;border:1px solid var(--line);background:var(--panel-2);color:var(--strong)}
.algo span[data-k="weak"]{color:var(--muted)}
.mock{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr);gap:10px}
@media (max-width:520px){.mock{grid-template-columns:1fr}}
.mk{border:1px solid var(--line);border-radius:12px;background:var(--panel-2);padding:10px 12px;min-width:0}
.mk .k{font:600 10px/1.2 var(--font-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.mk h4{margin:4px 0 6px;font:700 15px/1.25 var(--font-display);color:var(--strong)}
.mk dl{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;margin:0;font-size:12.5px}
.mk dt{color:var(--muted)}.mk dd{margin:0;color:var(--strong);min-width:0}
.mk .tabs{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.mk .tabs span{font:600 11px/1 var(--font-mono);padding:6px 7px;border-radius:6px;border:1px solid var(--line);color:var(--text)}
.mk .tabs span:first-child{border-color:var(--accent);color:var(--strong)}
.spark{display:block;width:100%;height:28px;margin-top:6px}
.yr{display:grid;gap:7px}
.yr .row{display:grid;grid-template-columns:minmax(92px,30%) 1fr;gap:10px;align-items:center;font-size:13px}
.yr .row>span:first-child{color:var(--strong);min-width:0}
.yr .trk{position:relative;height:14px;border-radius:4px;background:var(--panel-2);border:1px solid var(--line)}
.yr .fil{position:absolute;top:0;bottom:0;right:0;border-radius:3px;background:var(--accent)}
.yr .fil[data-c="day"]{background:color-mix(in srgb,var(--accent) 35%,var(--panel-2))}
.yr .fil[data-c="paid"]{background:var(--t-open)}
.yr .fil i{position:absolute;left:4px;top:50%;transform:translateY(-50%);font:600 10px/1 var(--font-mono);font-style:normal;color:var(--bg)}
.yr .fil[data-c="day"] i{color:var(--strong)}
.yr .axis{display:grid;grid-template-columns:minmax(92px,30%) 1fr;gap:10px;font:500 10.5px/1 var(--font-mono);color:var(--muted)}
.yr .axis div{display:block}
.yr .mark{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--t-open)}
.loop{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:6px;counter-reset:l}
.loop div{counter-increment:l;border:1px solid var(--line);border-radius:10px;padding:8px 10px;background:var(--panel-2);font-size:13px;min-width:0}
.loop div::before{content:counter(l);font:700 11px/1 var(--font-mono);color:var(--accent);display:block;margin-bottom:3px}
.loop div b{display:block;color:var(--strong);font:700 14px/1.25 var(--font-display)}
.qa .body h4{font:700 13px/1.2 var(--font-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:14px 0 6px}
.qa .why{color:var(--text);font-size:14.5px}
.qa .see{font-size:13px;color:var(--muted)}
`;

export const SITE_CSS = CSS1 + EXTRA_CSS;

const FONTS = `<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600;700&display=swap">`;

export const head = (page, tag, lede) => {
  const n = PAGES.findIndex((p) => p.file === page.file);
  return `<p class="eyebrow">Round 2 · ${n ? String(n).padStart(2, "0") + " · " : ""}${page.short}${tag ? " " + pill(tag) : ""}</p><h1>${page.name}</h1><p class="lede">${lede}</p>`;
};
export const panel = (title, html) => `<section class="panel">${title ? `<h3>${title}</h3>` : ""}${html}</section>`;
export const opts = (list) => `<div class="opts">${list.map(([l, t, p, lean]) => `<div class="opt${lean ? " lean" : ""}"><i>${l}</i><b>${t}</b><span>${p}</span></div>`).join("")}</div>`;
export const was = (a, b) => `<div class="was"><div class="r1"><em>Round 1 said</em>${a}</div><div class="r2"><em>Round 2 option</em>${b}</div></div>`;

export function pageHtml(page, { body, script = "", full }) {
  const i = PAGES.findIndex((p) => p.file === page.file);
  const prev = PAGES[i - 1], next = PAGES[i + 1];
  const title = page.file === "index.html" ? "QMX unit system: round 2" : `${page.name} · QMX round 2`;
  const nav = PAGES.map((p, j) => `<a href="${p.file}"${j === i ? ' aria-current="page"' : ""}><b>${j === 0 ? "&#8962;" : String(j).padStart(2, "0")}</b>${esc(p.name)}</a>`).join("") + `<a href="${ROUND1}" target="_blank" rel="noopener"><b>R1</b>Round 1 site</a>`;
  const headTags = `<title>${esc(title)}</title><meta name="claude:viewport-fit-sides" content="cover">${FONTS}<link rel="stylesheet" href="site.css">`;
  const content = `<header class="top"><div class="top-in"><a class="brand" href="index.html">QMX <span>unit system · round 2</span></a><details class="menu"><summary>Pages</summary><nav aria-label="All pages">${nav}</nav></details></div></header>
<main class="wrap">${body}</main>
<nav class="pn" aria-label="Previous and next page">${prev ? `<a class="prev" href="${prev.file}"><small>&larr; Previous</small><span>${esc(prev.name)}</span></a>` : ""}${next ? `<a class="next" href="${next.file}"><small>Next &rarr;</small><span>${esc(next.name)}</span></a>` : ""}</nav>
<div class="foot"><div class="legend">${pill("found")} in code or docs today ${pill("proposed")} an option, not agreed ${pill("open")} needs your call ${pill("improve")} fix or upgrade</div><p>Round 2: options from the research and studies of 27 October, after your review. Nothing here is decided or folded into the architecture. Every number is a configurable starting value.</p></div>
<script src="site.js"></script>${script ? `<script>${script}</script>` : ""}`;
  if (!full) return headTags + content;
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">${headTags}</head><body>${content}</body></html>`;
}

// scenes: plain objects -> the literal QX expects
export const modesOf = (obj) => JSON.stringify(obj);
