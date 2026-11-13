// Space check: measures SPACE-RULES.md instead of looking at it.
//
// Run it in any browser tab that has the app open (http://localhost:5174/),
// from the devtools console or the built-in browser's JavaScript tool:
//
//   const m = await import("/src/lib/dev/space-check.js?t=" + Date.now());
//   const r = await m.run();                    // the whole matrix
//   m.table(r.failures)                         // one line per failure
//
// Tools that time out after a few seconds: m.start() runs it in the
// background; read window.__space (progress, then { rows, failures, summary }).
//
// Narrow it with options, e.g. m.run({ sizes: ["1280x720"], data: ["demo"], text: ["larger"] }).
//
// It loads the app in a hidden iframe of the exact window size, so the
// viewport of the tab running it does not matter. Layout is the default one:
// the saved tile layouts in this browser are set aside during the run and put
// back afterwards.
//
// By default it covers the Overview board (this round's scope); pass
// places: ["overview", "trading"] and unitsPage: true to widen it.
// For every widget on the board, every widget opened in its tab (and the
// Units list page when asked) it records: the box height, the height the content
// uses, the largest empty band inside, sideways scroll, and the size mode.
// A case FAILS when
//   - an empty band inside a widget or page is taller than one row: the
//     widget's own typical row (the median height of its visible list rows),
//     and never less than ROW rem,
//   - the board, the page or the document scrolls (content taller than its box,
//     except a widget's own list, which may scroll down inside itself),
//   - anything scrolls sideways,
//   - a navigation pill runs past its column.
// A designed empty state (marked data-empty) is exempt from the band rule.

export const ROW = 3; // rem: one list row with its second line
const SIZES = ["1280x720", "1600x900", "1920x1080"];
const DATA = ["demo", "worst", "first"];
const TEXT = ["standard", "larger"];
const REVIEW = ["on", "off"]; // off = the app alone, edge to edge, as in its desktop window
const TILE_KEYS = ["qmx-desk.tiles.v1", "qmx-desk.tiles.v2"];

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function frameFor(w, h) {
  const f = document.createElement("iframe");
  f.style.cssText = `position:fixed;left:0;top:0;width:${w}px;height:${h}px;border:0;opacity:0;pointer-events:none;z-index:-1`;
  document.body.appendChild(f);
  return f;
}

async function load(f, url) {
  await new Promise((res) => {
    f.onload = res;
    f.src = url;
  });
  const d = f.contentDocument;
  for (let i = 0; i < 60; i++) {
    if (d.querySelector("main")) break;
    await wait(50);
  }
  await settle(f);
}
async function settle(f) {
  // Timers, not animation frames: a hidden tab never runs frames.
  await wait(320);
}

const visible = (el, win) => {
  const s = win.getComputedStyle(el);
  return s.visibility !== "hidden" && s.display !== "none" && parseFloat(s.opacity) > 0.01;
};

// Vertical bands of real content inside `box`, clipped to its visible area.
function bands(box, win) {
  const B = box.getBoundingClientRect();
  const out = [];
  const walk = (el) => {
    if (!visible(el, win)) return;
    const leaf = el.childElementCount === 0 || el.tagName === "svg" || el.tagName === "TABLE" || el.dataset.leaf !== undefined;
    if (leaf) {
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const top = Math.max(r.top, B.top);
      const bot = Math.min(r.bottom, B.bottom);
      if (bot > top && r.right > B.left && r.left < B.right) out.push([top - B.top, bot - B.top]);
      return;
    }
    for (const c of el.children) walk(c);
  };
  for (const c of box.children) walk(c);
  out.sort((a, b) => a[0] - b[0]);
  let gap = 0;
  let at = 0;
  let used = 0;
  for (const [t, b] of out) {
    gap = Math.max(gap, t - at);
    at = Math.max(at, b);
    used = Math.max(used, b);
  }
  gap = Math.max(gap, B.height - at);
  return { height: B.height, used, gap };
}

