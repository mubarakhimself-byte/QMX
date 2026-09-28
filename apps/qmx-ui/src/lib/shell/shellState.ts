import { get, writable } from "svelte/store";
import {
  PRODUCT_DESTINATION_COUNT,
  type ProductDestinationId,
} from "./destinations";
import {
  CLOSE_APP_UNMOUNT,
  FACTORY_TEST_HEADLESS_PACK,
  FACTORY_TEST_VISUAL_APP,
  closeApp,
  showsNavigationPane,
  showsOpenedAppIcon,
  type ChromeEvent,
  type OpenedApp,
} from "./openedApps";

export type ShellSnapshot = {
  selectedDestination: ProductDestinationId | "settings" | null;
  lastEvent: ChromeEvent | null;
  openedAppIconCount: number;
  headlessPackCount: number;
  navigationPaneCount: number;
  productDestinationCount: typeof PRODUCT_DESTINATION_COUNT;
  settingsIsProduct: false;
  closeUnmount: typeof CLOSE_APP_UNMOUNT;
  cancelledJobHandles: false;
  openedApps: OpenedApp[];
};

function snapshot(
  openedApps: OpenedApp[],
  selectedDestination: ProductDestinationId | "settings" | null,
  lastEvent: ChromeEvent | null,
): ShellSnapshot {
  const icons = openedApps.filter(showsOpenedAppIcon);
  const headless = openedApps.filter((app) => !showsOpenedAppIcon(app));
  return {
    selectedDestination,
    lastEvent,
    openedAppIconCount: icons.length,
    headlessPackCount: headless.length,
    navigationPaneCount: openedApps.filter(showsNavigationPane).length,
    productDestinationCount: PRODUCT_DESTINATION_COUNT,
    settingsIsProduct: false,
    closeUnmount: CLOSE_APP_UNMOUNT,
    cancelledJobHandles: false,
    openedApps,
  };
}

const initial = snapshot([], null, null);
export const shellState = writable<ShellSnapshot>(initial);

function commit(
  openedApps: OpenedApp[],
  selectedDestination: ProductDestinationId | "settings" | null,
  lastEvent: ChromeEvent | null,
): ShellSnapshot {
  const next = snapshot(openedApps, selectedDestination, lastEvent);
  shellState.set(next);
  return next;
}

export function getShellState(): ShellSnapshot {
  return get(shellState);
}

export function selectDestination(
  destination: ProductDestinationId,
): ShellSnapshot {
  const current = get(shellState);
  return commit(current.openedApps, destination, {
    type: "select_destination",
    destination,
  });
}

export function openSettingsChrome(): ShellSnapshot {
  const current = get(shellState);
  return commit(current.openedApps, "settings", current.lastEvent);
}

export function setSelectedFromPath(
  destination: ProductDestinationId | "settings" | null,
): void {
  const current = get(shellState);
  if (current.selectedDestination === destination) return;
  commit(current.openedApps, destination, current.lastEvent);
}

export function addOpenedApp(app: OpenedApp): ShellSnapshot {
  const current = get(shellState);
  if (current.openedApps.some((item) => item.instanceId === app.instanceId)) {
    return current;
  }
  return commit(
    [...current.openedApps, app],
    current.selectedDestination,
    current.lastEvent,
  );
}

export function closeOpenedApp(instanceId: string): ShellSnapshot {
  const current = get(shellState);
  const { remaining, event } = closeApp(current.openedApps, instanceId);
  return commit(remaining, current.selectedDestination, event);
}

export function resetOpenedApps(): ShellSnapshot {
  const current = get(shellState);
  return commit([], current.selectedDestination, current.lastEvent);
}

export function applyOpenedAppFixture(raw: string | null): void {
  if (raw === "opened-visual") addOpenedApp(FACTORY_TEST_VISUAL_APP);
  if (raw === "opened-headless") addOpenedApp(FACTORY_TEST_HEADLESS_PACK);
}
