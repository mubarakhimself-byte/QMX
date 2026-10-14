import { describe, expect, it } from "vitest";
import { settings } from "./settings.svelte";

describe("settings: what a copilot may use", () => {
  it("offers models only from providers that are on and allowed", () => {
    expect(settings.modelsFor("portfolio").map((m) => m.value)).toEqual([
      "claude-plan/Opus 5.5",
      "claude-plan/Sonnet 5.5",
      "claude-plan/Haiku 5.5",
    ]);
    settings.setUse("portfolio", "ollama", true);
    expect(settings.modelsFor("portfolio").map((m) => m.value)).toContain(
      "ollama/qwen",
    );
    settings.providers.find((p) => p.id === "ollama")!.on = false;
    expect(settings.modelsFor("portfolio").map((m) => m.value)).not.toContain(
      "ollama/qwen",
    );
  });

  it("keeps one relation: allowing a tool shows the copilot as its user", () => {
    expect(settings.usersOf("github").map((c) => c.id)).toEqual(["lab"]);
    settings.setUse("library", "github", true);
    expect(settings.usersOf("github").map((c) => c.id)).toEqual([
      "lab",
      "library",
    ]);
    expect(settings.copilot("library").uses).toContain("github");
    settings.setUse("library", "github", false);
    expect(settings.usersOf("github").map((c) => c.id)).toEqual(["lab"]);
  });
});
