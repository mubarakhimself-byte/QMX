import { describe, expect, it } from "vitest";
import { GROUPS, TEMPLATES, apps } from "./apps.svelte";
import { ICONS } from "./icons";

const status = (id: string) => apps.status(apps.byId(id)!);

describe("apps: where each one stands", () => {
  it("reads live, stopped, needs a look, proving and being built", () => {
    expect(status("news")).toBe("live");
    expect(status("exchange-status")).toBe("stopped");
    expect(status("dca")).toBe("attention");
    expect(status("spreads")).toBe("proving");
    expect(status("correlation")).toBe("building");
  });

  it("safe mode turns every app off and back", () => {
    apps.safe = true;
    expect(apps.all.every((a) => apps.status(a) === "off")).toBe(true);
    apps.safe = false;
    expect(status("news")).toBe("live");
  });

  it("restart brings a stopped app back to live", () => {
    apps.restart("exchange-status");
    expect(status("exchange-status")).toBe("live");
    expect(apps.byId("exchange-status")!.log[0]).toBe("now restarted by you");
  });
});

describe("apps: pins", () => {
  it("pins and unpins an app", () => {
    expect(apps.pinned("screener")).toBe(false);
    apps.pin("screener");
    expect(apps.pinned("screener")).toBe(true);
    apps.pin("screener");
    expect(apps.pinned("screener")).toBe(false);
  });
});

describe("apps: making one", () => {
  it("an app made from widgets starts at Build with those widgets", () => {
    const id = apps.fromWidgets("My desk", ["markets", "positions"]);
    const a = apps.byId(id)!;
    expect([a.name, a.stage, a.panels]).toEqual([
      "My desk",
      0,
      ["markets", "positions"],
    ]);
    expect(apps.status(a)).toBe("building");
    apps.remove(id);
    expect(apps.byId(id)).toBeUndefined();
  });

  it("every app and template has a known icon and group", () => {
    for (const t of [...apps.all, ...TEMPLATES]) {
      expect(ICONS[t.icon], t.name).toBeDefined();
      expect(GROUPS[t.group], t.name).toBeDefined();
    }
  });
});
