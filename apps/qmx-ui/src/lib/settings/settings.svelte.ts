/**
 * Settings state kept on this machine (localStorage) until the daemon owns
 * it. One relation decides what a copilot may use: `CopilotConfig.uses`
 * holds provider and MCP server ids. Models and tools edits it from the
 * tool's side, Copilots from the copilot's side.
 */
import { REACH } from "$lib/copilot/aim.svelte";
import { apps, type MiniApp } from "$lib/apps/apps.svelte";

export type ReachId = (typeof REACH)[number]["id"];

function load<T extends object>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    const v: unknown = JSON.parse(raw);
    if (Array.isArray(fallback)) return (Array.isArray(v) ? v : fallback) as T;
    return v && typeof v === "object" && !Array.isArray(v)
      ? { ...fallback, ...v }
      : fallback;
  } catch {
    return fallback;
  }
}

function save(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: lasts for this window only */
  }
}

/* ---------- General ---------- */

export const ALERTS = [
  { id: "fills", label: "Orders filled or refused" },
  { id: "risk", label: "Kill switch or risk stop" },
  { id: "errand", label: "A copilot needs you" },
  { id: "appStopped", label: "A mini app stopped itself" },
  { id: "serverDown", label: "A server goes down" },
  { id: "testDone", label: "A test or sweep finished" },
] as const;
export type AlertId = (typeof ALERTS)[number]["id"];

function browserZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export type General = {
  name: string;
  timeZone: string;
  currency: string;
  start: string;
  weekStart: string;
  numbers: string;
  alerts: Record<AlertId, boolean>;
  quietOn: boolean;
  quietFrom: string;
  quietTo: string;
  updates: string;
  channel: string;
};

const GENERAL: General = {
  name: "",
  timeZone: browserZone(),
  currency: "USD",
  start: "home",
  weekStart: "mon",
  numbers: "1,234.56",
  alerts: {
    fills: true,
    risk: true,
    errand: true,
    appStopped: true,
    serverDown: true,
    testDone: false,
  },
  quietOn: false,
  quietFrom: "23:00",
  quietTo: "07:00",
  updates: "ask",
  channel: "stable",
};

/* ---------- Models and tools ---------- */

export type Provider = {
  id: string;
  name: string;
  how: string;
  models: string[];
  paid: boolean;
  on: boolean;
};

export type McpServer = {
  id: string;
  name: string;
  note: string;
  paid: boolean;
  on: boolean;
};

const PROVIDERS: Provider[] = [
  {
    id: "claude-plan",
    name: "Claude through your plan",
    how: "Claude Code on this laptop. No key; uses your Claude plan.",
    models: ["Opus 5.5", "Sonnet 5.5", "Haiku 4.5"],
    paid: false,
    on: true,
  },
  {
    id: "anthropic-api",
    name: "Anthropic API",
    how: "API key in the credential store. Billed per use.",
    models: ["Opus 5.5", "Sonnet 5.5", "Haiku 4.5"],
    paid: true,
    on: false,
  },
  {
    id: "openai",
    name: "OpenAI",
    how: "API key in the credential store.",
    models: ["GPT models"],
    paid: true,
    on: false,
  },
  {
    id: "gemini",
    name: "Google Gemini",
    how: "API key in the credential store.",
    models: ["Gemini models"],
    paid: true,
    on: false,
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    how: "One key for many models.",
    models: ["DeepSeek", "Qwen", "Grok"],
    paid: true,
    on: false,
  },
  {
    id: "ollama",
    name: "Local models",
    how: "Ollama on this laptop. Free, private, slower.",
    models: ["qwen", "llama"],
    paid: false,
    on: true,
  },
];

const MCP: McpServer[] = [
  {
    id: "ctrader",
    name: "cTrader",
    note: "Prices, positions and history from your IC Markets accounts. Orders only through your pods.",
    paid: false,
    on: true,
  },
  {
    id: "ccxt",
    name: "Exchange data",
    note: "Prices, order books and funding from your crypto exchanges (CCXT).",
    paid: false,
    on: true,
  },
  {
    id: "files",
    name: "Files",
    note: "Read and write inside the QMX data folder only.",
    paid: false,
    on: true,
  },
  {
    id: "firecrawl",
    name: "Firecrawl",
    note: "Web search, scraping and Alexandria data. Asks you before every call.",
    paid: true,
    on: false,
  },
  {
    id: "github",
    name: "GitHub",
    note: "Read strategy repositories.",
    paid: false,
    on: false,
  },
];

/* ---------- Data sources ---------- */

