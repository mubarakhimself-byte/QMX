/**
 * Client-local workbench chrome state. Layout only: nothing here is a
 * daemon identity, and nothing here pretends a backend answered.
 */

import { parseArt, parsePresets, type ArtConfig, type ArtPreset } from "./art";
import {
  parseCustom,
  parseRotation,
  parseSurface,
  type CustomTheme,
  type Rotation,
  type Surface,
} from "./look";

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

export const DEMO_APPS: OpenedApp[] = [];

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
    id: "research-crypto",
    name: "Research · Crypto",
    kind: "Mini app",
    ops: ["crypto.quote", "crypto.signals", "crypto.correlation"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "news-sentiment",
    name: "News & sentiment",
    kind: "Headless app",
    ops: ["news.refresh", "news.windows"],
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
    name: "Lab",
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
    id: "paper-server",
    name: "Paper server",
    kind: "Trading server",
    ops: ["server.status", "server.journal"],
    axes: {
      published: true,
      configured: true,
      granted: true,
      reachable: true,
      healthy: true,
    },
  },
  {
    id: "live-server",
    name: "Live server",
    kind: "Trading server",
    ops: ["server.status"],
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

function storedJson(key: string): unknown {
  try {
    const v = localStorage.getItem(key);
    return v === null ? undefined : JSON.parse(v);
  } catch {
    return undefined;
  }
}

function store(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: lasts for this window only */
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
  /** Background art and the operator's saved variants (per machine). */
  art = $state<ArtConfig>(parseArt(storedJson("qmx.art")));
  artPresets = $state<ArtPreset[]>(parsePresets(storedJson("qmx.art.presets")));

  setArt(c: ArtConfig) {
    this.art = parseArt(c);
    store("qmx.art", this.art);
  }

  saveArtPreset(name: string) {
    const preset = {
      id: `u-${Date.now().toString(36)}`,
      name: name.trim().slice(0, 40) || "Untitled",
      config: { ...this.art },
    };
    this.artPresets = [...this.artPresets, preset];
    store("qmx.art.presets", this.artPresets);
    return preset;
  }

  /** Surface style, custom theme and art rotation (per machine). */
  surface = $state<Surface>(parseSurface(storedJson("qmx.surface")));
  custom = $state<CustomTheme>(parseCustom(storedJson("qmx.customTheme")));
  artRotate = $state<Rotation>(parseRotation(storedJson("qmx.art.rotate")));

  /** Base text size in pixels; everything scales with it (operator, 2026-10-04: "bigger fonts"). */
  textSize = $state<number>(
    [15, 17, 19].includes(Number(storedJson("qmx.textSize")))
      ? Number(storedJson("qmx.textSize"))
      : 17,
  );

  setTextSize(px: number) {
    this.textSize = px;
    store("qmx.textSize", px);
  }

  setSurface(s: Surface) {
    this.surface = s;
    store("qmx.surface", s);
  }

  setCustom(c: CustomTheme) {
    this.custom = parseCustom(c);
    store("qmx.customTheme", this.custom);
  }

  setArtRotate(r: Rotation) {
    this.artRotate = r;
    store("qmx.art.rotate", r);
  }

  deleteArtPreset(id: string) {
    this.artPresets = this.artPresets.filter((p) => p.id !== id);
    store("qmx.art.presets", this.artPresets);
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

  addRef(label: string, quiet = false) {
    if (!this.copilotRefs.includes(label))
      this.copilotRefs = [...this.copilotRefs, label];
    if (!quiet)
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
