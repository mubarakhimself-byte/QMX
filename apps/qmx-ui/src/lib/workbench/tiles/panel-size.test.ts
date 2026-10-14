import { describe, expect, it } from "vitest";
import { sizeMode } from "./panel-size";

describe("sizeMode", () => {
  it("is expanded whenever the tile is maximised", () => {
    expect(sizeMode({ width: 100, height: 100 }, 17, true)).toBe("expanded");
  });
  it("is compact when either side is short", () => {
    expect(sizeMode({ width: 400, height: 600 }, 17, false)).toBe("compact");
    expect(sizeMode({ width: 900, height: 200 }, 17, false)).toBe("compact");
  });
  it("is regular for a normal tile and expanded for a very large one", () => {
    expect(sizeMode({ width: 760, height: 370 }, 17, false)).toBe("regular");
    expect(sizeMode({ width: 1500, height: 700 }, 17, false)).toBe("expanded");
  });
  it("reaches compact sooner at a larger text size", () => {
    expect(sizeMode({ width: 430, height: 400 }, 17, false)).toBe("regular");
    expect(sizeMode({ width: 430, height: 400 }, 19, false)).toBe("compact");
  });
});
