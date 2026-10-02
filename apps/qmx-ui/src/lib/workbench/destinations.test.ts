import { describe, expect, it } from "vitest";
import { PRODUCT_DESTINATIONS, isActive } from "./destinations";

describe("platform rail destinations", () => {
  it("keeps the four product destinations in rail order", () => {
    expect(PRODUCT_DESTINATIONS.map((d) => d.id)).toEqual([
      "home",
      "copilot",
      "library",
      "lab",
    ]);
  });

  it("marks nested routes active without matching prefixes of other words", () => {
    expect(isActive("/apps/a1", "/apps/a1")).toBe(true);
    expect(isActive("/apps/a1/detail", "/apps/a1")).toBe(true);
    expect(isActive("/apps/a10", "/apps/a1")).toBe(false);
  });
});
