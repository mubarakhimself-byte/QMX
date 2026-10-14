import { describe, expect, it } from "vitest";
import { podModel } from "./pod-model.svelte";

describe("podModel", () => {
  it("doubling risk doubles the sized trade and deepens the test", () => {
    const before = podModel.trail("trend")[0].usd;
    const dip = podModel.attr("dip", "trend");
    podModel.set("trend", "fixed-frac", "risk", 1.5);
    expect(podModel.trail("trend")[0].usd).toBeCloseTo(before * 2);
    expect(podModel.scale("trend")).toBeCloseTo(2);
    expect(podModel.attr("dip", "trend")).toBeLessThan(dip);
    expect(podModel.setting("trend", "fixed-frac")).toBe("1.5%");
    expect(podModel.isDirty("trend")).toBe(true);
  });

  it("saving keeps the edit and clears the draft; discard returns to it", () => {
    expect(podModel.save("trend")).toBe("v3");
    expect(podModel.isDirty("trend")).toBe(false);
    podModel.set("trend", "kill", "kill", 30);
    podModel.discard("trend");
    expect(podModel.kill("trend")).toBe(15);
    expect(podModel.get("trend", "fixed-frac", "risk")).toBe(1.5);
  });

  it("a tighter kill line makes the stress board stand down sooner", () => {
    const loose = podModel.stress("classic", "flash")!;
    expect(loose.stoodDown).toBe(false);
    podModel.set("classic", "kill", "kill", 10);
    expect(podModel.stress("classic", "flash")!.stoodDown).toBe(true);
  });

  it("extending a soak adds days and un-readies the run", () => {
    expect(podModel.paper("voltarget").ready).toBe(true);
    podModel.paperExtra.voltarget = 7;
    const run = podModel.paper("voltarget");
    expect(run.of).toBe(14);
    expect(run.ready).toBe(false);
  });
});
