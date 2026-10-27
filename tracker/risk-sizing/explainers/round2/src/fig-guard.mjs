import { bench, svgOf, cardY } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// Three shapes side by side: (a) one pod object holding the guard, (b) a fixed guard base with a pod template on top,
// (c) one pod with the guard as a locked block. A copilot edit card drops onto each; a floor lamp shows if the floor can move.
export function guardFig() {
  const BENCH = { x: -154, y: -62, w: 308, d: 126, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-100, -40, 64], [100, -40, 64]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  const W = 62, D = 56;
  const slot = (x, y, w, d, z, name, px = 2.8) => [box({ x, y, w, d, r: 1 }, z, 1.2, { tone: "lo" }), labelTop(name, x + w / 2, y + d / 2, z + 1.2, { px })].join("");

  // (a) one object
  const A = { x: -131, y: -46, w: W, d: D, r: 3 };
  out.push(hot("a", [box(A, 0, 24, { tone: "mid", bevel: 0.8 }), `<g data-cls="ga">${slot(A.x + 5, A.y + 5, 52, 13, 24, "GUARD")}</g>`, slot(A.x + 5, A.y + 21, 52, 13, 24, "BUDGET"), slot(A.x + 5, A.y + 37, 52, 13, 24, "SAME-BET"), labelY("A · ONE OBJECT", A.x + W / 2, A.y + D, 7, { px: 4 }), lamp("fa", A.x + W / 2, A.y + D + 12, 0, { r: 2.8 }), labelTop("FLOOR", A.x + W / 2 + 13, A.y + D + 12, 0, { px: 3 })].join("")));
  // (b) two layers
  const G = { x: -31, y: -46, w: W, d: D, r: 3 };
  const PT = { x: -26, y: -41, w: W - 10, d: D - 10, r: 2.5 };
  out.push(hot("b", [`<g data-cls="gb">${box(G, 0, 13, { tone: "lo", bevel: 0.8 })}</g>`, L([4, 9].map((z) => k.sideSeam(G, z, P, 4)).join(""), { tone: "faint" }), labelY("GUARD · FIXED", 0, G.y + D, 3.4, { px: 3.4 }),
    ...k.corners(PT, 5).map(([x, y]) => cyl(x, y, 1.8, 13, 3, { tone: "mid", steps: 14 })),
    box(PT, 16, 12, { tone: "mid", bevel: 0.6 }), slot(PT.x + 4, PT.y + 6, 44, 14, 28, "BUDGET"), slot(PT.x + 4, PT.y + 25, 44, 14, 28, "SAME-BET"), labelY("POD TEMPLATE", 0, PT.y + PT.d, 19.5, { px: 3.2 }),
    lamp("fb", 0, G.y + D + 12, 0, { r: 2.8 }), labelTop("FLOOR", 13, G.y + D + 12, 0, { px: 3 })].join("")));
  // (c) locked block
  const C = { x: 69, y: -46, w: W, d: D, r: 3 };
  out.push(hot("c", [box(C, 0, 24, { tone: "mid", bevel: 0.8 }), `<g data-cls="gc">${box({ x: C.x + 5, y: C.y + 5, w: 52, d: 14, r: 1.2 }, 24, 3, { tone: "hi", bevel: 0.4 })}</g>`, labelTop("GUARD · LOCKED", C.x + 26, C.y + 12, 27, { px: 2.8 }),
    box({ x: C.x + 48, y: C.y + 8, w: 6, d: 7, r: 1 }, 27, 4, { tone: "mid", bevel: 0.3 }), slot(C.x + 5, C.y + 23, 52, 12, 24, "BUDGET"), slot(C.x + 5, C.y + 38, 52, 12, 24, "SAME-BET"), labelY("C · LOCKED BLOCK", C.x + W / 2, C.y + D, 7, { px: 3.8 }), lamp("fc", C.x + W / 2, C.y + D + 12, 0, { r: 2.8 }), labelTop("FLOOR", C.x + W / 2 + 13, C.y + D + 12, 0, { px: 3 })].join("")));
  out.push(labelTop("B · TWO LAYERS", 0, 34, 0, { px: 3.4 }));
  // edit cards, drawn last; each built hovering above its station
  const card = (id, cx) => show(id, hot("edit", move(id, `<g data-cls="${id}c">${cardY(B, { x: cx - 12, y: -24, z: 48, w: 24, h: 16, text: "EDIT", px: 3, lines: 2 })}</g>`)));
  out.push(card("ea", -100), card("eb", 0), card("ec", 100));

  const svg = svgOf(B, { label: "Three shapes side by side. A: one pod object with guard, budget and same-bet slots. B: a fixed guard base with a pod template standing on posts above it. C: one pod with the guard as a locked block. A copilot edit card drops onto each; a floor lamp in front of each shows whether the edit could lower the safety floor.", body: out });
  const labels = { a: "A: pod = BMS = guard + shared budget + same-bet limits, one per account.", b: "B: a fixed guard per account; pod templates above it.", c: "C: one shape; the guard is a locked block inside every pod.", edit: "A copilot remakes the pod." };
  const base = { show: { ea: false, eb: false, ec: false }, move: { ea: [0, 0, 0], eb: [0, 0, 0], ec: [0, 0, 0] }, lamps: { fa: "ok", fb: "ok", fc: "ok" }, cls: { ga: "", gb: "", gc: "", eac: "", ebc: "", ecc: "" } };
  const modes = { main: [
    { say: "A: one object per account. Guard, shared budget and same-bet limits together.", lit: ["a"], ...base, ms: 3400 },
    { say: "A copilot remakes this pod. The edit lands on the whole object…", lit: ["a", "edit"], show: { ea: true }, move: { ea: [0, 0, -20] }, ms: 3000 },
    { say: "…so one edit can reach the guard and lower the floor.", lit: ["a"], cls: { ga: "bad" }, lamps: { fa: "bad" }, ms: 3000 },
    { say: "B: a fixed guard per account. Pod templates sit above it.", lit: ["b"], ms: 3200 },
    { say: "The copilot remakes the template. The guard below can't be touched.", lit: ["b", "edit"], show: { eb: true }, move: { eb: [0, 0, -18] }, cls: { gb: "ok" }, ms: 3400 },
    { say: "C: one shape. The guard is a locked block inside every pod.", lit: ["c"], ms: 3200 },
    { say: "An edit that changes the locked block is refused by a hook.", lit: ["c", "edit"], show: { ec: true }, move: { ec: [0, 0, -18] }, cls: { ecc: "bad", gc: "ok" }, ms: 3400 },
    { say: "Safe only if the lock is checked by code, not by habit.", lit: ["c"], move: { ec: [0, 0, 0] }, ms: 3000 },
    { say: "All three share one small door: may this unit add risk? Yes or no, with a reason. None resizes.", lit: ["a", "b", "c"], ms: 4000 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.5 };
}
