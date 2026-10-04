import { describe, expect, it } from "vitest";
import { LAB_PANELS } from "./catalog";
import { BUILTIN_LAYOUTS } from "./lab.svelte";
import { panes } from "$lib/workbench/tiles/tiles";

describe("Lab panels", () => {
  it("every built-in layout uses only panels the Lab provides", () => {
    for (const l of BUILTIN_LAYOUTS)
      for (const p of panes(l.root))
        expect(LAB_PANELS[p.panel], `${l.id}: ${p.panel}`).toBeDefined();
  });
});