export const SCHEDULES = [
  "On request",
  "Every 5 min",
  "Every 15 min",
  "Hourly",
  "Daily",
  "Weekly",
] as const;

export const SOURCE_KINDS = {
  feed: "Feed",
  upload: "File",
  api: "API",
  scrape: "Scrape",
} as const;
export type SourceKind = keyof typeof SOURCE_KINDS;

export type Source = {
  id: string;
  name: string;
  kind: SourceKind;
  detail: string;
  schedule: string;
  on: boolean;
  paid: boolean;
  /** Paid sources stay off until you approve them. */
  approved: boolean;
};

const SOURCES: Source[] = [
  {
    id: "arxiv",
    name: "arXiv q-fin",
    kind: "feed",
    detail: "New quant finance papers",
    schedule: "Daily",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "alphaxiv",
    name: "alphaXiv",
    kind: "feed",
    detail: "Discussion of arXiv papers",
    schedule: "Daily",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "ssrn",
    name: "SSRN financial economics",
    kind: "feed",
    detail: "Working papers",
    schedule: "Weekly",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "mql5",
    name: "MQL5 articles",
    kind: "scrape",
    detail: "3,057 articles",
    schedule: "Daily",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "calendar",
    name: "Economic calendar",
    kind: "feed",
    detail: "Forex Factory",
    schedule: "Every 15 min",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "news",
    name: "Market news",
    kind: "feed",
    detail: "Headline feeds",
    schedule: "Every 5 min",
    on: true,
    paid: false,
    approved: true,
  },
  {
    id: "firecrawl",
    name: "Firecrawl",
    kind: "api",
    detail: "Search, scraping, Alexandria",
    schedule: "On request",
    on: false,
    paid: true,
    approved: false,
  },
];

/* ---------- Copilots ---------- */

export type CopilotConfig = {
  model: string;
  instructions: string;
  /** Provider and MCP server ids this copilot may use. */
  uses: string[];
  reach: ReachId[];
  /** Areas where it must ask before acting. */
  approve: ReachId[];
};

export type CopilotEntry = { id: string; name: string };

const BASE_COPILOTS: CopilotEntry[] = [
  { id: "main", name: "Main" },
  { id: "lab", name: "Lab" },
  { id: "portfolio", name: "Portfolio" },
  { id: "library", name: "Library" },
];

const COPILOT_DEFAULTS: Record<string, CopilotConfig> = {
  main: {
    model: "claude-plan/Opus 5.5",
    instructions:
      "Answer in plain words. Ask before anything that costs money or can't be undone.",
    uses: ["claude-plan", "ollama", "ctrader", "ccxt", "files", "firecrawl"],
    reach: ["lab", "portfolio", "library", "apps", "servers"],
    approve: ["portfolio", "servers"],
  },
  lab: {
    model: "claude-plan/Opus 5.5",
    instructions: "Test on CFDs and crypto. Never run on the trading servers.",
    uses: ["claude-plan", "ollama", "ctrader", "ccxt", "files", "github"],
    reach: ["lab", "library", "servers"],
    approve: ["servers"],
  },
  portfolio: {
    model: "claude-plan/Sonnet 5.5",
    instructions: "Live changes are always proposals for my signature.",
    uses: ["claude-plan", "ctrader", "ccxt"],
    reach: ["portfolio", "library"],
    approve: ["portfolio"],
  },
  library: {
    model: "claude-plan/Sonnet 5.5",
    instructions: "",
    uses: ["claude-plan", "files", "firecrawl"],
    reach: ["library"],
    approve: [],
  },
};

const APP_COPILOT: CopilotConfig = {
  model: "claude-plan/Haiku 4.5",
  instructions: "",
  uses: ["claude-plan"],
  reach: ["apps"],
  approve: [],
};

/* ---------- Mini apps ---------- */

export const APP_SCHEDULES = ["When open", ...SCHEDULES.slice(1)] as const;
export const APPROVAL = {
  auto: "Goes ahead",
  ask: "Asks first",
  sign: "You sign",
} as const;
export type Approval = keyof typeof APPROVAL;

export type AppControls = {
  budgetMin: number;
  schedule: string;
  network: string[];
  approval: Approval;
};

