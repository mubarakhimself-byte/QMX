import { bench, svgOf, cardY } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// The finding loop as a track: seed → card → build → three gate arches → screen → reflect → back to build.
// A try counter on the island in the middle; survivors leave for the proposal tray.
export function loopFig() {
  const BENCH = { x: -142, y: -84, w: 284, d: 172, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [72, -40, 30]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, liveY, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  const TR = { x: -120, y: -72, w: 212, d: 122, r: 8 };
  out.push(hot("track", [box(TR, 0, 3, { tone: "lo", bevel: 0.6 }), L(k.planOutline(k.insetPlan(TR, 4), 3, P), { tone: "faint" })].join("")));
  out.push(B.wire([-100, -46, 3.2], [-100, -46, 3.2], [[-100, -40, 3.2], [-100, 30, 3.2], [-60, 34, 3.2], [20, 34, 3.2], [60, 30, 3.2], [73, 10, 3.2], [73, -40, 3.2], [60, -56, 3.2], [-60, -56, 3.2], [-96, -52, 3.2]], { tone: "faint", flow: true, ends: "none" }));
  const ST = { seed: [-100, -56, "SEED"], card: [-44, -56, "CARD"], build: [12, -56, "BUILD"], screen: [40, 34, "SCREEN"], reflect: [-40, 34, "REFLECT"] };
  for (const [id, [x, y, name]] of Object.entries(ST)) out.push(hot(id, [box({ x: x - 14, y: y - 10, w: 28, d: 20, r: 2 }, 3, 2, { tone: "mid", bevel: 0.3 }), labelTop(name, x, y < 0 ? y - 13 : y + 14, 3, { px: 3.4 })].join("")));
  // gates: arches across the right-hand straight
  const GY = [-40, -18, 4];
  const GN = ["NEW?", "SIMPLE?", "MATCHES?"];
  // island (behind the gates on screen)
  const IS = { x: -82, y: -30, w: 118, d: 40, r: 4 };
  out.push(hot("tries", [box(IS, 3, 6, { tone: "mid", bevel: 0.8 }), L(k.planOutline(k.insetPlan(IS, 4), 9, P), { tone: "faint" }), labelTop("FINDING LOOP", IS.x + 40, IS.y + 14, 9, { px: 4.2 }), liveY("tries", "TRIES 0", IS.x + IS.w / 2, IS.y + IS.d, 3.6, { px: 3.6 })].join("")));
  GY.forEach((y, i) => {
    out.push(hot("gates", [cyl(60, y, 2, 3, 18, { tone: "mid", steps: 14 }), cyl(86, y, 2, 3, 18, { tone: "mid", steps: 14 }), box({ x: 57, y: y - 3, w: 32, d: 6, r: 1 }, 21, 4, { tone: "mid", bevel: 0.4 }), lamp("g" + i, 82, y, 25, { r: 2 }), labelY(GN[i], 69, y + 3, 21.6, { px: 2.6, plate: false })].join("")));
  });
  // proposal tray
  out.push(hot("proposal", [box({ x: 96, y: 52, w: 40, d: 30, r: 2 }, 0, 4, { tone: "mid", bevel: 0.4 }), cardY(B, { x: 104, y: 62, z: 4, w: 24, h: 18, text: "PROPOSAL", px: 2.8, lines: 3 }), lamp("prop", 130, 76, 4, { r: 2 })].join("")));
  // token, built at SEED
  const S0 = ST.seed;
  out.push(hot("token", move("tok", box({ x: S0[0] - 5, y: S0[1] - 5, w: 10, d: 10, r: 2 }, 5, 7, { tone: "hi", bevel: 0.5 }))));
  const at = (x, y) => [x - S0[0], y - S0[1], 0];
  const p = (id) => at(ST[id][0], ST[id][1]);
  const G3 = { g0: "ok", g1: "ok", g2: "ok" };
  const base = { move: { tok: [0, 0, 0] }, text: { tries: "TRIES 0" }, lamps: { g0: "off", g1: "off", g2: "off", prop: "off" } };
  const modes = { main: [
    { say: "A seed: your words, a copilot chat, an article, a video.", lit: ["seed"], ...base, ms: 2800 },
    { say: "A hypothesis card: what, why, which market and session.", lit: ["card"], move: { tok: p("card") }, ms: 2800 },
    { say: "A cheap model builds the unit from library blocks.", lit: ["build"], move: { tok: p("build") }, ms: 2800 },
    { say: "Three cheap gates: is it new? simple enough? does the code match the card?", lit: ["gates"], move: { tok: at(73, -18) }, lamps: G3, ms: 3600 },
    { say: "A screen backtest. Every screen counts as a try.", lit: ["screen", "tries"], move: { tok: p("screen") }, text: { tries: "TRIES 1" }, ms: 3000 },
    { say: "Reflect: name the one step that failed, or pick two parents to cross.", lit: ["reflect"], move: { tok: p("reflect") }, lamps: { g0: "off", g1: "off", g2: "off" }, ms: 3200 },
    { say: "Loop back and change that one step.", lit: ["track"], move: { tok: at(-100, 34) }, ms: 1400 },
    { say: "Loop back and change that one step.", lit: ["track"], move: { tok: p("seed") }, ms: 1400 },
    { say: "Build again.", lit: ["build"], move: { tok: p("build") }, ms: 1800 },
    { say: "Through the gates…", lit: ["gates"], move: { tok: at(73, -18) }, lamps: G3, ms: 1800 },
    { say: "Screen: try 2. Gains fade after about 15 rounds, so late winners get a flag.", lit: ["screen", "tries"], move: { tok: p("screen") }, text: { tries: "TRIES 2" }, ms: 3600 },
    { say: "Survivors end as a proposal card for you. Never a promotion.", lit: ["proposal"], move: { tok: at(116, 66) }, lamps: { prop: "ok" }, ms: 3400 },
  ] };
  const labels = { seed: "Seed: you, a copilot chat, an article, a video.", card: "Hypothesis card: observation, reasoning, market, session.", build: "Build from library blocks (a cheap model is fine).", gates: "Gates: original vs existing units, complexity, code matches the card.", screen: "Screen backtest on a validation window. Always a try.", reflect: "Reflect: one failing step to change, or two parents to cross.", tries: "Every screen and refinement counts as a try.", proposal: "A proposal card. You decide.", track: "The loop grows only while it makes progress. No fixed cap.", token: "A candidate unit." };
  const svg = svgOf(B, { label: "A track with stations: seed, card, build, three gate arches (new? simple? matches?), screen and reflect, around an island showing the try count. A candidate token goes round twice, then leaves for a proposal tray.", body: out });
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.45 };
}
