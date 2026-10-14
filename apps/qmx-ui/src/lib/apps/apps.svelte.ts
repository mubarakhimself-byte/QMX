/**
 * Mini apps (pass 2, 2026-10-14). An app is something you open and use, so
 * each one carries a preview of its own output and a group saying what it is
 * for. Its road to live (Build, Tests, Sandbox, Shadow run, Live), its box
 * and its log sit one level down, in About. DEMO data; the real list, stages,
 * evidence and logs come from the backend
 * (handoff/MINI-APPS-AND-COPILOT-CONTRACT.md sections 4-6).
 */
import type { Component } from "svelte";
import { HOME_PANELS } from "$lib/home/catalog";
import { PORTFOLIO_PANELS } from "$lib/portfolio/catalog";
import {
  pane,
  split,
  type TileLayout,
  type TileNode,
} from "$lib/workbench/tiles/tiles";

export const STEPS = [
  "Build",
  "Tests",
  "Sandbox",
  "Shadow run",
  "Live",
] as const;

/** What an app can touch decides how it goes live. */
export const RISK = {
  show: {
    label: "Shows things",
    rule: "Goes live by itself once its tests and shadow run pass.",
  },
  work: {
    label: "Runs work",
    rule: "Goes live by itself, inside a budget it can't exceed.",
  },
  money: {
    label: "Touches money",
    rule: "Only proposes. Every order needs your signature in Portfolio.",
  },
} as const;
export type Risk = keyof typeof RISK;

export const KIND = {
  screens: "Has screens",
  headless: "Runs in the background",
  both: "Screens and background work",
} as const;
export type Kind = keyof typeof KIND;

export type Health = "ok" | "warn" | "tripped" | "idle";

/** What an app is for. Apps are grouped by this, never by stage. */
export const GROUPS = {
  markets: "Markets",
  watching: "Watching",
  research: "Research",
  helpers: "Trading helpers",
} as const;
export type Group = keyof typeof GROUPS;

/** Icon names, resolved to components in icons.ts (drafts are saved as JSON). */
export type IconName =
  | "newspaper"
  | "scan-search"
  | "binoculars"
  | "server-cog"
  | "gauge"
  | "calendar-clock"
  | "activity"
  | "piggy-bank"
  | "network"
  | "percent"
  | "telescope"
  | "calculator"
  | "layout-grid"
  | "trending-up"
  | "coins"
  | "file-text";

type Tone = "up" | "down";
/** A glimpse of what the app gives you, drawn on its tile. */
export type Preview =
  | { kind: "figure"; value: string; label: string; spark?: number[] }
  | { kind: "headline"; text: string; meta: string }
  | { kind: "rows"; rows: { label: string; value: string; tone?: Tone }[] }
  | { kind: "alert"; text: string; when: string };

/** Where an app stands, in the order a tile shows it. */
export const STATUS = {
  live: { label: "Live", dot: "bg-success" },
  attention: { label: "Needs a look", dot: "bg-warning" },
  stopped: { label: "Stopped", dot: "bg-destructive" },
  off: { label: "Off", dot: "bg-muted-foreground" },
  proving: { label: "Proving", dot: "bg-info" },
  building: { label: "Being built", dot: "bg-muted-foreground" },
} as const;
export type Status = keyof typeof STATUS;

export function statusOf(a: MiniApp, safe: boolean): Status {
  if (!a.on || safe) return "off";
  if (a.health === "tripped") return "stopped";
  if (a.health === "warn") return "attention";
  if (a.stage === 0) return "building";
  return a.stage < 4 ? "proving" : "live";
}

export type MiniApp = {
  id: string;
  name: string;
  summary: string;
  icon: IconName;
  group: Group;
  preview?: Preview;
  /** Headless apps: when it runs next. */
  next?: string;
  kind: Kind;
  risk: Risk;
  /** Index into STEPS. */
  stage: number;
  /** What is happening at this stage, in one line. */
  stageNote: string;
  /** What each finished step left behind (evidence, not logs). */
  evidence: string[];
  health: Health;
  builtBy: string;
  runsOn: string;
  budget: string;
  budgetUsed: number;
  network: string;
  breaker: string;
  /** Where its output shows up in QMX. */
  provides: string[];
  ops: string[];
  feeds?: string[];
  schedule?: string;
  log: string[];
  /** Widget ids its screen is made of (screens kind). */
  panels?: string[];
  /** Why it stopped itself, when its circuit breaker tripped. */
  stopped?: string;
  /** The copilot errand building or watching it. */
  errand?: string;
  on: boolean;
};

