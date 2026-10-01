/**
 * Client-local workbench chrome state. Layout only: nothing here is a
 * daemon identity, and nothing here pretends a backend answered.
 */

/** Transport state shown in the status bar. No transport is bound yet. */
export type ConnectionState =
  "not-bound" | "connecting" | "connected" | "reconnecting" | "failed";

/** An opened mini-app instance as the rail shows it (below the divider). */
export type OpenedApp = {
  instanceId: string;
  label: string;
  attention?: "running" | "unknown" | "failed";
};

class Workbench {
  connection = $state<ConnectionState>("not-bound");
  /** Instances come from the daemon listing; empty until a transport exists. */
  openedApps = $state<OpenedApp[]>([]);

  /** Chrome-only close: unmounts the app view, never cancels its jobs. */
  closeApp(instanceId: string) {
    this.openedApps = this.openedApps.filter(
      (a) => a.instanceId !== instanceId,
    );
  }
}

export const workbench = new Workbench();
