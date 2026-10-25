import { PAGES, pill, chips, figCard, bars, flow, cards, table, figScript, Y, N, H } from "./site.mjs";
import { unitFig } from "./fig-unit.mjs";

export const head = (page, tag, lede) => {
  const n = PAGES.findIndex((p) => p.file === page.file);
  return `<p class="eyebrow">${n ? String(n).padStart(2, "0") + " · " : ""}${page.short}${tag ? " " + pill(tag) : ""}</p><h1>${page.name}</h1><p class="lede">${lede}</p>`;
};
export const panel = (title, html) => `<section class="panel">${title ? `<h3>${title}</h3>` : ""}${html}</section>`;

export const CONTENT = {};

CONTENT["unit.html"] = (page) => {
  const f = unitFig();
  const body = [
    head(page, "proposed", "One complete trading algorithm. It replaces the trading bot, and it is tested and traded as one piece."),
    figCard({ id: "fig-unit", name: "Fig 1 · A unit in its pod", svg: f.svg }),
    chips("fig-unit", [
      ["proposed", "<b>Entry and exits</b> live inside the unit", "entry"],
      ["proposed", "<b>Size</b> calibrates itself from its own journal", "size"],
      ["proposed", "<b>Needs</b>: the conditions the router must see", "needs"],
      ["proposed", "<b>Session profile</b>, learned in stress and paper", "sessions"],
      ["proposed", "<b>Exam baseline</b>: what live is judged against", "exam"],
      ["proposed", "<b>One journal</b> per unit", "journal"],
    ]),
    `<h2>What one unit can do</h2>`,
    cards([
      { k: "Trade", v: "Its own way", p: "Entry, exits and safety exits ship as one." },
      { k: "Size", v: "Itself", p: "Shrinks fast after losses, grows back on fresh evidence." },
      { k: "Time", v: "Pick its sessions", p: "Weights sessions, e.g. Tokyo 70 / London 20 / NY 10." },
      { k: "Markets", v: "State its needs", p: "Spread, volatility and news limits it needs before it fits." },
      { k: "Trust", v: "Judge itself", p: "Live behaviour vs its own exam, not one number for every bot." },
      { k: "Memory", v: "One journal", p: "Backtest, stress, paper and live in one place." },
    ]),
    `<h2>The model it copies</h2>`,
    panel("MT5 Wizard: three modules, one EA", flow([{ t: "Signal" }, { t: "Trailing" }, { t: "Money" }, { t: "One EA", s: "ships as one" }]) + `<p class="note" style="margin-top:10px">QMX difference: the money part calibrates itself from the unit's journal.</p>`),
    `<h2>Outside the unit: only three things</h2>`,
    figCardNote(),
    cards([
      { k: "1 · Account guard", v: "Stops. Never resizes.", p: "Kill line, daily budget, news windows, kill switch, venue rules." },
      { k: "2 · Pod", v: "Shares one budget", p: "A group of units. Limits units that are really the same bet." },
      { k: "3 · Router", v: "Switches on and off", p: "Which units run where and when. Never how they trade." },
    ]),
    `<h2>Today and conflicts</h2>`,
    chips("fig-unit", [
      ["found", "The Library already has <b>unit, bot and pod kinds</b>, with empty fields", "unit"],
      ["found", "Docs still say <b>the bot never sizes</b> and <b>the Book owns exits</b>", "size"],
      ["improve", "Rewrite those docs after the design is agreed", null],
      ["found", "The 13 Oct four-part formula was Claude's baseline, <b>never agreed</b>", null],
      ["open", "Keep the word <b>unit</b>? Question 6", null],
    ]),
  ].join("");
  return { body, script: figScript("fig-unit", f) };
};
function figCardNote() { return ""; }

import { hubFig } from "./fig-hub.mjs";
CONTENT["index.html"] = (page) => {
  const f = hubFig();
  const list = PAGES.slice(1).map((p, i) => `<a href="${p.file}"><i>${String(i + 1).padStart(2, "0")}</i><b>${p.name}</b><span>${p.blurb}</span></a>`).join("");
  const body = [
    `<p class="eyebrow">Unit system · ${pill("proposed")}</p><h1>QMX unit system</h1><p class="lede">A picture tour of the converged design. Each unit is one complete trading algorithm; everything else only tests it, places it or stops it.</p>`,
    figCard({ id: "fig-hub", name: "The whole bench", svg: f.svg, hint: "Tap a part to open its page" }),
    panel("The guiding line", `<p style="font:700 19px/1.35 var(--font-display);color:var(--strong);margin:0">When making strategies is nearly free, judging them is the product.</p><p class="note">QMX is your own platform, so effort goes into honest judging and simple machinery.</p>`),
    `<h2>Pages</h2><div class="pages">${list}</div>`,
    panel("Where it stands", chips("fig-hub", [
      ["found", "Research done: 304 ideas funnelled into one shape", null],
      ["open", "Paused by you on 25 Oct: a deeper talk comes first", null],
      ["open", "Then your 8 questions, planning, architecture, PRs", null],
    ])),
  ].join("");
  return { body, script: figScript("fig-hub", f) };
};