const DEMO: MiniApp[] = $state([
  {
    id: "news",
    name: "News & sentiment",
    summary:
      "Reads market, crypto and macro news, scores the mood of each story.",
    icon: "newspaper",
    group: "research",
    preview: {
      kind: "headline",
      text: "Spot BTC ETFs took in $412M yesterday",
      meta: "Mood +0.7 · 12 stories this hour",
    },
    kind: "both",
    risk: "show",
    stage: 4,
    stageNote: "Live for 21 days",
    evidence: [
      "Built from the news workflow template",
      "38 of 38 tests passed",
      "3 days on recorded news, no crashes",
      "7 days shadow run; scores matched a hand check 84% of the time",
    ],
    health: "ok",
    builtBy: "the copilot, from a template",
    runsOn: "Its own box on Frankfurt",
    budget: "2 CPU hours a day",
    budgetUsed: 0.41,
    network: "News sites and CryptoPanic only",
    breaker: "Stops itself after 5 failed fetches in 10 minutes",
    provides: [
      "News panel on Home",
      "News guard for every pod",
      "Mood scores for Market mood",
    ],
    ops: ["news.refresh", "news.windows", "news.score"],
    feeds: ["mood"],
    schedule: "Every 5 minutes",
    log: [
      "14:05 fetched 12 stories, scored 12",
      "14:00 fetched 9 stories, scored 9",
      "13:55 CryptoPanic slow (2.1 s), retried once",
    ],
    panels: ["events", "calendar"],
    on: true,
  },
  {
    id: "screener",
    name: "Coin screener",
    summary: "Ranks the top coins by trend, volume and funding.",
    icon: "scan-search",
    group: "markets",
    preview: {
      kind: "rows",
      rows: [
        { label: "SOL", value: "+6.2%", tone: "up" },
        { label: "ETH", value: "+3.1%", tone: "up" },
        { label: "BTC", value: "−0.4%", tone: "down" },
      ],
    },
    kind: "screens",
    risk: "show",
    stage: 4,
    stageNote: "Live for 9 days",
    evidence: [
      "Built by the copilot from your description",
      "12 of 12 tests passed",
      "2 days on recorded prices",
      "5 days shadow run, no errors",
    ],
    health: "ok",
    builtBy: "the copilot",
    runsOn: "This laptop",
    budget: "Light; runs when open",
    budgetUsed: 0.08,
    network: "Your exchanges only",
    breaker: "Stops itself if prices are older than 2 minutes",
    provides: ["Screener panel on Home → Markets"],
    ops: ["crypto.quote", "crypto.rank"],
    log: ["14:06 ranked 40 coins", "14:01 ranked 40 coins"],
    panels: ["screener", "markets"],
    on: true,
  },
  {
    id: "funding",
    name: "Funding rates",
    summary: "Perpetual funding and open interest for the coins you trade.",
    icon: "percent",
    group: "markets",
    preview: {
      kind: "figure",
      value: "+0.012%",
      label: "BTC funding, next 8h",
      spark: [8, 9, 11, 10, 12, 13, 12],
    },
    kind: "screens",
    risk: "show",
    stage: 4,
    stageNote: "Live for 15 days",
    evidence: [
      "Built from the Funding watcher template",
      "10 of 10 tests passed",
      "2 days on recorded funding",
      "5 days shadow run, no errors",
    ],
    health: "ok",
    builtBy: "you, from a template",
    runsOn: "This laptop",
    budget: "Light; runs when open",
    budgetUsed: 0.04,
    network: "Your exchanges only",
    breaker: "Stops itself if rates are older than 10 minutes",
    provides: ["Funding panel on Home → Markets"],
    ops: ["crypto.funding", "crypto.open_interest"],
    log: [
      "14:00 funding BTC +0.012%, ETH +0.009%",
      "06:00 funding BTC +0.010%",
    ],
    panels: ["markets", "screener"],
    on: true,
  },
  {
    id: "brief",
    name: "Morning brief",
    summary: "One page at 07:00: overnight moves, today's news, your pods.",
    icon: "file-text",
    group: "research",
    preview: {
      kind: "headline",
      text: "Gold held 2,640; dollar firmer into CPI",
      meta: "Today 07:00 · 3 min read",
    },
    next: "Next brief tomorrow 07:00",
    kind: "both",
    risk: "show",
    stage: 4,
    stageNote: "Live for 30 days",
    evidence: [
      "Built by the copilot from your description",
      "8 of 8 tests passed",
      "5 recorded mornings",
      "7 days shadow run; you kept 6 of 7 briefs",
    ],
    health: "ok",
    builtBy: "the copilot",
    runsOn: "Its own box on Frankfurt",
    budget: "20 CPU minutes a day",
    budgetUsed: 0.5,
    network: "News sites and your brokers",
    breaker: "Stops itself if the brief is not ready by 07:30",
    provides: ["A brief in Library each morning", "Recent items on Home"],
    ops: ["news.windows", "pods.read", "library.save"],
    schedule: "Every day at 07:00",
    log: ["07:00 brief written, 640 words", "07:00 yesterday: brief written"],
    panels: ["recent", "events"],
    on: true,
  },
  {
    id: "sizer",
    name: "Position sizer",
    summary: "Lot size from your risk, stop and account, for any market.",
    icon: "calculator",
    group: "helpers",
    preview: {
      kind: "rows",
      rows: [
        { label: "XAUUSD · 0.5% risk", value: "0.42 lots" },
        { label: "EURUSD · 0.5% risk", value: "1.10 lots" },
      ],
    },
    kind: "screens",
    risk: "show",
    stage: 4,
    stageNote: "Live for 12 days",
    evidence: [
      "Made by you from widgets",
      "6 of 6 tests passed",
      "1 day on recorded prices",
      "3 days shadow run",
    ],
    health: "ok",
    builtBy: "you, from widgets",
    runsOn: "This laptop",
    budget: "Light; runs when open",
    budgetUsed: 0.01,
    network: "Your brokers only",
    breaker: "Stops itself if prices are older than 1 minute",
    provides: ["Its own screen"],
    ops: ["accounts.read", "cfd.quote"],
    log: ["13:58 sized XAUUSD 0.42 lots at 0.5% risk"],
    panels: ["accounts", "positions"],
    on: true,
  },
  {
    id: "watcher",
    name: "Weekend watcher",
    summary:
      "Watches the paper pods while you're away and messages you if one drifts.",
    icon: "binoculars",
    group: "watching",
    preview: {
      kind: "alert",
      text: "4 pods inside their lines",
      when: "3 min ago",
    },
    next: "Next check 14:18",
    kind: "headless",
    risk: "work",
    stage: 4,
    stageNote: "Live for 4 days · last ran 3 minutes ago",
    evidence: [
      "Set up by the copilot from an errand",
      "9 of 9 tests passed",
      "1 day on a recorded weekend",
      "3 days shadow run; it would have messaged you once, correctly",
    ],
    health: "ok",
    builtBy: "the copilot, from an errand",
    runsOn: "Its own box on Tokyo",
    budget: "30 CPU minutes a day",
    budgetUsed: 0.22,
    network: "QMX only; messages through your Telegram bot",
    breaker: "Stops itself after 3 failed checks in a row",
    provides: ["Messages to you", "Entries in Needs you on Home"],
    ops: ["pods.read", "notify.send"],
    schedule: "Every 15 minutes, Friday 20:00 to Monday 02:00",
    log: [
      "14:03 4 pods checked, all inside their lines",
      "13:48 4 pods checked, all inside their lines",
    ],
    errand: "weekend",
    on: true,
  },
  {
    id: "exchange-status",
    name: "Broker status",
    summary:
      "Checks IC Markets' cTrader servers and each exchange's status page.",
    icon: "server-cog",
    group: "watching",
    preview: {
      kind: "alert",
      text: "Kraken status page down",
      when: "40 min ago",
    },
    next: "Every minute, once restarted",
    kind: "headless",
    risk: "work",
    stage: 4,
    stageNote: "Stopped itself 40 minutes ago",
    evidence: [
      "Built from a template",
      "6 of 6 tests passed",
      "1 day on recorded status pages",
      "3 days shadow run",
    ],
    health: "tripped",
    stopped:
      "Kraken's status page kept failing, so after 5 failed calls in a minute it switched itself off.",
    builtBy: "you, from a template",
    runsOn: "Its own box on Frankfurt",
    budget: "10 CPU minutes a day",
    budgetUsed: 0.6,
    network: "Broker and exchange status pages only",
    breaker: "Stops itself after 5 failed calls in a minute",
    provides: ["Exchange dots in the bottom bar"],
    ops: ["status.check"],
    schedule: "Every minute",
    log: [
      "13:26 circuit breaker: 5 failed calls in 60 s, stopped",
      "13:26 kraken status page returned 503",
      "13:25 kraken status page returned 503",
    ],
    on: true,
  },
  {
    id: "mood",
    name: "Market mood",
    summary: "One crowd-mood number per market, from news and social posts.",
    icon: "gauge",
    group: "markets",
    preview: {
      kind: "figure",
      value: "62",
      label: "BTC crowd mood",
      spark: [54, 57, 55, 58, 60, 59, 62],
    },
    kind: "screens",
    risk: "show",
    stage: 3,
    stageNote: "Shadow run, day 3 of 7. Nothing uses its output yet.",
    evidence: [
      "Built by the copilot overnight",
      "21 of 21 tests passed",
      "3 days on recorded news; one slow day, no crashes",
    ],
    health: "ok",
    builtBy: "the copilot, overnight",
    runsOn: "Its own box on this laptop",
    budget: "1 CPU hour a day",
    budgetUsed: 0.3,
    network: "News sites and X search only",
    breaker: "Stops itself after 5 failed fetches in 10 minutes",
    provides: ["Mood panel (after it goes live)"],
    ops: ["mood.index"],
    log: [
      "14:00 mood: gold 55, BTC 62, ETH 58",
      "13:00 mood: gold 57, BTC 60, ETH 57",
    ],
    panels: ["markets", "events"],
    on: true,
  },
  {
    id: "econ-calendar",
    name: "Economic calendar watcher",
    summary:
      "Pauses new CFD trades 15 minutes either side of high-impact news.",
    icon: "calendar-clock",
    group: "helpers",
    preview: {
      kind: "headline",
      text: "US CPI at 14:30",
      meta: "Would pause Gold & indices 14:15 to 14:45",
    },
    kind: "both",
    risk: "work",
    stage: 3,
    stageNote:
      "Shadow run, day 5 of 7. It suggests pauses; nothing is paused yet.",
    evidence: [
      "Built from the news workflow template",
      "14 of 14 tests passed",
      "2 days on last month's calendar; every pause matched a hand check",
    ],
    health: "ok",
    builtBy: "the copilot, from a template",
    runsOn: "Its own box on London",
    budget: "10 CPU minutes a day",
    budgetUsed: 0.05,
    network: "Forex Factory calendar only",
    breaker: "Stops itself if the calendar is older than 1 hour",
    provides: [
      "Pause windows for Gold & indices and FX majors (after it goes live)",
      "Calendar panel on Home",
    ],
    ops: ["calendar.events", "pods.pause_window"],
    schedule: "Every 10 minutes",
    log: [
      "14:00 next: US CPI at 14:30, would pause Gold & indices 14:15 to 14:45",
      "13:50 calendar refreshed: 6 high-impact events this week",
    ],
    panels: ["calendar", "events"],
    on: true,
  },
  {
    id: "spreads",
    name: "Spread watcher",
    summary:
      "Watches IC Markets spreads on gold, indices and FX, and warns when they widen.",
    icon: "activity",
    group: "watching",
    preview: {
      kind: "alert",
      text: "Gold spread over 40¢ twice",
      when: "replay of Sep 12",
    },
    kind: "headless",
    risk: "work",
    stage: 2,
    stageNote: "Sandbox: replaying last month's cTrader ticks",
    evidence: [
      "Built by the copilot from your description",
      "17 of 17 tests passed",
    ],
    health: "ok",
    builtBy: "the copilot",
    runsOn: "Its own box on Research VPS",
    budget: "1 CPU hour a day",
    budgetUsed: 0.12,
    network: "Recorded data only (sandbox)",
    breaker: "Stops itself if a replay day takes over 10 minutes",
    provides: ["Alerts in Needs you (after it goes live)"],
    ops: ["cfd.spreads"],
    log: [
      "13:50 replayed Sep 12: gold spread over 40 cents twice",
      "13:41 replayed Sep 11: no wide spreads",
    ],
    on: true,
  },
  {
    id: "dca",
    name: "Weekly DCA proposer",
    summary: "Proposes a weekly buy of BTC and ETH when they dip.",
    icon: "piggy-bank",
    group: "helpers",
    kind: "headless",
    risk: "money",
    stage: 1,
    stageNote: "Tests: 11 of 14 passed; the copilot is fixing 3",
    evidence: ["Built by the copilot from your description"],
    health: "warn",
    builtBy: "the copilot",
    runsOn: "Its own box on this laptop",
    budget: "5 CPU minutes a day",
    budgetUsed: 0.02,
    network: "None until it goes live",
    breaker: "Stops itself if a proposal is over $500",
    provides: ["Proposals in Portfolio for your signature"],
    ops: ["proposal.create"],
    log: [
      "13:12 test 'skips when no dip' failed",
      "13:12 test 'caps at budget' failed",
    ],
    errand: "weekend",
    on: true,
  },
  {
    id: "correlation",
    name: "Correlation map",
    summary: "How the markets in your pods move together, week by week.",
    icon: "network",
    group: "research",
    kind: "screens",
    risk: "show",
    stage: 0,
    stageNote: "The copilot is building it tonight; first draft by 07:00",
    evidence: [],
    health: "idle",
    builtBy: "the copilot, overnight",
    runsOn: "Its own box on Research VPS",
    budget: "2 CPU hours tonight",
    budgetUsed: 0.35,
    network: "Your brokers and exchanges only",
    breaker: "Stops the build if it runs past 07:00",
    provides: ["Correlation panel for Home and Portfolio"],
    ops: [],
    log: ["13:40 wrote the data loader", "13:20 planned three panels"],
    errand: "weekend",
    on: true,
  },
]);

