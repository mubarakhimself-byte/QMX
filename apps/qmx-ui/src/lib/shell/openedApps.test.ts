import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  CLOSE_APP_UNMOUNT,
  FACTORY_TEST_HEADLESS_PACK,
  FACTORY_TEST_MIXED_APP,
  FACTORY_TEST_VISUAL_APP,
  closeApp,
  showsNavigationPane,
  showsOpenedAppIcon,
} from "./openedApps";
import {
  addOpenedApp,
  closeOpenedApp,
  resetOpenedApps,
  selectDestination,
} from "./shellState";

const here = dirname(fileURLToPath(import.meta.url));

describe("opened apps and close_app", () => {
  it("unmounts with wire.detach and does not cancel jobs or the daemon", () => {
    const { remaining, event } = closeApp(
      [FACTORY_TEST_VISUAL_APP],
      FACTORY_TEST_VISUAL_APP.instanceId,
    );
    expect(remaining).toEqual([]);
    expect(event.type).toBe("close_app");
    expect(event.unmount).toBe(CLOSE_APP_UNMOUNT);
    expect(event.unmount).toBe("wire.detach");
    expect(event.cancelledJobHandles).toBe(false);
    expect(event.stoppedDaemon).toBe(false);
    const src = [
      readFileSync(join(here, "openedApps.ts"), "utf8"),
      readFileSync(join(here, "shellState.ts"), "utf8"),
    ].join("\n");
    expect(src).not.toMatch(/dispatchCancel|cancel_job|JobHandle\.cancel/);
    expect(src).not.toMatch(/stop_daemon|spawn\(/);
  });

  it("keeps headless packs first-class without an icon or navigation pane", () => {
    expect(showsOpenedAppIcon(FACTORY_TEST_HEADLESS_PACK)).toBe(false);
    expect(showsNavigationPane(FACTORY_TEST_HEADLESS_PACK)).toBe(false);
    expect(showsOpenedAppIcon(FACTORY_TEST_VISUAL_APP)).toBe(true);
    expect(showsOpenedAppIcon(FACTORY_TEST_MIXED_APP)).toBe(true);
    expect(FACTORY_TEST_MIXED_APP.copilotProfile).toBe("app-use");
    expect(FACTORY_TEST_VISUAL_APP.badge?.cancelAuthority).toBe(false);
  });

  it("records select_destination and chrome-only close_app on the shell store", () => {
    resetOpenedApps();
    const selected = selectDestination("home");
    expect(selected.lastEvent).toEqual({
      type: "select_destination",
      destination: "home",
    });
    expect(selected.productDestinationCount).toBe(4);
    expect(selected.settingsIsProduct).toBe(false);
    addOpenedApp(FACTORY_TEST_HEADLESS_PACK);
    addOpenedApp(FACTORY_TEST_VISUAL_APP);
    const withApps = closeOpenedApp(FACTORY_TEST_VISUAL_APP.instanceId);
    expect(withApps.openedAppIconCount).toBe(0);
    expect(withApps.headlessPackCount).toBe(1);
    expect(withApps.navigationPaneCount).toBe(0);
    expect(withApps.lastEvent?.type).toBe("close_app");
    expect(withApps.cancelledJobHandles).toBe(false);
    resetOpenedApps();
  });
});
