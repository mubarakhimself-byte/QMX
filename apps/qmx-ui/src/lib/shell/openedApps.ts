/**
 * Opened-app slots live below the rail divider. Headless packs stay
 * first-class without a navigation pane or a required icon (DEC-0471).
 * Chrome close_app unmounts with wire.detach and must not cancel jobs.
 */
import { FACTORY_TEST_LABEL } from "$lib/bootstrap";

export type PackCapability = "visual" | "headless" | "mixed";

export type ObservationBadge = {
  kind: "job_handle" | "listing_axis";
  label: string;
  /** Observation on a badge is not cancel authority. */
  cancelAuthority: false;
};

export type OpenedApp = {
  instanceId: string;
  label: string;
  capability: PackCapability;
  hasView: boolean;
  copilotProfile?: string;
  badge?: ObservationBadge;
};

export const CLOSE_APP_UNMOUNT = "wire.detach" as const;

export type CloseAppEvent = {
  type: "close_app";
  unmount: typeof CLOSE_APP_UNMOUNT;
  cancelledJobHandles: false;
  stoppedDaemon: false;
  instanceId: string;
};

export type SelectDestinationEvent = {
  type: "select_destination";
  destination: "home" | "copilot" | "library" | "authoring";
};

export type ChromeEvent = SelectDestinationEvent | CloseAppEvent;

export function showsOpenedAppIcon(app: OpenedApp): boolean {
  if (app.capability === "headless" && !app.hasView && !app.copilotProfile) {
    return false;
  }
  return app.hasView || Boolean(app.copilotProfile);
}

export function showsNavigationPane(app: OpenedApp): boolean {
  return app.hasView;
}

export function closeApp(
  apps: readonly OpenedApp[],
  instanceId: string,
): { remaining: OpenedApp[]; event: CloseAppEvent } {
  return {
    remaining: apps.filter((app) => app.instanceId !== instanceId),
    event: {
      type: "close_app",
      unmount: CLOSE_APP_UNMOUNT,
      cancelledJobHandles: false,
      stoppedDaemon: false,
      instanceId,
    },
  };
}

export const FACTORY_TEST_VISUAL_APP: OpenedApp = {
  instanceId: "instance:FACTORY-TEST-visual",
  label: `${FACTORY_TEST_LABEL} visual`,
  capability: "visual",
  hasView: true,
  badge: {
    kind: "job_handle",
    label: "queued",
    cancelAuthority: false,
  },
};

export const FACTORY_TEST_HEADLESS_PACK: OpenedApp = {
  instanceId: "instance:FACTORY-TEST-headless",
  label: `${FACTORY_TEST_LABEL} headless`,
  capability: "headless",
  hasView: false,
};

export const FACTORY_TEST_MIXED_APP: OpenedApp = {
  instanceId: "instance:FACTORY-TEST-mixed",
  label: `${FACTORY_TEST_LABEL} mixed`,
  capability: "mixed",
  hasView: true,
  copilotProfile: "app-use",
};