export type Template = {
  id: string;
  name: string;
  note: string;
  risk: Risk;
  icon: IconName;
  group: Group;
  /** A sample of what it will show once it runs. */
  preview: Preview;
};

export const TEMPLATES: Template[] = [
  {
    id: "news-digest",
    name: "News digest",
    note: "Sources you pick, scored and summed up",
    risk: "show",
    icon: "newspaper",
    group: "research",
    preview: {
      kind: "headline",
      text: "Oil slips as stocks build",
      meta: "Mood −0.3 · 8 stories",
    },
  },
  {
    id: "price-alerts",
    name: "Price alerts",
    note: "Message me when a market crosses a line",
    risk: "work",
    icon: "trending-up",
    group: "watching",
    preview: { kind: "alert", text: "XAUUSD crossed 2,650", when: "just now" },
  },
  {
    id: "funding-watcher",
    name: "Funding watcher",
    note: "Funding rates and open interest",
    risk: "show",
    icon: "percent",
    group: "markets",
    preview: {
      kind: "figure",
      value: "+0.010%",
      label: "ETH funding",
      spark: [5, 6, 8, 7, 9, 10],
    },
  },
  {
    id: "spread-alerts",
    name: "Spread alerts",
    note: "Warn me when a broker's spreads widen",
    risk: "work",
    icon: "activity",
    group: "watching",
    preview: {
      kind: "alert",
      text: "NAS100 spread 3.1 pts",
      when: "at the open",
    },
  },
  {
    id: "on-chain",
    name: "On-chain flows",
    note: "Big moves to and from exchanges",
    risk: "work",
    icon: "coins",
    group: "markets",
    preview: {
      kind: "rows",
      rows: [
        { label: "BTC into exchanges", value: "+2,140", tone: "down" },
        { label: "ETH out of exchanges", value: "−18,300", tone: "up" },
      ],
    },
  },
  {
    id: "weekly-report",
    name: "Weekly report",
    note: "A PDF of every pod, every Monday",
    risk: "work",
    icon: "file-text",
    group: "research",
    preview: {
      kind: "headline",
      text: "Week 41: +1.8%, two pods ahead",
      meta: "Monday 08:00 · PDF",
    },
  },
  {
    id: "econ-calendar",
    name: "Economic calendar",
    note: "Pause pods around high-impact news",
    risk: "work",
    icon: "calendar-clock",
    group: "helpers",
    preview: {
      kind: "headline",
      text: "FOMC minutes at 19:00",
      meta: "Would pause FX majors",
    },
  },
  {
    id: "dca",
    name: "DCA proposer",
    note: "Proposes buys; you sign each one",
    risk: "money",
    icon: "piggy-bank",
    group: "helpers",
    preview: { kind: "figure", value: "$250", label: "Proposed BTC buy" },
  },
];

