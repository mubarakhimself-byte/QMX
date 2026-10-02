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
  /** Built-in app routes (e.g. /trade) override the default /apps/<id>. */
  href?: string;
  icon?: "chart" | "node" | "lab" | "ml";
  attention?: "running" | "unknown" | "failed";
};

export const DEMO_APPS: OpenedApp[] = [
  {
    instanceId: "demo-research",
    label: "Research (demo)",
    icon: "chart",
    attention: "running",
  },
  {
    instanceId: "demo-trade",
    label: "Trading node (demo)",
    icon: "node",
    href: "/trade",
  },
  {
    instanceId: "demo-lab",
    label: "Backtest lab (demo)",
    icon: "lab",
    attention: "running",
  },
  { instanceId: "demo-ml", label: "ML Studio (demo)", icon: "ml" },
];

/**
 * Model and tool choices shown in the composer. The real lists come from
 * the daemon's provider and tool registry; these are the demo defaults.
 */
export const MODELS = [
  {
    id: "opus",
    label: "Opus 5.5",
    note: "Most careful; long research and builds",
  },
  {
    id: "sonnet",
    label: "Sonnet 5.5",
    note: "Fast and capable; everyday work",
  },
  {
    id: "haiku",
    label: "Haiku 4.5",
    note: "Quickest; lookups and small edits",
  },
];
export const TOOLS = [
  { id: "get_candles", note: "Read price history" },
  { id: "run_backtest", note: "Backtest a published workflow" },
  { id: "library.search", note: "Search your Library" },
  { id: "web.browse", note: "Open pages in the preview browser" },
  { id: "build_app", note: "Compose a mini app from the component catalog" },
];

/**
 * What the copilot can reach (docs: published ∩ granted ∩ healthy). Each
 * target lists its operations and where it stands on the five listing
 * axes. Demo values; the daemon's listing replaces them.
 */
export const TARGETS = [
  {
    id: "research-fx",
    name: "Research · FX",
    kind: "Mini app",
    ops: ["fx.quote", "fx.signals", "fx.correlation"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "calendar-sync",
    name: "Calendar sync",
    kind: "Headless app",
    ops: ["calendar.refresh", "calendar.windows"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "lab",
    name: "Backtest lab",
    kind: "Mini app",
    ops: ["qmb.backtest", "qmb.walk_forward", "qmb.robustness"],
    axes: {
      published: true,
      configured: true,
      granted: false,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "paper-node",
    name: "Paper node",
    kind: "Trading node",
    ops: ["node.status", "node.journal"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "live-node",
    name: "Live node",
    kind: "Trading node",
    ops: ["node.status"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: false,
      healthy: false,
    },
  },
] as const;
export type TargetId = (typeof TARGETS)[number]["id"];

export const THEMES = [
  "ink",
  "cobalt",
  "ember",
  "graphite",
  "moss",
  "violet",
  "paper",
] as const;
export type Theme = (typeof THEMES)[number];

function storedFlag(key: string, fallback: boolean): boolean {
  try {
    const v = localStorage.getItem(key);
    return v === null ? fallback : v === "1";
  } catch {
    return fallback;
  }
}

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
  model = $state("opus");
  /** The app or node a message is aimed at; none = the copilot decides. */
  target = $state<TargetId | null>(null);
  /** Default model per copilot profile; the daemon owns the real setting. */
  modelDefaults = $state<Record<string, string>>({
    copilot: "opus",
    app: "sonnet",
    agent: "haiku",
  });
  /** Decorative ink background on/off (per machine). */
  inkEnabled = $state(storedFlag("qmx.ink", true));

  setInk(on: boolean) {
    this.inkEnabled = on;
    try {
      localStorage.setItem("qmx.ink", on ? "1" : "0");
    } catch {
      /* storage unavailable */
    }
  }
  tools = $state<string[]>(["get_candles", "run_backtest", "library.search"]);

  toggleTool(id: string) {
    this.tools = this.tools.includes(id)
      ? this.tools.filter((t) => t !== id)
      : [...this.tools, id];
  }

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

  /** Short confirmation shown after an action (e.g. added to copilot). */
  notice = $state<{ text: string; href?: string; action?: string } | null>(
    null,
  );
  #noticeTimer: ReturnType<typeof setTimeout> | undefined;

  notify(text: string, href?: string, action?: string) {
    this.notice = { text, href, action };
    clearTimeout(this.#noticeTimer);
    this.#noticeTimer = setTimeout(() => (this.notice = null), 4000);
  }

  addRef(label: string) {
    if (!this.copilotRefs.includes(label))
      this.copilotRefs = [...this.copilotRefs, label];
    this.notify(`Added to copilot: ${label}`, "/copilot", "Open Copilot");
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
