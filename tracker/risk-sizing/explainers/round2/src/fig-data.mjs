import { bench, svgOf } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// A price tape with a reader carriage. Today, every step leaves a pile of copies behind it (piles grow step by step);
// a memory dial climbs. Four plates in front are the four places that copy. Fixed: one tape, a pointer, a flat dial.
export function replayFig() {
  const BENCH = { x: -142, y: -78, w: 284, d: 150, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-110, -60, 50]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, liveY, lamp, dial, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // copy piles at the back
  const PX = [-118, -78, -38, 2, 42, 82];
  PX.forEach((x, i) => {
    const n = i + 1;
    const plates = [];
    for (let j = 0; j < n * 2; j++) plates.push(box({ x: x - 14, y: -70, w: 28, d: 22, r: 1.5 }, j * 3.6, 3.2, { tone: j === n * 2 - 1 ? "hi" : "mid", bevel: 0.3, steps: 3 }));
    out.push(show("p" + i, hot("piles", plates.join("") + labelY("STEP " + n, x, -48, 0.4, { px: 3, plate: false }))));
  });
  // the tape
  const T = { x: -132, y: -30, w: 264, d: 16, r: 2 };
  const tk = k.topTicks(T.x + 6, T.x + T.w - 6, 6, 5, T.y + T.d, 4, [1.6, 3.2], P);
  out.push(hot("tape", [box(T, 0, 4, { tone: "mid", bevel: 0.5 }), L(tk.minor, { tone: "lo" }), L(tk.major, { tone: "mid" }), labelTop("1990", T.x + 14, T.y + 7, 4, { px: 3.4 }), labelTop("2026", T.x + T.w - 14, T.y + 7, 4, { px: 3.4 }), labelY("ONE PRICE SERIES", -2, T.y + T.d, 0.6, { px: 3.6, plate: false })].join("")));
  // the carriage (built at the left, moved right)
  const C = { x: -124, y: -34, w: 14, d: 24, r: 2 };
  out.push(hot("car", move("car", [box(C, 4, 9, { tone: "hi", bevel: 0.5 }), cyl(C.x + 7, C.y + 7, 2.6, 13, 2, { tone: "mid" }), box({ x: C.x + 5.5, y: C.y + C.d - 1, w: 3, d: 4, r: 0.5 }, 0.2, 4, { tone: "mid" })].join(""))));
  // four places that copy
  const FIX = [["LIST", "f0"], ["FREEZE", "f1"], ["DEEP FREEZE", "f2"], ["COMPARE", "f3"]];
  FIX.forEach(([name, id], i) => {
    const R = { x: -132 + i * 46, y: 12, w: 40, d: 26, r: 2 };
    out.push(hot("fix", [box(R, 0, 8, { tone: "mid", bevel: 0.5 }), lamp(id, R.x + 32, R.y + 13, 8, { r: 2.2 }), labelTop(name, R.x + 15, R.y + 13, 8, { px: name.length > 8 ? 2.6 : 3.2 }), labelY(String(i + 1), R.x + R.w / 2, R.y + R.d, 1.2, { px: 3.4, plate: false })].join("")));
  });
  // memory dial
  const M = dial("mem", 104, 30, 20, 16, { h: 4, value: 0.05, ticks: 25, every: 5 });
  out.push(hot("mem", [box({ x: 78, y: 4, w: 52, d: 52, r: 3 }, 0, 16, { tone: "mid", bevel: 0.6 }), M.svg, lamp("mem", 124, 50, 16, { r: 2.4 }), labelY("MEMORY", 104, 56, 4, { px: 4 })].join("")));

  const svg = svgOf(B, { label: "A long price tape from 1990 to 2026 with a reader carriage on it. Behind it, piles of copied plates grow one step at a time. In front, four plates mark the four places in the code that copy, and a memory dial on a pedestal.", body: out });
  const labels = { tape: "One price series. A test may start wherever the data reaches.", car: "The replay reader: one step per bar.", piles: "Today: every step keeps its own copy of every price so far.", fix: "Four places copy or compare whole frames. All four must change.", mem: "Memory used by one run." };
  const hide = Object.fromEntries(PX.map((_, i) => ["p" + i, false]));
  const showN = (n) => Object.fromEntries(PX.map((_, i) => ["p" + i, i < n]));
  const base = { show: hide, dial: { mem: 0.05 }, move: { car: [0, 0, 0] }, lamps: { f0: "off", f1: "off", f2: "off", f3: "off", mem: "ok" } };
  const step = (n) => [n * 36, 0, 0];
  const modes = {
    today: [
      { say: "A replay walks through prices one step at a time.", lit: ["car", "tape"], ...base, ms: 2800 },
      { say: "Step 1 keeps a copy of every price so far.", lit: ["piles"], show: showN(1), move: { car: step(1) }, dial: { mem: 0.08 }, ms: 2600 },
      { say: "Step 2 copies them all again. Step 3 again.", lit: ["piles"], show: showN(3), move: { car: step(3) }, dial: { mem: 0.25 }, ms: 3000 },
      { say: "Memory grows with the square of the steps.", lit: ["piles", "mem"], show: showN(6), move: { car: step(6) }, dial: { mem: 0.7 }, lamps: { mem: "warn" }, ms: 3200 },
      { say: "At 4,320 steps a test ran out of memory. Runs are capped at 1,000 steps: about 17 hours of 1-minute bars.", lit: ["mem"], dial: { mem: 1 }, lamps: { mem: "bad" }, ms: 4200 },
      { say: "That cap is the lookback limit you heard about. Four places make the copies.", lit: ["fix"], lamps: { f0: "bad", f1: "bad", f2: "bad", f3: "bad" }, ms: 3800 },
    ],
    fixed: [
      { say: "Fix: one shared price series. Each step only marks where it ends.", lit: ["tape", "car"], ...base, lamps: { f0: "ok", f1: "ok", f2: "ok", f3: "ok", mem: "ok" }, ms: 3400 },
      { say: "Memory stays flat. Same answers, no change to any unit.", lit: ["mem", "car"], move: { car: step(6) }, dial: { mem: 0.12 }, ms: 3200 },
      { say: "Or keep only the window the unit declares, like live does.", lit: ["car"], ms: 3000 },
      { say: "Then a test can start in 1990, wherever the data goes back that far.", lit: ["tape", "car"], move: { car: [0, 0, 0] }, ms: 3400 },
    ],
  };
  return { svg, P, labels, init: base, dials: { mem: M.spec }, modes: modesOf(modes), ease: 0.6 };
}