/** Widgets an app's screen can be made from: everything Home and Portfolio offer. */
type Widget = {
  title: string;
  icon: Component;
  note: string;
  view: Component;
  from: string;
};
export const WIDGETS: Record<string, Widget> = Object.fromEntries([
  ...Object.entries(PORTFOLIO_PANELS).map(([id, p]) => [
    id,
    { ...p, from: "Portfolio" },
  ]),
  ...Object.entries(HOME_PANELS)
    .filter(([id]) => id !== "pinned")
    .map(([id, p]) => [
      id,
      { ...p, from: id === "pods" || id === "events" ? "Portfolio" : "Home" },
    ]),
]);

/** A first layout for an app screen: columns of two widgets each. */
export function layoutFor(app: MiniApp): TileLayout {
  const ids = app.panels ?? [];
  const cols: [TileNode, number][] = [];
  for (let i = 0; i < ids.length; i += 2) {
    const pair = ids
      .slice(i, i + 2)
      .map((w, k) => pane(`${app.id}-${i + k}`, w));
    cols.push([
      pair.length === 1
        ? pair[0]
        : split(
            "col",
            pair.map((p) => [p, 50] as [TileNode, number]),
          ),
      100 / Math.ceil(ids.length / 2),
    ]);
  }
  return {
    id: "main",
    name: app.name,
    root: cols.length === 1 ? cols[0][0] : split("row", cols),
    docked: [],
  };
}

