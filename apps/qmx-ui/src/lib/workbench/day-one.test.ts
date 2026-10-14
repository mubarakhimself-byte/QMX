import { describe, expect, it } from "vitest";
import { LAB_PANELS } from "$lib/lab/catalog";
import { PORTFOLIO_PANELS } from "$lib/portfolio/catalog";
import { HOME_PANELS } from "$lib/home/catalog";
import { DAY_ONE, FIRST, GET_STARTED } from "./day-one";

const ROUTES = ["/settings", "/library", "/copilot"];

describe("day one", () => {
  it("every board panel has a one-line empty state and an action", () => {
    const ids = [
      ...Object.keys(LAB_PANELS),
      ...Object.keys(PORTFOLIO_PANELS),
      ...Object.keys(HOME_PANELS),
    ];
    const missing = ids.filter((id) => !DAY_ONE[id]);
    expect(missing).toEqual([]);
    for (const [id, d] of Object.entries(DAY_ONE))
      expect(d.line.split(" ").length, id).toBeLessThanOrEqual(8);
  });

  it("every action lands on a real screen", () => {
    for (const a of Object.values(FIRST))
      expect(ROUTES, a.label).toContain(a.href.split("?")[0]);
  });

  it("get started has the four first steps in order", () => {
    expect(GET_STARTED.map((s) => s.label)).toEqual([
      "Connect a broker",
      "Pick a model provider",
      "Add a data source",
      "Start a strategy or pod",
    ]);
  });
});
