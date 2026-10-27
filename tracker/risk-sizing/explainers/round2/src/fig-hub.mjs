import { bench, svgOf, unitBlock, cardY, ledger } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// Round 2 on one bench: PC home + a stand-in server, the router's offer board, his key lock,
// the node with a feed keeper, an envelope fence around three units and a guard, the ideas shelf,
// the journals, and an open-ended data tape along the front. Every part links to its page.
export function hubFig() {
  const BENCH = { x: -162, y: -134, w: 324, d: 236, r: 10 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-130, -120, 50], [76, -112, 44]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const link = (id, href, svg) => hot(id, svg, ` data-href="${href}" role="link" tabindex="0" aria-label="${id}"`);
  const out = [B.base(BENCH, { h: 8 })];

  // back row: PC + server stand-in
  const PC = { x: -154, y: -128, w: 46, d: 38, r: 3 };
  out.push(link("pc", "feeds.html", [box(PC, 0, 40, { tone: "mid", bevel: 0.8 }), box({ x: PC.x + 7, y: PC.y + 7, w: 26, d: 16, r: 1 }, 40, 1.4, { tone: "lo" }), lamp("pc", PC.x + 38, PC.y + 30, 40, { r: 2.6 }), labelY("PC · HOME", PC.x + PC.w / 2, PC.y + PC.d, 16, { px: 5.4 })].join("")));
  const SV = { x: -100, y: -126, w: 24, d: 30, r: 2 };
  out.push(link("server", "feeds.html", [box(SV, 0, 24, { tone: "lo", bevel: 0.5 }), L([6, 12, 18].map((z) => k.sideSeam(SV, z, P, 4)).join(""), { tone: "faint" }), lamp("server", SV.x + 12, SV.y + 22, 24, { r: 2 }), labelY("SERVER", SV.x + SV.w / 2, SV.y + SV.d, 12, { px: 3.2 })].join("")));
  // router board
  const RB = { x: -48, y: -128, w: 74, d: 26, r: 2.5 };
  out.push(link("router", "router.html", [box(RB, 0, 26, { tone: "mid", bevel: 0.7 }), box({ x: RB.x + 6, y: RB.y + 8, w: 46, d: 6, r: 1 }, 26, 1.4, { tone: "lo" }), lamp("router", RB.x + 64, RB.y + 13, 26, { r: 2.6 }), labelY("ROUTER · OFFERS", RB.x + RB.w / 2, RB.y + RB.d, 8, { px: 5 })].join("")));
  // lock
  const LK = { x: 44, y: -128, w: 40, d: 30, r: 2.5 };
  out.push(link("lock", "envelope.html", [box(LK, 0, 22, { tone: "mid", bevel: 0.7 }), cyl(LK.x + 14, LK.y + 11, 7, 22, 1.6, { tone: "lo" }), move("key", [box({ x: LK.x + 13, y: LK.y + 9.4, w: 2, d: 3.2, r: 0.3 }, 23.6, 12, { tone: "hi", bevel: 0 }), box({ x: LK.x + 9.5, y: LK.y + 9.4, w: 9, d: 3.2, r: 1.4 }, 35.6, 8, { tone: "hi", bevel: 0.4 })].join(""), [0, 0, 9]), lamp("admit", LK.x + 32, LK.y + 10, 22, { r: 2.4 }), labelTop("YOUR CLICK", LK.x + LK.w / 2, LK.y + 23, 22, { px: 4.2 })].join("")));
  // ideas shelf + journals on the left
  const SH = { x: -156, y: -80, w: 56, d: 34, r: 2 };
  out.push(link("ideas", "ideas.html", [box(SH, 0, 5, { tone: "mid", bevel: 0.5 }), ...[0, 1, 2].map((i) => cardY(B, { x: SH.x + 4 + i * 17, y: SH.y + 10 + (i % 2) * 6, z: 5, w: 15, h: 20, lines: 3 })), labelY("IDEAS", SH.x + SH.w / 2, SH.y + SH.d, 0.8, { px: 4.6, plate: false })].join("")));
  out.push(link("journals", "journals.html", [ledger(B, { x: -156, y: -24, w: 56, d: 40, r: 2.5 }, 0, { h: 14, text: "JOURNALS", px: 4.8 })].join("")));
  // node
  const N = { x: -84, y: -86, w: 238, d: 124, r: 5 };
  const NZ = 10;
  out.push(link("node", "independence.html", [box(N, 0, NZ, { tone: "mid", bevel: 1, steps: 6 }), L(k.planOutline(k.insetPlan(N, 4), NZ, P, 6), { tone: "faint" }), labelY("NODE", N.x + 30, N.y + N.d, 2, { px: 5 })].join("")));
  // cables: PC -> node (soft), router -> node (offers)
  out.push(show("pcOn", B.wire([-108, -100, 8], [-84, -60, 6], [[-96, -92, 1], [-96, -60, 1]], { tone: "mid", flow: true })));
  // feed keeper
  const K = { x: -76, y: -78, w: 38, d: 30, r: 2.5 };
  out.push(link("feed", "feeds.html", [box(K, NZ, 20, { tone: "mid", bevel: 0.7 }), lamp("feed", K.x + 30, K.y + 22, NZ + 20, { r: 2.4 }), labelY("FEEDS", K.x + K.w / 2, K.y + K.d, NZ + 6, { px: 4.4 })].join("")));
  out.push(B.wire([-38, -63, NZ + 8], [-20, -63, NZ + 4], [], { tone: "mid", flow: true }));
  // envelope fence with units
  const E = { x: -20, y: -80, w: 116, d: 106, r: 4 };
  const posts = [];
  for (const x of [E.x + 3, E.x + E.w - 3]) for (const y of [E.y + 3, E.y + E.d - 3]) posts.push([x, y]);
  const post = ([x, y]) => [cyl(x, y, 1.9, NZ + 3, 12, { tone: "mid", steps: 14 }), cyl(x, y, 2.5, NZ + 15, 1.4, { tone: "mid", steps: 14 })].join("");
  const rail = (a, b) => box({ x: Math.min(a[0], b[0]) - 0.7, y: Math.min(a[1], b[1]) - 0.7, w: Math.abs(a[0] - b[0]) + 1.4, d: Math.abs(a[1] - b[1]) + 1.4, r: 0.4 }, NZ + 11, 1.5, { tone: "lo", bevel: 0 });
  const [pBL, pBR, pFL, pFR] = [[E.x + 3, E.y + 3], [E.x + E.w - 3, E.y + 3], [E.x + 3, E.y + E.d - 3], [E.x + E.w - 3, E.y + E.d - 3]];
  out.push(link("envelope", "envelope.html", [box(E, NZ, 3, { tone: "lo", bevel: 0.5 }), post(pBL), post(pBR), post(pFL), rail(pBL, pBR), rail(pBL, pFL)].join("")));
  const UNITS = [{ x: -8, y: -70, w: 40, d: 22, r: 2 }, { x: 46, y: -70, w: 40, d: 22, r: 2 }, { x: -8, y: -36, w: 40, d: 22, r: 2 }, { x: 46, y: -36, w: 40, d: 22, r: 2 }];
  UNITS.forEach((U, i) => out.push(link("units", "independence.html", [unitBlock(B, U, NZ + 3, { h: 13, cls: "u" + i }), lamp("u" + i, U.x + U.w / 2, U.y + U.d + 5, NZ + 3, { r: 2 })].join(""))));
  out.push(link("envelope", "envelope.html", [post(pFR), rail(pFL, pFR), rail(pBR, pFR)].join("")));
  // guard
  const G = { x: 106, y: -78, w: 40, d: 34, r: 2.5 };
  out.push(link("guard", "guard-pod.html", [box(G, NZ, 22, { tone: "mid", bevel: 0.7 }), cyl(G.x + 16, G.y + 16, 8, NZ + 22, 1.6, { tone: "lo" }), `<g data-cls="gbtn">${cyl(G.x + 16, G.y + 16, 6, NZ + 23.6, 3.5, { tone: "hi", bevel: 0.4 })}</g>`, labelY("GUARD + POD", G.x + G.w / 2, G.y + G.d, NZ + 6, { px: 3.8 })].join("")));
  // papers: a small loop disc on the node
  out.push(link("papers", "papers.html", [cyl(126, 8, 14, NZ, 3, { tone: "lo" }), L(k.ring(126, 8, 9, NZ + 3, P, 32), { tone: "mid" }), cyl(135, 8, 2.4, NZ + 3, 3, { tone: "hi" }), labelTop("LOOP", 126, 26, NZ, { px: 3.6 })].join("")));
  // data tape along the front
  const T = { x: -154, y: 58, w: 308, d: 18, r: 2 };
  const tk = k.topTicks(T.x + 8, T.x + T.w - 8, 8, 5, T.y + T.d, 4, [1.8, 3.6], P);
  out.push(link("data", "data.html", [box(T, 0, 4, { tone: "mid", bevel: 0.5 }), L(tk.minor, { tone: "lo" }), L(tk.major, { tone: "mid" }), labelTop("1990", T.x + 18, T.y + 8, 4, { px: 4 }), labelTop("2026", T.x + T.w - 18, T.y + 8, 4, { px: 4 }), labelY("DATA · NO LOOKBACK CAP", 0, T.y + T.d, 0.6, { px: 4.2, plate: false })].join("")));
  out.push(link("data", "data.html", move("car", [box({ x: 96, y: 54, w: 16, d: 26, r: 2 }, 4, 9, { tone: "hi", bevel: 0.5 }), cyl(104, 61, 2.6, 13, 2, { tone: "mid" })].join(""))));
  // offer card, drawn last
  const C0 = { x: -36, y: -120, z: 27.4 };
  out.push(show("card", link("router", "router.html", move("card", cardY(B, { x: C0.x, y: C0.y, z: C0.z, w: 20, h: 12, text: "OFFER", px: 3, lines: 2 })))));
  const toU1 = [66 - (C0.x + 10), -59 - C0.y, NZ + 16 - C0.z];

  const svg = svgOf(B, { label: "Round 2 on one bench. Back row: the PC (home) with a smaller stand-in server, the router's offer board, and a key lock for your click. Middle: the node, with a feed keeper, a fenced envelope holding four units, the guard and pod, and a loop disc for the papers. Left: the ideas shelf and the journals. Front: a data tape from 1990 to 2026 with a reader carriage. Each part opens its page.", body: out });
  const labels = { pc: "PC: home. It can run everything alone → page", server: "Servers stand in or extend, never replace → page", router: "Router: offers that expire, never a switch → page", lock: "Your click: the only way into live → page", ideas: "Ideas, sources and lineage → page", journals: "Four journals, one writer each → page", node: "Every hard need of a unit is local → page", feed: "Feed pool: one keeper per broker connection → page", envelope: "The admission envelope → page", units: "Units stand alone → page", guard: "Guard and pod: three shapes → page", papers: "Papers and the Hermes gold mine → page", data: "Data and the lookback limit → page" };
  const ids = ["u0", "u1", "u2", "u3"];
  const all = (v) => Object.fromEntries(ids.map((i) => [i, v]));
  const base = { lamps: { pc: "ok", server: "ok", router: "ok", admit: "off", feed: "ok", ...all("ok") }, move: { key: [0, 0, 9], card: [0, 0, 0], car: [0, 0, 0] }, show: { card: true, pcOn: true }, cls: { ...all(""), gbtn: "" } };
  const modes = { main: [
    { say: "1 · The router directs and never switches. It offers; units decide.", lit: ["router"], ...base, ms: 3000 },
    { say: "1 · An offer reaches a unit. It may take it or ignore it.", lit: ["router", "units"], move: { card: toU1 }, ms: 3000 },
    { say: "2 · Units stand alone. Router down: they keep trading.", lit: ["units", "node"], lamps: { router: "off" }, show: { card: false }, cls: all("ok"), ms: 3400 },
    { say: "3 · Only you promote. Your click admits a unit with its envelope.", lit: ["lock", "envelope"], lamps: { router: "ok", admit: "ok" }, move: { key: [0, 0, 0] }, cls: all(""), ms: 3400 },
    { say: "4 · Unbounded by default: any start date; plain Python always allowed.", lit: ["data"], move: { car: [-230, 0, 0] }, ms: 3400 },
    { say: "5 · Local first: the PC can run it all. Servers only stand in.", lit: ["pc"], lamps: { server: "off" }, ms: 3400 },
    { say: "Tap any part to open its page.", lit: [], lamps: { server: "ok" }, move: { car: [0, 0, 0], card: [0, 0, 0] }, show: { card: true }, ms: 3000 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.6 };
}
