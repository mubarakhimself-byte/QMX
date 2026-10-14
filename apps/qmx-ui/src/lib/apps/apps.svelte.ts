/**
 * Mini apps (pass 1, 2026-10-04). An app is judged the way a pod is: by
 * what it can touch and how far it has got on its road to live (Build,
 * Tests, Sandbox, Shadow run, Live), not by how it was made. Each runs in
 * its own box with a budget, a network allow-list and a circuit breaker.
 * DEMO data; the real list, stages, evidence and logs come from the
 * backend (handoff/MINI-APPS-AND-COPILOT-CONTRACT.md sections 4-6).
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

export type MiniApp = {
  id: string;
  name: string;
  summary: string;
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
    id: "watcher",
    name: "Weekend watcher",
    summary:
      "Watches the paper pods while you're away and messages you if one drifts.",
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
    name: "Broker and exchange status",
    summary:
      "Checks IC Markets' cTrader servers and each exchange's status page.",
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

export const TEMPLATES: { name: string; note: string; risk: Risk }[] = [
  {
    name: "News digest",
    note: "Sources you pick, scored and summed up",
    risk: "show",
  },
  {
    name: "Price alerts",
    note: "Message me when a market crosses a line",
    risk: "work",
  },
  {
    name: "Funding watcher",
    note: "Funding rates and open interest",
    risk: "show",
  },
  {
    name: "Spread alerts",
    note: "Warn me when a broker's spreads widen",
    risk: "work",
  },
  {
    name: "On-chain flows",
    note: "Big moves to and from exchanges",
    risk: "work",
  },
  {
    name: "Weekly report",
    note: "A PDF of every pod, every Monday",
    risk: "work",
  },
  {
    name: "Economic calendar",
    note: "Pause pods around high-impact news",
    risk: "work",
  },
  {
    name: "DCA proposer",
    note: "Proposes buys; you sign each one",
    risk: "money",
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

class Apps {
  mine = $state<MiniApp[]>([]);
  safe = $state(false);
  selected = $state<string | null>("news");

  constructor() {
    try {
      const raw = localStorage.getItem(KEY);
      this.mine = raw ? (JSON.parse(raw) as MiniApp[]) : [];
    } catch {
      this.mine = [];
    }
  }

  get all(): MiniApp[] {
    return [...this.mine, ...DEMO];
  }

  byId(id: string | null) {
    return this.all.find((a) => a.id === id);
  }

  private persist() {
    try {
      localStorage.setItem(KEY, JSON.stringify(this.mine));
    } catch {
      /* storage unavailable: the draft lasts for this window */
    }
  }

  /** A new app made from widgets you picked; it starts at Build. */
  fromWidgets(name: string, panels: string[]): string {
    const id = `my-${Date.now().toString(36)}`;
    this.mine = [
      {
        id,
        name,
        summary: `Made from ${panels.length} widget${panels.length === 1 ? "" : "s"} you picked.`,
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
    this.selected = id;
    this.persist();
    return id;
  }

  remove(id: string) {
    this.mine = this.mine.filter((a) => a.id !== id);
    if (this.selected === id) this.selected = null;
    this.persist();
  }

  toggle(id: string, on: boolean) {
    const mine = this.mine.find((a) => a.id === id);
    if (mine) {
      mine.on = on;
      this.persist();
    } else {
      const d = DEMO.find((a) => a.id === id);
      if (d) d.on = on;
    }
  }
}

export const apps = new Apps();