const KEY = "qmx.apps.v1";
const PINS = "qmx.apps.pins.v1";

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}
function save(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: the change lasts for this window */
  }
}

class Apps {
  mine = $state<MiniApp[]>(load(KEY, []));
  pins = $state<string[]>(load(PINS, ["news", "watcher"]));
  safe = $state(false);
  /** The app whose About sheet is open. */
  selected = $state<string | null>(null);

  get all(): MiniApp[] {
    return [...this.mine, ...DEMO];
  }

  byId(id: string | null) {
    return this.all.find((a) => a.id === id);
  }

  status(a: MiniApp): Status {
    return statusOf(a, this.safe);
  }

  pinned(id: string) {
    return this.pins.includes(id);
  }

  pin(id: string, on = !this.pinned(id)) {
    this.pins = on
      ? [...this.pins.filter((p) => p !== id), id]
      : this.pins.filter((p) => p !== id);
    save(PINS, this.pins);
  }

  /** A new app made from widgets you picked; it starts at Build. */
  fromWidgets(name: string, panels: string[]): string {
    const id = `my-${Date.now().toString(36)}`;
    this.mine = [
      {
        id,
        name,
        summary: `Made from ${panels.length} widget${panels.length === 1 ? "" : "s"} you picked.`,
        icon: "layout-grid",
        group: "helpers",
        kind: "screens",
        risk: "show",
        stage: 0,
        stageNote: "Draft ready to open. Say when it's done and its tests run.",
        evidence: [],
        health: "idle",
        builtBy: "you, from widgets",
        runsOn: "This laptop",
        budget: "Light; runs when open",
        budgetUsed: 0,
        network: "Whatever its widgets already use",
        breaker: "Inherits each widget's own limits",
        provides: ["Its own screen, opened from Apps"],
        ops: [],
        log: ["Created from widgets"],
        panels,
        on: true,
      },
      ...this.mine,
    ];
    save(KEY, this.mine);
    return id;
  }

  remove(id: string) {
    this.mine = this.mine.filter((a) => a.id !== id);
    this.pin(id, false);
    if (this.selected === id) this.selected = null;
    save(KEY, this.mine);
  }

  toggle(id: string, on: boolean) {
    const a = this.byId(id);
    if (!a) return;
    a.on = on;
    if (this.mine.includes(a)) save(KEY, this.mine);
  }

  /** Demo restart: clears the trip here; the real one goes through the daemon. */
  restart(id: string) {
    const a = this.byId(id);
    if (!a || a.health !== "tripped") return;
    a.health = "ok";
    a.stopped = undefined;
    a.stageNote = "Live · restarted just now";
    a.log = ["now restarted by you", ...a.log];
    if (a.preview?.kind === "alert")
      a.preview = {
        kind: "alert",
        text: "Restarted, checking again",
        when: "just now",
      };
  }
}

export const apps = new Apps();