function sideways(doc, win) {
  const bad = [];
  if (doc.documentElement.scrollWidth > win.innerWidth + 1) bad.push("document");
  for (const el of doc.querySelectorAll("body *")) {
    if (el.scrollWidth <= el.clientWidth + 1) continue;
    const ox = win.getComputedStyle(el).overflowX;
    if (ox === "auto" || ox === "scroll") bad.push(describe(el));
  }
  return bad;
}
const describe = (el) => el.closest("section")?.getAttribute("aria-label") ?? el.className?.toString().slice(0, 40) ?? el.tagName;

// One row of this box: the median height of its visible list rows.
function rowOf(box, win, rem) {
  const hs = [...box.querySelectorAll("li, [role=listitem], tr")]
    .filter((el) => visible(el, win) && el.offsetHeight > 0)
    .map((el) => el.offsetHeight)
    .sort((a, b) => a - b);
  return Math.max(ROW * rem, hs.length ? hs[Math.floor(hs.length / 2)] : 0);
}

const near = [];
function measureWidgets(doc, win, where, ctx, rows, failures) {
  const rem = parseFloat(win.getComputedStyle(doc.documentElement).fontSize);
  for (const sec of doc.querySelectorAll(".board section.frame")) {
    const body = sec.querySelector(":scope > [data-body]") ?? sec.children[1];
    if (!body) continue;
    const name = sec.getAttribute("aria-label");
    const empty = !!body.querySelector("[data-empty]");
    const m = bands(body, win);
    const one = rowOf(body, win, rem);
    const r = {
      ...ctx,
      where,
      widget: name,
      mode: sec.dataset.size ?? "none",
      box: Math.round(m.height),
      used: Math.round(m.used),
      gapRem: +(m.gap / rem).toFixed(1),
      rowRem: +(one / rem).toFixed(1),
      scrollsDown: body.scrollHeight > body.clientHeight + 1,
      empty,
    };
    rows.push(r);
    if (!empty && m.gap > one) failures.push({ ...r, why: `empty band ${r.gapRem}rem > row ${r.rowRem}rem` });
    else if (!empty && m.gap / rem > ROW) near.push({ ...r, why: `band ${r.gapRem}rem: over ${ROW}rem but under its own row ${r.rowRem}rem` });
  }
}

function measureChrome(doc, win, where, ctx, failures) {
  const html = doc.documentElement;
  if (html.scrollHeight > win.innerHeight + 1) failures.push({ ...ctx, where, why: `document taller than window by ${html.scrollHeight - win.innerHeight}px` });
  const board = doc.querySelector(".board .tiles > div");
  if (board && board.scrollHeight > board.clientHeight + 1) failures.push({ ...ctx, where, why: "board scrolls" });
  const main = doc.querySelector("main");
  if (main && main.scrollHeight > main.clientHeight + 1) failures.push({ ...ctx, where, why: "page area overflows" });
  for (const s of sideways(doc, win)) failures.push({ ...ctx, where, why: `scrolls sideways: ${s}` });
  // Navigation never scrolls and never runs past its column.
  for (const nav of doc.querySelectorAll("nav[aria-label='Places'], nav[aria-label='Mini apps']")) {
    const col = nav.parentElement.getBoundingClientRect();
    const r = nav.getBoundingClientRect();
    if (r.bottom > col.bottom + 1 || nav.scrollHeight > nav.clientHeight + 1) failures.push({ ...ctx, where, why: `navigation overflows: ${nav.getAttribute("aria-label")} by ${Math.round(r.bottom - col.bottom)}px` });
  }
}

