import { bench, svgOf, unitBlock, cardY, ledger, reset } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// The node with a unit in the middle and its hard needs wired in around it (feed, guards, journal, spec + envelope, labels).
// At the back, off the node, the soft links: router, PC and Library, on cables that can be pulled.
export function indepFig() {
  const BENCH = { x: -132, y: -96, w: 264, d: 180, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [0, -90, 40], [-74, -90, 30], [74, -64, 30], [-114, -42, 30], [114, -8, 36]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // soft links at the back
  const SOFT = [["router", "ROUTER", -54, 24], ["pc", "PC", 0, 32], ["lib", "LIBRARY", 54, 22]];
  for (const [id, name, cx, h] of SOFT) {
    const R = { x: cx - 20, y: -90, w: 40, d: 26, r: 2.5 };
    const parts = [box(R, 0, h, { tone: "mid", bevel: 0.7 }), L(k.planOutline(k.insetPlan(R, 3), h, P), { tone: "faint" }), lamp(id, cx + 12, -77, h, { r: 2.6 }), labelY(name, cx, R.y + R.d, h - 9, { px: 4 })];
    if (id === "pc") parts.splice(2, 0, box({ x: cx - 15, y: -86, w: 20, d: 14, r: 1 }, h, 1.4, { tone: "lo" }));
    if (id === "lib") parts.splice(2, 0, ledger(B, { x: cx - 16, y: -86, w: 20, d: 16, r: 1 }, h, { h: 7 }));
    out.push(hot(id, parts.join("")));
  }
  // node plinth
  const N = { x: -124, y: -50, w: 248, d: 126, r: 5 };
  out.push(hot("node", [box(N, 0, 8, { tone: "mid", bevel: 1, steps: 6 }), L(k.planOutline(k.insetPlan(N, 4), 8, P, 6), { tone: "faint" }), labelY("NODE · EVERY HARD NEED IS LOCAL", -40, N.y + N.d, 1.2, { px: 4.6 })].join("")));
  // soft cables: plugged, or lying unplugged on the bench
  const UT = 24.5; // unit top z
  const cable = (id, x0, z0, end) => [
    show(id + "On", B.wire([x0, -64, z0], end, [[x0, -56, 9], [end[0], -56, 9], [end[0], end[1] - 2, UT + 3]], { tone: "mid", flow: true })),
    show(id + "Off", B.wire([x0, -64, z0], [x0 + 10, -56, 1.2], [[x0, -60, 1]], { tone: "lo" })),
  ].join("");
  out.push(cable("router", -54, 6, [-12, 18, UT]), cable("pc", 0, 6, [0, 18, UT]), cable("lib", 54, 6, [12, 18, UT]));

  // hard needs on the node, back row
  const F = { x: -114, y: -42, w: 46, d: 34, r: 2.5 };
  out.push(hot("feed", [box(F, 8, 18, { tone: "mid", bevel: 0.7 }), ...[0, 1, 2].map((i) => box({ x: F.x + 6 + i * 12, y: F.y + 6, w: 8, d: 14, r: 1 }, 26, 1.2, { tone: "lo" })), lamp("feed", F.x + 38, F.y + 26, 26, { r: 2.6 }), labelY("FEED", F.x + F.w / 2, F.y + F.d, 12, { px: 4.4 })].join("")));
  const G = { x: 68, y: -42, w: 46, d: 34, r: 2.5 };
  out.push(hot("guard", [box(G, 8, 22, { tone: "mid", bevel: 0.7 }), cyl(G.x + 18, G.y + 16, 8, 30, 1.6, { tone: "lo" }), `<g data-cls="gbtn">${cyl(G.x + 18, G.y + 16, 6, 31.6, 3.5, { tone: "hi", bevel: 0.4 })}</g>`, lamp("guard", G.x + 37, G.y + 26, 30, { r: 2.6 }), labelY("GUARDS", G.x + G.w / 2, G.y + G.d, 13, { px: 4.4 })].join("")));
  // the unit
  const U = { x: -24, y: -4, w: 48, d: 26, r: 2.5 };
  out.push(B.wire([-68, -24, 14], [-24, 6, 14], [[-50, -24, 9], [-50, 6, 9]], { tone: "mid" }));
  out.push(B.wire([68, -24, 14], [24, 6, 14], [[48, -24, 9], [48, 6, 9]], { tone: "mid" }));
  out.push(hot("unit", [unitBlock(B, U, 8, { h: 16, cls: "unitc" }), lamp("unit", 30, 18, 8, { r: 3 })].join("")));
  // front row: journal, labels, spec + envelope
  out.push(B.wire([-74, 46, 12], [-18, 22, 12], [[-46, 46, 9], [-46, 30, 9], [-18, 30, 9]], { tone: "mid" }));
  out.push(hot("journal", [ledger(B, { x: -114, y: 32, w: 40, d: 30, r: 2 }, 8, { h: 12, text: "JOURNAL", px: 4 }), lamp("journal", -80, 68, 8, { r: 2.2 })].join("")));
  const LB = { x: -12, y: 40, w: 36, d: 24, r: 2 };
  out.push(B.wire([6, 40, 12], [6, 22, 12], [[6, 32, 9]], { tone: "faint" }));
  out.push(hot("labels", [box(LB, 8, 10, { tone: "mid", bevel: 0.5 }), labelTop("LABELS", LB.x + 14, LB.y + 12, 18, { px: 3.8 }), lamp("labels", LB.x + 30, LB.y + 12, 18, { r: 2.2 })].join("")));
  out.push(B.wire([70, 48, 12], [24, 18, 14], [[50, 48, 9], [50, 18, 9]], { tone: "mid" }));
  out.push(hot("spec", [box({ x: 70, y: 36, w: 46, d: 26, r: 2 }, 8, 4, { tone: "mid", bevel: 0.4 }), cardY(B, { x: 73, y: 44, z: 12, w: 19, h: 18, text: "SPEC", px: 3.2, lines: 3 }), cardY(B, { x: 94, y: 48, z: 12, w: 19, h: 18, text: "ADMIT", px: 3.2, lines: 3 })].join("")));

  const svg = svgOf(B, { label: "A node plinth with a unit in the middle, wired to its hard needs: a feed keeper and guards behind it, its journal, a market-label box, and its spec and signed admission in front. At the back, off the node, a router, the PC and the Library connect by cables that can be pulled out.", body: out });
  const labels = { router: "Router: soft. Offers only; they expire.", pc: "PC link: none needed for trading. You watch from it.", lib: "Library: writes wait in an outbox when it's away.", node: "Everything the unit needs to trade is on this machine.", feed: "Feed: hard, per symbol. A local keeper, never the router.", guard: "Guards read the feed directly. Down = no new entries.", unit: "The unit keeps trading while its hard needs are here.", journal: "Journal: written before every order. Hard.", labels: "Market labels: soft. Read the cache or compute here.", spec: "Its spec and your signed admission: local copies." };
  const L0 = { router: "ok", pc: "ok", lib: "ok", feed: "ok", guard: "ok", unit: "ok", journal: "ok", labels: "ok" };
  const plug = { routerOn: true, routerOff: false, pcOn: true, pcOff: false, libOn: true, libOff: false };
  const base = { lamps: L0, show: plug, cls: { unitc: "", gbtn: "" } };
  const start = (say) => ({ say, lit: ["unit"], lamps: L0, show: plug, cls: { unitc: "", gbtn: "" }, ms: 2600 });
  const modes = {
    router: [start("All plugged in. The unit is trading."),
      { say: "The router goes down. Its cable is out.", lit: ["router"], lamps: { router: "off" }, show: { routerOn: false, routerOff: true }, ms: 2800 },
      { say: "Offers expire. The unit trades what you admitted, on its own conditions.", lit: ["unit", "spec"], ms: 3400 },
      { say: "Its missing heartbeat is a yellow light, not a stop.", lit: ["router"], lamps: { router: "warn" }, ms: 3000 }],
    pc: [start("All plugged in. The unit is trading."),
      { say: "The PC link drops.", lit: ["pc"], lamps: { pc: "off" }, show: { pcOn: false, pcOff: true }, ms: 2600 },
      { say: "Your screen shows 'unreachable since …'. Trading carries on.", lit: ["unit"], ms: 3000 },
      { say: "Library away too: writes wait in an outbox until it's back.", lit: ["lib", "journal"], lamps: { lib: "warn" }, show: { libOn: false, libOff: true }, ms: 3200 }],
    feed: [start("All plugged in. The unit is trading."),
      { say: "One symbol's feed goes stale.", lit: ["feed"], lamps: { feed: "warn" }, ms: 2600 },
      { say: "No new entries on that symbol. Open trades keep their stops at the broker.", lit: ["unit"], lamps: { unit: "warn" }, cls: { unitc: "warn" }, ms: 3400 },
      { say: "The guards see it too: they read the feed directly, not via the router.", lit: ["guard", "feed"], ms: 3200 },
      { say: "Feed back: the unit resumes from the last prices.", lit: ["feed", "unit"], lamps: { feed: "ok", unit: "ok" }, cls: { unitc: "" }, ms: 2800 }],
    guard: [start("All plugged in. The unit is trading."),
      { say: "A guard itself fails.", lit: ["guard"], lamps: { guard: "bad" }, cls: { gbtn: "bad" }, ms: 2600 },
      { say: "Fail closed: no new entries on its account. Exits continue.", lit: ["unit"], lamps: { unit: "warn" }, cls: { unitc: "warn" }, ms: 3400 },
      { say: "The news guard already behaves this way in the shipped node.", lit: ["guard"], ms: 3000 }],
    labels: [start("All plugged in. The unit is trading."),
      { say: "The shared market-label cache goes missing.", lit: ["labels"], lamps: { labels: "warn" }, ms: 2800 },
      { say: "Option c': the unit computes the label itself, with the same library code.", lit: ["labels", "unit"], lamps: { labels: "ok" }, ms: 3600 },
      { say: "Option b: it uses its declared fallback, tested both ways in QMB.", lit: ["unit"], ms: 3200 }],
  };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.5 };
}
