import { describe, expect, it } from "vitest";
import { LIBRARY, PLACES, SHELVES } from "./items";

const ROUTES = ["/lab", "/portfolio", "/copilot", "/home", "/library"];

describe("Library catalogue", () => {
  it("gives every item a unique id and a real shelf", () => {
    const ids = LIBRARY.map((i) => i.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const i of LIBRARY)
      expect(SHELVES.some((s) => s.id === i.shelf)).toBe(true);
  });

  it("only links to screens that exist", () => {
    for (const i of LIBRARY)
      for (const u of [...i.uses, ...(i.starts ? [i.starts] : [])]) {
        expect(ROUTES).toContain(u.path);
        expect(PLACES).toContain(u.place);
      }
  });

  it("connects the trading things to Lab or Portfolio", () => {
    const trading = LIBRARY.filter((i) => ["bots", "pods"].includes(i.shelf));
    for (const i of trading)
      expect(
        i.uses.some((u) => u.place === "Lab" || u.place === "Portfolio"),
      ).toBe(true);
  });
});