export async function run({ sizes = SIZES, data = DATA, text = TEXT, review = REVIEW, places = ["overview"], unitsPage = false, tabs = true, origin = location.origin } = {}) {
  const saved = Object.fromEntries(TILE_KEYS.map((k) => [k, localStorage.getItem(k)]));
  TILE_KEYS.forEach((k) => localStorage.removeItem(k));
  const rows = [];
  const failures = [];
  near.length = 0;
  try {
    for (const size of sizes) {
      const [w, h] = size.split("x").map(Number);
      const f = frameFor(w, h);
      try {
        for (const rv of review)
        for (const d of data) {
          for (const t of text) {
            const ctx = { size, review: rv, data: d, text: t };
            if (typeof window !== "undefined" && window.__space?.running) window.__space = { running: true, at: ctx, rows, failures };
            const q = `&data=${d}&text=${t}${rv === "off" ? "&review=off" : ""}`;
            for (const place of places) {
              await load(f, `${origin}/?place=${place}${q}`);
              const doc = f.contentDocument;
              const win = f.contentWindow;
              measureChrome(doc, win, place, ctx, failures);
              measureWidgets(doc, win, place, ctx, rows, failures);
              if (!tabs || d === "first") continue;
              const count = doc.querySelectorAll(".board section.frame").length;
              for (let i = 0; i < count; i++) {
                const sec = doc.querySelectorAll(".board section.frame")[i];
                const name = sec?.getAttribute("aria-label");
                const btn = sec?.querySelector('button[aria-label="Open in a tab"]');
                if (!btn) continue;
                btn.click();
                await settle(f);
                measureChrome(doc, win, `${place} tab: ${name}`, ctx, failures);
                measureWidgets(doc, win, `${place} tab`, ctx, rows, failures);
                // The tab as a page: the widget's frame must reach the page's
                // edges (rule 5); what is inside it is measured above.
                const pageBox = doc.querySelector(".board");
                const frame = pageBox?.querySelector("section.frame");
                if (pageBox && frame) {
                  const rem = parseFloat(win.getComputedStyle(doc.documentElement).fontSize);
                  const P = pageBox.getBoundingClientRect();
                  const F = frame.getBoundingClientRect();
                  const pad = parseFloat(win.getComputedStyle(pageBox).paddingBottom) || 0;
                  const gap = P.bottom - pad - F.bottom;
                  const r = { ...ctx, where: `${place} tab page`, widget: name, mode: "tab", box: Math.round(P.height), used: Math.round(F.height), gapRem: +(gap / rem).toFixed(1), scrollsDown: false, empty: false };
                  rows.push(r);
                  if (gap > 2) failures.push({ ...r, why: `tab page: frame stops ${r.gapRem}rem short of the page` });
                }
                win.dispatchEvent(new win.KeyboardEvent("keydown", { key: "Escape" }));
                await settle(f);
              }
            }
            if (!unitsPage) continue;
            await load(f, `${origin}/?place=units${q}`);
            const doc = f.contentDocument;
            const win = f.contentWindow;
            measureChrome(doc, win, "units list", ctx, failures);
            const list = doc.querySelector("main section.lv > [data-list]") ?? doc.querySelector("main section.lv > div:last-child");
            if (list) {
              const rem = parseFloat(win.getComputedStyle(doc.documentElement).fontSize);
              const empty = !!list.querySelector("[data-empty]");
              const m = bands(list, win);
              const one = rowOf(list, win, rem);
              const r = { ...ctx, where: "units list", widget: "Units page", mode: "page", box: Math.round(m.height), used: Math.round(m.used), gapRem: +(m.gap / rem).toFixed(1), rowRem: +(one / rem).toFixed(1), scrollsDown: list.scrollHeight > list.clientHeight + 1, empty };
              rows.push(r);
              if (!empty && m.gap > one) failures.push({ ...r, why: `empty band ${r.gapRem}rem > row ${r.rowRem}rem` });
            }
          }
        }
      } finally {
        f.remove();
      }
    }
  } finally {
    for (const [k, v] of Object.entries(saved)) if (v !== null) localStorage.setItem(k, v);
  }
  // near: bands over the flat ROW floor that pass only because the widget's
  // own rows are taller. Reported, never hidden.
  return { rows, failures, near: [...near], summary: `${failures.length} failures, ${near.length} near (over ${ROW}rem, under one row), over ${rows.length} measured boxes` };
}

export function start(opts) {
  window.__space = { running: true };
  run(opts).then((r) => (window.__space = r), (e) => (window.__space = { error: String(e) }));
  return "started";
}

export const table = (list) =>
  list.map((x) => `${x.size} review-${x.review} ${x.data} ${x.text} | ${x.where}${x.widget ? ` | ${x.widget} [${x.mode}] box ${x.box}px used ${x.used}px` : ""} | ${x.why}`).join("\n");
