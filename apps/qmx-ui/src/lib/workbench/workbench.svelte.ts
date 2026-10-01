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

export const DEMO_APPS: OpenedApp[] = [
  {
    instanceId: "demo-research",
    label: "Research (demo)",
    attention: "running",
  },
];

export const THEMES = ["ink", "cobalt", "ember", "plain"] as const;
export type Theme = (typeof THEMES)[number];

function storedTheme(): Theme {
  try {
    const t = localStorage.getItem("qmx.theme");
    return (THEMES as readonly string[]).includes(t ?? "")
      ? (t as Theme)
      : "ink";
  } catch {
    return "ink";
  }
}

class Workbench {
  /** Visual theme: a per-machine preference, never a daemon setting. */
  theme = $state<Theme>(storedTheme());

  setTheme(t: Theme) {
    this.theme = t;
    try {
      localStorage.setItem("qmx.theme", t);
    } catch {
      /* storage unavailable: theme lasts for this window only */
    }
  }

  connection = $state<ConnectionState>("not-bound");
  /** Instances come from the daemon listing; empty until a transport exists. */
  openedApps = $state<OpenedApp[]>([]);
  /**
   * Demo mode shows labelled sample apps and data for design review.
   * Off means the rail shows only daemon instances.
   */
  demoMode = $state(true);
  /**
   * Message-only context chips a widget added to a copilot composer
   * (UI CHAT §8): not durable refs, not a send, cleared on use.
   */
  copilotRefs = $state<string[]>([]);

  addRef(label: string) {
    if (!this.copilotRefs.includes(label))
      this.copilotRefs = [...this.copilotRefs, label];
  }

  removeRef(label: string) {
    this.copilotRefs = this.copilotRefs.filter((r) => r !== label);
  }

  /** Rail entries: daemon instances, plus demo apps while demo mode is on. */
  get railApps(): OpenedApp[] {
    return this.demoMode ? [...DEMO_APPS, ...this.openedApps] : this.openedApps;
  }

  /** Chrome-only close: unmounts the app view, never cancels its jobs. */
  closeApp(instanceId: string) {
    this.openedApps = this.openedApps.filter(
      (a) => a.instanceId !== instanceId,
    );
  }
}

export const workbench = new Workbench();