function appDefaults(a: MiniApp): AppControls {
  const m = /(\d+)\s*CPU (hour|minute)/.exec(a.budget);
  const sched = a.schedule ?? "When open";
  return {
    budgetMin: m ? Number(m[1]) * (m[2] === "hour" ? 60 : 1) : 10,
    schedule: (APP_SCHEDULES as readonly string[]).includes(sched)
      ? sched
      : /minute/.test(sched)
        ? "Every 15 min"
        : "When open",
    network: a.network
      .replace(/ only$/, "")
      .split(/;|,| and /)
      .map((s) => s.trim())
      .filter(Boolean),
    approval: a.risk === "money" ? "sign" : a.risk === "work" ? "ask" : "auto",
  };
}

/* ---------- Safety ---------- */

export const GO_LIVE = {
  auto: "By itself after checks",
  ask: "Ask me first",
} as const;
export type GoLive = keyof typeof GO_LIVE;

export type Sticky = { id: string; who: string; what: string };

export type Safety = {
  goLive: { show: GoLive; work: GoLive };
  agentsUsd: number;
  appsUsd: number;
  /** Share of the Claude plan's 5-hour usage background agents may use. */
  planShare: number;
  sticky: Sticky[];
};

const SAFETY: Safety = {
  goLive: { show: "auto", work: "auto" },
  agentsUsd: 20,
  appsUsd: 10,
  planShare: 50,
  sticky: [
    {
      id: "s1",
      who: "Main copilot",
      what: "Restart a mini app that stopped itself",
    },
    { id: "s2", who: "Lab copilot", what: "Start sweeps on Home PC" },
    { id: "s3", who: "Portfolio copilot", what: "Change paper-side layouts" },
  ],
};

/* ---------- Store ---------- */

class SettingsStore {
  general = $state(load("qmx.settings.general", GENERAL));
  providers = $state(load("qmx.settings.providers", PROVIDERS));
  mcp = $state(load("qmx.settings.mcp", MCP));
  sources = $state(load("qmx.settings.sources", SOURCES));
  copilotOverrides = $state(
    load<Record<string, CopilotConfig>>("qmx.settings.copilots", {}),
  );
  appOverrides = $state(
    load<Record<string, AppControls>>("qmx.settings.apps", {}),
  );
  safety = $state(load("qmx.settings.safety", SAFETY));

  get copilots(): CopilotEntry[] {
    return [
      ...BASE_COPILOTS,
      ...apps.all.map((a) => ({ id: `app:${a.id}`, name: a.name })),
    ];
  }

  copilot(id: string): CopilotConfig {
    return (
      this.copilotOverrides[id] ??
      COPILOT_DEFAULTS[id] ?? { ...APP_COPILOT, uses: [...APP_COPILOT.uses] }
    );
  }

  editCopilot(id: string, patch: Partial<CopilotConfig>) {
    this.copilotOverrides[id] = { ...this.copilot(id), ...patch };
  }

  /** Copilots allowed to use a provider or MCP server. */
  usersOf(toolId: string): CopilotEntry[] {
    return this.copilots.filter((c) =>
      this.copilot(c.id).uses.includes(toolId),
    );
  }

  setUse(copilotId: string, toolId: string, on: boolean) {
    const uses = this.copilot(copilotId).uses.filter((u) => u !== toolId);
    this.editCopilot(copilotId, { uses: on ? [...uses, toolId] : uses });
  }

  /** Models a copilot can pick: from providers that are on and allowed. */
  modelsFor(copilotId: string) {
    const uses = this.copilot(copilotId).uses;
    return this.providers
      .filter((p) => p.on && uses.includes(p.id))
      .flatMap((p) =>
        p.models.map((m) => ({
          value: `${p.id}/${m}`,
          label: `${m} · ${p.name}`,
        })),
      );
  }

  appControls(a: MiniApp): AppControls {
    return this.appOverrides[a.id] ?? appDefaults(a);
  }

  editApp(a: MiniApp, patch: Partial<AppControls>) {
    this.appOverrides[a.id] = { ...this.appControls(a), ...patch };
  }
}

export const settings = new SettingsStore();

$effect.root(() => {
  $effect(() =>
    save("qmx.settings.general", $state.snapshot(settings.general)),
  );
  $effect(() =>
    save("qmx.settings.providers", $state.snapshot(settings.providers)),
  );
  $effect(() => save("qmx.settings.mcp", $state.snapshot(settings.mcp)));
  $effect(() =>
    save("qmx.settings.sources", $state.snapshot(settings.sources)),
  );
  $effect(() =>
    save("qmx.settings.copilots", $state.snapshot(settings.copilotOverrides)),
  );
  $effect(() =>
    save("qmx.settings.apps", $state.snapshot(settings.appOverrides)),
  );
  $effect(() => save("qmx.settings.safety", $state.snapshot(settings.safety)));
});
