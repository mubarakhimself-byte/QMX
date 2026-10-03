import { describe, expect, it } from "vitest";
import {
  DEFAULT_CUSTOM,
  parseCustom,
  parseRotation,
  parseSurface,
} from "./look";

describe("look settings", () => {
  it("falls back to defaults for junk", () => {
    expect(parseCustom("nope")).toEqual(DEFAULT_CUSTOM);
    expect(parseSurface("chrome")).toBe("glass");
    expect(parseRotation(7)).toBe("off");
  });

  it("clamps numbers and rejects bad colours", () => {
    const c = parseCustom({
      on: true,
      accent: "red",
      panel: 3,
      radius: -4,
      text: 30,
    });
    expect(c).toMatchObject({
      on: true,
      accent: DEFAULT_CUSTOM.accent,
      panel: 1,
      radius: 0,
      text: 18,
    });
  });

  it("keeps valid values", () => {
    expect(
      parseCustom({ on: true, accent: "#12ab34", background: "#000000" }),
    ).toMatchObject({
      accent: "#12ab34",
      background: "#000000",
    });
    expect(parseSurface("brutal")).toBe("brutal");
    expect(parseRotation("daily")).toBe("daily");
  });
});
