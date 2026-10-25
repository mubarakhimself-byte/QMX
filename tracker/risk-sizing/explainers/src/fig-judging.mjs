import { bench, svgOf } from "./parts.mjs";

// The luck bar: one pillar per variant tried, and a bar that rises with the number of tries.
// Height = Sharpe per trade. SE = 1/sqrt(500) = 0.045. The bar sits at the expected best of N pure-luck variants.
export const LUCK = { 1: 0, 5: 1.16, 10: 1.54, 20: 1.87, 100: 2.51 };
export function judgingFig() {
  const BENCH = { x: -130, y: -46, w: 260, d: 92, r: 8 };
  const ZK = 420; // world z per Sharpe unit
  const SE = 0.045;
  const N = 20;
  // fixed pseudo-random luck draws (|z| of a normal, deterministic), plus one real-edge variant at 0.12
  const draws = [0.31, 1.12, 0.52, 1.66, 0.08, 0.94, 1.38, 0.21, 0.73, 1.87, 0.45, 1.05, 0.15, 1.51, 0.66, 0.38, 1.24, 0.87, 0.57, 1.02];
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-110, -20, 0.14 * ZK + 10], [110, -20, 0.14 * ZK + 10]], { width: 400, pad: 8, azimuth: 60 });
  const { box, cyl, hot, move, L, D, k, P, labelY, labelTop, liveY, show } = B;
  const out = [B.base(BENCH, { h: 8 })];
  // back posts with a scale strip
  for (const x of [-118, 112]) out.push(box({ x, y: -34, w: 6, d: 6, r: 1 }, 0, 0.15 * ZK, { tone: "mid", bevel: 0.4 }));
  // the luck bar: a beam across the posts, moved up and down
  const beam = [box({ x: -120, y: -24, w: 238, d: 4, r: 0.8 }, 0, 2.2, { tone: "hi", bevel: 0 })].join("");
  out.push(hot("bar", move("bar", `<g data-cls="bar">${beam}</g>`, [0, 0, 0])));
  // pillars: variant 0 is the real-edge idea
  const px = (i) => -104 + i * 10.9;
  for (let i = 0; i < N; i++) {
    const h = i === 0 ? 0.12 * ZK : Math.max(1.5, draws[i] * SE * ZK);
    const body = [box({ x: px(i) - 4.4, y: -14, w: 8.8, d: 9, r: 1 }, 0, h, { tone: i === 0 ? "hi" : "mid", bevel: 0.3 })].join("");
    out.push(i === 0 ? hot("best", body) : show("p" + i, hot("luck", body)));
  }
  out.push(hot("count", [box({ x: -126, y: 26, w: 44, d: 16, r: 2 }, 0, 14, { tone: "mid", bevel: 0.5 }), liveY("n", "N = 1", -104, 42, 4, { px: 5 })].join("")));
  out.push(labelY("EACH PILLAR = ONE VARIANT TRIED", 30, 30, 0.2, { px: 4.2, plate: false, tone: "mid" }));
  const svg = svgOf(B, { label: "A row of pillars, one per variant tried; the first is a real idea at 0.12 Sharpe per trade. A bar across the back rises to where the best of N pure-luck variants would reach. As N grows, the real idea barely clears it.", body: out });
  const labels = { best: "Your best variant: 0.12 per trade (example).", luck: "Pure luck: variants with no edge at all.", bar: "Luck bar: what the best of N lucky variants reaches.", count: "N: the number of variants tried in the family." };
  const sc = (n, shown, say, extra = "") => `{say:${JSON.stringify(say)},text:{n:"N = ${n}"},move:{bar:[0,0,${(LUCK[n] * SE * ZK).toFixed(1)}]},show:{${Array.from({ length: N - 1 }, (_, j) => `p${j + 1}:${j + 1 < shown}`).join(",")}},${extra}ms:3600}`;
  const modes = `{main:[
 ${sc(1, 1, "One idea, one test: 0.12 per trade looks clearly real.", 'lit:["best"],')},
 ${sc(5, 5, "Five variants tried: luck alone reaches 0.05.", 'lit:["bar"],')},
 ${sc(10, 10, "Ten tried: luck reaches 0.07.", 'lit:["bar","count"],')},
 ${sc(20, 20, "Twenty tried: luck reaches 0.08.", 'lit:["luck"],')},
 ${sc(100, 20, "A hundred tried: luck reaches 0.11. Your 0.12 barely beats luck.", 'lit:["best","bar"],cls:{bar:"warn"},')},
 {say:"So QMX counts every try and corrects the best result for it.",lit:["count"],cls:{bar:""},ms:3200}
]}`;
  return { svg, P, labels, modes, init: { show: Object.fromEntries(Array.from({ length: N - 1 }, (_, j) => ["p" + (j + 1), false])) }, ease: 0.5 };
}
