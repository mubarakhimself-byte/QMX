import { describe, expect, it } from "vitest";
import { deepestDip, growth, ladderMult, replay } from "./sizing-math";

const ladder = [
  { at: 5, mult: 0.5 },
  { at: 10, mult: 0.25 },
];

describe("ladderMult", () => {
  it("cuts size at each step below the peak", () => {
    expect(ladderMult(2, ladder)).toBe(1);
    expect(ladderMult(5, ladder)).toBe(0.5);
    expect(ladderMult(12, ladder)).toBe(0.25);
  });
});

describe("replay", () => {
  it("returns the same curve when nothing changes", () => {
    const { curve } = replay([100, 110, 99], { scale: 1 });
    expect(curve.map((v) => Math.round(v * 1e6) / 1e6)).toEqual([100, 110, 99]);
  });

  it("doubles each return when risk doubles", () => {
    const { curve } = replay([100, 110, 99], { scale: 2 });
    expect(curve[1]).toBeCloseTo(120);
    expect(curve[2]).toBeCloseTo(96);
  });

  it("halves a loss once the dip passes a ladder step", () => {
    // 100 → 90 is a 10% fall; the next 10% fall is cut to a quarter.
    const { curve } = replay([100, 90, 81], { scale: 1, ladder });
    expect(curve[2]).toBeCloseTo(87.75);
  });

  it("stands down at the kill line and stays flat", () => {
    const { curve, stoodDownAt } = replay([100, 80, 60, 120], {
      scale: 1,
      killAt: 15,
    });
    expect(stoodDownAt).toBe(1);
    expect(curve).toEqual([100, 80, 80, 80]);
  });
});

describe("figures", () => {
  it("measures growth and the deepest dip", () => {
    expect(growth([100, 120])).toBeCloseTo(20);
    expect(deepestDip([100, 120, 90, 130])).toBeCloseTo(25);
  });
});

describe("replay with the ladder it was made with", () => {
  it("undoes the ladder the curve was made with", () => {
    const made = replay([100, 90, 81], { scale: 1, ladder }).curve;
    const back = replay(made, { scale: 1, made: ladder }).curve;
    expect(back[2]).toBeCloseTo(81);
  });
});
