import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  FIRST_PARTY_SVELTE_HOST_AT_INSPECT,
  INSPECT_SHA,
  PLATFORM_RAIL_AT_INSPECT,
} from "../inspect";
import {
  PRODUCT_DESTINATION_COUNT,
  PRODUCT_DESTINATION_IDS,
  PRODUCT_DESTINATIONS,
  PRODUCT_SESSION_PROFILES,
  SETTINGS_CHROME,
  destinationFromPath,
  isProductDestination,
  profileForDestination,
} from "./destinations";

const srcRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

describe("platform destinations", () => {
  it("keeps four product destinations above Settings chrome", () => {
    expect(PRODUCT_DESTINATION_IDS).toEqual([
      "home",
      "copilot",
      "library",
      "authoring",
    ]);
    expect(PRODUCT_DESTINATIONS.map((item) => item.id)).toEqual([
      ...PRODUCT_DESTINATION_IDS,
    ]);
    expect(PRODUCT_DESTINATIONS).toHaveLength(PRODUCT_DESTINATION_COUNT);
    expect(SETTINGS_CHROME.kind).toBe("chrome");
    expect(isProductDestination("settings")).toBe(false);
    expect(PRODUCT_DESTINATIONS.every((item) => item.kind === "product")).toBe(
      true,
    );
  });

  it("does not mint a third ProductSessionProfile", () => {
    expect(PRODUCT_SESSION_PROFILES).toEqual(["authoring", "app-use"]);
    expect(profileForDestination("home")).toBe("authoring");
    expect(profileForDestination("authoring")).toBe("authoring");
    expect(profileForDestination("copilot")).toBeUndefined();
    expect(profileForDestination("library")).toBeUndefined();
  });

  it("maps paths independently of opened apps", () => {
    expect(destinationFromPath("/home")).toBe("home");
    expect(destinationFromPath("/copilot/")).toBe("copilot");
    expect(destinationFromPath("/library")).toBe("library");
    expect(destinationFromPath("/authoring")).toBe("authoring");
    expect(destinationFromPath("/settings")).toBe("settings");
    expect(destinationFromPath("/")).toBeNull();
  });

  it("proves PlatformRail after this story and absent at inspect", () => {
    expect(INSPECT_SHA).toBe("34c148be404a375cbfd79fd4ce6997452e4f1d20");
    expect(FIRST_PARTY_SVELTE_HOST_AT_INSPECT).toBe(false);
    expect(PLATFORM_RAIL_AT_INSPECT).toBe(false);
    expect(existsSync(join(srcRoot, "lib/shell/PlatformRail.svelte"))).toBe(
      true,
    );
    const rail = readFileSync(
      join(srcRoot, "lib/shell/PlatformRail.svelte"),
      "utf8",
    );
    expect(rail).toContain('data-emits="select_destination"');
    expect(rail).toContain("rail-product-destinations");
    expect(rail).toContain("rail-opened-apps");
    expect(rail).toContain('data-kind="chrome"');
  });
});
