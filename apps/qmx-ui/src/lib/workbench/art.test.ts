import { describe, expect, it } from "vitest";
import {
  ART_STYLES,
  BUILTIN_PRESETS,
  DEFAULT_ART,
  buildScene,
  parseArt,
  parsePresets,
} from "./art";

describe("background art", () => {
  it("falls back to the default for junk input", () => {
    expect(parseArt(null)).toEqual(DEFAULT_ART);
    expect(parseArt({ style: "plasma", glow: 3 })).toEqual(DEFAULT_ART);
  });

  it("clamps numbers into range", () => {
    const c = parseArt({
      style: "candles",
      density: 9,
      strength: -1,
      seed: 1.6,
    });
    expect(c).toMatchObject({
      style: "candles",
      density: 2,
      strength: 0.3,
      seed: 2,
    });
  });

  it("drops malformed saved presets and repairs configs", () => {
    const out = parsePresets([
      { id: "u-1", name: "Mine", config: { style: "contour", density: 0.1 } },
      { name: "no id" },
      "junk",
    ]);
    expect(out).toHaveLength(1);
    expect(out[0].config).toMatchObject({ style: "contour", density: 0.5 });
  });

  it("draws every style deterministically", () => {
    for (const s of ART_STYLES) {
      const c = { ...DEFAULT_ART, style: s.id };
      const a = buildScene(c);
      expect(a.strokes.length + a.fills.length).toBeGreaterThan(0);
      expect(a).toEqual(buildScene(c));
      expect(JSON.stringify(a)).not.toContain("NaN");
    }
  });

  it("ships one built-in preset per style", () => {
    expect(new Set(BUILTIN_PRESETS.map((p) => p.config.style)).size).toBe(
      ART_STYLES.length,
    );
  });
});
