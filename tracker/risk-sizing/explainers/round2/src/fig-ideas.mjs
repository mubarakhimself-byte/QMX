import { bench, svgOf, unitBlock, cardY } from "./common.mjs";
import { modesOf } from "./site2.mjs";

// Sources on a shelf, an idea record, two family trays. A port block is lifted out of a family X unit
// and set into a family Y unit (a transplant). Other unit kinds stand at the right.
export function ideasFig() {
  const BENCH = { x: -142, y: -92, w: 284, d: 172, r: 9 };
  const B = bench([[BENCH.x, BENCH.y, -12], [BENCH.x + BENCH.w, BENCH.y + BENCH.d, -12], [BENCH.x, BENCH.y + BENCH.d, -12], [BENCH.x + BENCH.w, BENCH.y, -12], [-120, -80, 30], [30, -62, 44]], { width: 400, pad: 8 });
  const { box, cyl, hot, move, L, k, P, labelY, labelX, labelTop, liveY, lamp, show } = B;
  const out = [B.base(BENCH, { h: 8 })];

  // source shelf
  const SH = { x: -136, y: -86, w: 66, d: 26, r: 2 };
  out.push(hot("sources", [box(SH, 0, 4, { tone: "mid", bevel: 0.5 }), ...["VIDEO", "POST", "CHAT", "YOU"].map((t, i) => cardY(B, { x: SH.x + 3 + i * 15.6, y: SH.y + 8 + (i % 2) * 6, z: 4, w: 14, h: 20, text: t, px: 2.7, lines: 3 })), labelY("SOURCES", SH.x + SH.w / 2, SH.y + SH.d, 0.6, { px: 3.6, plate: false })].join("")));
  // idea record
  const IR = { x: -132, y: -44, w: 46, d: 30, r: 2 };
  out.push(B.wire([-103, -60, 4], [-109, -44, 6], [[-103, -50, 1], [-109, -50, 1]], { tone: "mid" }));
  out.push(hot("idea", [box(IR, 0, 6, { tone: "mid", bevel: 0.5 }), cardY(B, { x: IR.x + 6, y: IR.y + 12, z: 6, w: 30, h: 16, text: "IDEA RECORD", px: 2.9, lines: 2 }), lamp("idea", IR.x + 40, IR.y + 24, 6, { r: 2 })].join("")));

  // family X (back) and Y (front)
  const FX = { x: -64, y: -88, w: 114, d: 48, r: 3 }, FY = { x: -64, y: -24, w: 114, d: 48, r: 3 };
  const port = (x, y, z, tone = "mid") => box({ x, y, w: 7, d: 7, r: 1 }, z, 4, { tone, bevel: 0.3 });
  const ux = (F) => [{ x: F.x + 8, y: F.y + 12, w: 40, d: 22, r: 2 }, { x: F.x + 62, y: F.y + 12, w: 40, d: 22, r: 2 }];
  const [X1, X2] = ux(FX), [Y1, Y2] = ux(FY);
  const plainUnit = (U, z) => [box(U, z, 12, { tone: "hi", bevel: 0.5 })].join("");
  const ports = (U, z, skip) => [0, 1, 2].filter((i) => i !== skip).map((i) => port(U.x + 5 + i * 11, U.y + 7.5, z)).join("");
  out.push(hot("famX", [box(FX, 0, 4, { tone: "lo", bevel: 0.5 }), L(k.planOutline(k.insetPlan(FX, 4), 4, P), { tone: "faint" }), labelX("FAMILY X", FX.x + FX.w, FX.y + FX.d / 2, 0.4, { px: 3.2 })].join("")));
  out.push(B.wire([X1.x + X1.w, X1.y + 11, 10], [X2.x, X2.y + 11, 10], [], { tone: "mid" }));
  out.push(hot("famX", [plainUnit(X1, 4), ports(X1, 16), labelY("X · V1", X1.x + X1.w / 2, X1.y + X1.d, 6, { px: 3, plate: false })].join("")));
  out.push(hot("famX", [plainUnit(X2, 4), ports(X2, 16, 1), labelY("X · SIBLING", X2.x + X2.w / 2, X2.y + X2.d, 6, { px: 3, plate: false })].join("")));
  out.push(B.wire([-86, -30, 4], [X1.x, X1.y + 11, 10], [[-70, -30, 1], [-70, X1.y + 11, 1]], { tone: "mid" }));
  out.push(hot("famY", [box(FY, 0, 4, { tone: "lo", bevel: 0.5 }), L(k.planOutline(k.insetPlan(FY, 4), 4, P), { tone: "faint" }), labelX("FAMILY Y", FY.x + FY.w, FY.y + FY.d / 2, 0.4, { px: 3.2 })].join("")));
  out.push(hot("famY", [plainUnit(Y1, 4), ports(Y1, 16), labelY("Y · V5", Y1.x + Y1.w / 2, Y1.y + Y1.d, 6, { px: 3, plate: false })].join("")));
  out.push(show("edge", B.wire([X2.x + 20, X2.y + X2.d, 8], [Y2.x + 20, Y2.y, 8], [[X2.x + 20, X2.y + X2.d + 8, 1], [Y2.x + 20, Y2.y - 6, 1]], { tone: "mid", flow: true })));
  out.push(hot("famY", [plainUnit(Y2, 4), ports(Y2, 16, 1), liveY("yv", "Y · V5", Y2.x + Y2.w / 2, Y2.y + Y2.d, 6, { px: 3 })].join("")));
  out.push(hot("tries", [box({ x: FY.x + 60, y: FY.y + FY.d - 1, w: 50, d: 5, r: 0.8 }, 0, 9, { tone: "mid" }), liveY("tries", "TRIES 14", FY.x + 85, FY.y + FY.d + 4, 2.6, { px: 3.4 })].join("")));

  // other unit kinds at the right
  const KX = 66;
  out.push(hot("kinds", [box({ x: KX, y: -86, w: 70, d: 116, r: 3 }, 0, 4, { tone: "lo", bevel: 0.5 }),
    cyl(KX + 22, -64, 13, 4, 18, { tone: "hi", bevel: 0.5 }), L(k.ring(KX + 22, -64, 8, 22, P, 24), { tone: "lo" }), labelTop("ML MODEL", KX + 46, -64, 4, { px: 3.2 }),
    box({ x: KX + 8, y: -36, w: 30, d: 22, r: 2 }, 4, 14, { tone: "hi", bevel: 0.5 }), box({ x: KX + 12, y: -32, w: 22, d: 14, r: 1 }, 18, 1, { tone: "lo" }), labelTop("MINI APP", KX + 46, -25, 4, { px: 3.2 }),
    box({ x: KX + 8, y: -6, w: 30, d: 22, r: 2 }, 4, 12, { tone: "hi", bevel: 0.5 }), labelTop("PY", KX + 23, 5, 16, { px: 5 }), labelTop("PYTHON", KX + 48, 5, 4, { px: 3.2 }),
    labelY("SAME LINEAGE · SAME JUDGE", KX + 35, 30, 0.6, { px: 3, plate: false })].join("")));

  // the transplanted port block, drawn last
  const from = [X2.x + 16, X2.y + 7.5, 16];
  out.push(hot("block", move("block", `<g data-cls="blk">${port(from[0], from[1], from[2], "hi")}</g>`)));
  const dyY = Y2.y - X2.y;

  const svg = svgOf(B, { label: "A shelf of sources (video, post, chat, your dictation) feeds an idea record. Behind, family X holds a unit and its sibling; in front, family Y holds two units. A port block lifts out of family X's sibling and sets into family Y's second unit, which becomes version 6 with a transplanted-from link and one more try. At the right stand an ML model, a mini app and a plain Python unit.", body: out });
  const labels = { sources: "Sources: video, post, article, chat, copilot chat, your dictation, a workflow.", idea: "Idea record: class, source with its exact spot, claims. Not runnable.", famX: "Family X: everything grown from one idea.", famY: "Family Y.", block: "A named port: setup, entry, invalidation, exit, regime.", tries: "Every transplant counts as a try in the family that receives it.", kinds: "Plain Python, ML models and mini apps: never blocked; flagged 'outside the standard'." };
  const base = { move: { block: [0, 0, 0] }, show: { edge: false }, text: { yv: "Y · V5", tries: "TRIES 14" }, lamps: { idea: "off" }, cls: { blk: "" } };
  const modes = { main: [
    { say: "Every unit starts from a source: a video, a post, a chat, your words.", lit: ["sources"], ...base, ms: 3000 },
    { say: "An idea record sits in front: class, source with its exact spot, claims.", lit: ["idea"], lamps: { idea: "ok" }, ms: 3200 },
    { say: "Units built from it form a family: versions and siblings.", lit: ["famX"], ms: 3000 },
    { say: "Transplant: one part leaves family X through a named port.", lit: ["block"], cls: { blk: "ok" }, move: { block: [0, 0, 16] }, ms: 3000 },
    { say: "…and goes into family Y.", lit: ["block", "famY"], move: { block: [0, dyY, 16] }, ms: 2800 },
    { say: "Y becomes version 6, linked 'transplanted from X'. One more try in Y.", lit: ["famY", "tries"], move: { block: [0, dyY, 0] }, show: { edge: true }, text: { yv: "Y · V6", tries: "TRIES 15" }, ms: 3600 },
    { say: "Plain Python, ML models and mini apps: same lineage, same judge.", lit: ["kinds"], ms: 3200 },
  ] };
  return { svg, P, labels, init: base, modes: modesOf(modes), ease: 0.55 };
}
