/**
 * The Library as one catalogue: every kind of thing QMX keeps, on shelves,
 * and for each item where it is used across QMX (operator, 2026-10-03: "it
 * needs to be able to connect to all the other parts"). Demo data is drawn
 * from the other screens' samples so the links are real links inside the
 * app; the daemon's Library index replaces all of it.
 */
import type { Component } from "svelte";
import Bot from "@lucide/svelte/icons/bot";
import BrainCircuit from "@lucide/svelte/icons/brain-circuit";
import Workflow from "@lucide/svelte/icons/workflow";
import Layers2 from "@lucide/svelte/icons/layers-2";
import Puzzle from "@lucide/svelte/icons/puzzle";
import AppWindow from "@lucide/svelte/icons/app-window";
import LayoutTemplate from "@lucide/svelte/icons/layout-template";
import FileChartColumn from "@lucide/svelte/icons/file-chart-column";
import Radio from "@lucide/svelte/icons/radio";
import Siren from "@lucide/svelte/icons/siren";
import SlidersHorizontal from "@lucide/svelte/icons/sliders-horizontal";
import Database from "@lucide/svelte/icons/database";
import FileBox from "@lucide/svelte/icons/file-box";
import BookOpen from "@lucide/svelte/icons/book-open";
import Rss from "@lucide/svelte/icons/rss";
import ChartCandlestick from "@lucide/svelte/icons/chart-candlestick";
import Play from "@lucide/svelte/icons/play";
import ShieldCheck from "@lucide/svelte/icons/shield-check";
import Inbox from "@lucide/svelte/icons/inbox";
import GraduationCap from "@lucide/svelte/icons/graduation-cap";
import { DEMO_ARTIFACTS, DEMO_ENTITIES } from "$lib/demo/assets";
import { SOURCES } from "$lib/demo/feeds";
import type { Entity } from "$lib/qmx/entities";
import { ASSETS, RUNS } from "$lib/lab/demo";
import {
  BLOCKS,
  INTERVENTIONS,
  LAB_PODS,
  PAPER_INTERVENTIONS,
  MY_STRESS,
  PAPER_RUNS,
  POD_TEMPLATES,
  SLOTS,
  STAGE_LABEL,
  STRESS,
  TEST_BOTS,
} from "$lib/lab/pods";
import {
  CANDIDATES,
  JOURNAL,
  PODS,
  TEMPLATES as PORTFOLIO_TEMPLATES,
} from "$lib/portfolio/demo";

export type Place = "Lab" | "Portfolio" | "Copilot" | "Home" | "Mini apps";
export const PLACES: Place[] = [
  "Lab",
  "Portfolio",
  "Copilot",
  "Home",
  "Mini apps",
];

/** One place an item is used, and how to get there. */
export type Use = { place: Place; what: string; path: string; query?: string };

export type ShelfId =
  | "bots"
  | "models"
  | "workflows"
  | "pods"
  | "blocks"
  | "apps"
  | "templates"
  | "reports"
  | "paper"
  | "scenarios"
  | "setups"
  | "datasets"
  | "files"
  | "articles"
  | "sources";

export type Shelf = {
  id: ShelfId;
  label: string;
  icon: Component;
  note: string;
};

export const SHELF_GROUPS: {
  label: string;
  icon: Component;
  shelves: Shelf[];
}[] = [
  {
    label: "Things that trade",
    icon: ChartCandlestick,
    shelves: [
      {
        id: "bots",
        label: "Bots",
        icon: Bot,
        note: "Strategies that place trades",
      },
      {
        id: "models",
        label: "Models",
        icon: BrainCircuit,
        note: "Trained and imported models",
      },
      {
        id: "pods",
        label: "Pods",
        icon: Layers2,
        note: "Risk and sizing systems",
      },
      {
        id: "blocks",
        label: "Pod blocks",
        icon: Puzzle,
        note: "Pieces pods are built from",
      },
    ],
  },
  {
    label: "Things that run",
    icon: Play,
    shelves: [
      {
        id: "workflows",
        label: "Workflows",
        icon: Workflow,
        note: "Steps that run on a schedule or on demand",
      },
      {
        id: "apps",
        label: "Mini apps",
        icon: AppWindow,
        note: "Screens and headless apps",
      },
      {
        id: "templates",
        label: "Templates",
        icon: LayoutTemplate,
        note: "Start anything from one",
      },
    ],
  },
  {
    label: "Proof",
    icon: ShieldCheck,
    shelves: [
      {
        id: "reports",
        label: "Test reports",
        icon: FileChartColumn,
        note: "Backtests, sweeps, robustness",
      },
      {
        id: "paper",
        label: "Paper runs",
        icon: Radio,
        note: "Bots and pods on paper money",
      },
      {
        id: "scenarios",
        label: "Stress scenarios",
        icon: Siren,
        note: "Crises to test pods against",
      },
    ],
  },
  {
    label: "Inputs",
    icon: Inbox,
    shelves: [
      {
        id: "setups",
        label: "Saved setups",
        icon: SlidersHorizontal,
        note: "Test settings, presets, features, model settings",
      },
      {
        id: "datasets",
        label: "Data",
        icon: Database,
        note: "Market data and uploads",
      },
      {
        id: "files",
        label: "Files",
        icon: FileBox,
        note: "Everything QMX produced",
      },
    ],
  },
  {
    label: "Knowledge",
    icon: GraduationCap,
    shelves: [
      {
        id: "articles",
        label: "Articles",
        icon: BookOpen,
        note: "Read in QMX",
      },
      {
        id: "sources",
        label: "Sources",
        icon: Rss,
        note: "Papers, news, video",
      },
    ],
  },
];
export const SHELVES = SHELF_GROUPS.flatMap((g) => g.shelves);
export const shelfById = (id: string) => SHELVES.find((s) => s.id === id);

export type LibraryItem = {
  id: string;
  shelf: ShelfId;
  name: string;
  summary: string;
  /** Strategy family or sub-kind; colours the card. */
  family?: string;
  version?: string;
  stage?: string;
  updated: string;
  uses: Use[];
  /** Bots, models, apps and workflows have a full page. */
  entity?: Entity;
  /** Templates: what using it starts. */
  starts?: Use;
  details?: [string, string][];
  /** Journal: what happened and why (trades, interventions, notes). */
  journal?: { time: string; text: string; tone?: "good" | "bad" }[];
  /** Machine logs, newest last. */
  logs?: string[];
  /** The item as code, read-only here; edit it in the Lab. */
  code?: { lang: "python" | "yaml"; text: string };
};

/** Colour by family so a scalper never looks like a trend follower. */
const FAMILY_HUE: [RegExp, string][] = [
  [/trend|momentum|rotation/i, "#2f6bff"],
  [/revers|fade/i, "#8b5cf6"],
  [/breakout|scalp/i, "#d4a017"],
  [/boost|markov|forecast|model/i, "#16a36a"],
  [/news|sentiment/i, "#e0663a"],
];
export function familyColor(item: Pick<LibraryItem, "family" | "shelf">) {
  for (const [re, c] of FAMILY_HUE) if (re.test(item.family ?? "")) return c;
  return (
    (
      {
        pods: "#0ea5a4",
        blocks: "#64748b",
        templates: "#a855f7",
        scenarios: "#dc2626",
        paper: "#f0a03a",
      } as Record<string, string>
    )[item.shelf] ?? "#64748b"
  );
}

const lab = (what: string, layout: string): Use => ({
  place: "Lab",
  what,
  path: "/lab",
  query: `layout=${layout}`,
});
const portfolio = (what: string, layout: string): Use => ({
  place: "Portfolio",
  what,
  path: "/portfolio",
  query: `layout=${layout}`,
});

/** Where a bot shows up: pods trading it, tests, paper, journal, chat, Home. */
function botUses(id: string, name: string): Use[] {
  const uses: Use[] = [];
  for (const p of PODS)
    if (p.bots.some((b) => b.id === id))
      uses.push(
        portfolio(
          `Trades in ${p.name} (${p.mode === "LIVE" ? "live" : "paper"})`,
          "pods",
        ),
      );
  if (TEST_BOTS.some((b) => b.id === id))
    uses.push(lab("Bot in the pod tests", "pod-test"));
  const runs = RUNS.filter((r) => r.symbol.startsWith(name.split(" ")[0]));
  if (runs.length) uses.push(lab(`${runs.length} test runs`, "test"));
  if (CANDIDATES.some((c) => c.entity.id === id))
    uses.push(portfolio("On the road to live", "road"));
  if (JOURNAL[id])
    uses.push(portfolio(`Journal, ${JOURNAL[id].length} notes`, "road"));
  if (id === "btc-breakout") {
    uses.push({
      place: "Copilot",
      what: "Edited in “Tighten the breakout stop”",
      path: "/copilot",
    });
    uses.push({ place: "Home", what: "Pinned on Home", path: "/home" });
    uses.push({
      place: "Mini apps",
      what: "Signals in Research · Crypto",
      path: "/library",
      query: "item=research-crypto",
    });
  }
  if (id === "eth-mr")
    uses.push({
      place: "Home",
      what: "Waiting for you on Home",
      path: "/home",
    });
  return uses;
}

function entityItems(): LibraryItem[] {
  const SHELF: Record<Entity["kind"], ShelfId> = {
    bot: "bots",
    model: "models",
    app: "apps",
    workflow: "workflows",
  };
  return DEMO_ENTITIES.map((e) => {
    const uses: Use[] =
      e.kind === "bot"
        ? botUses(e.id, e.name)
        : e.kind === "model"
          ? [
              lab("Training and slots", "train"),
              ...(e.id === "breakout-scorer"
                ? [lab("Feeds BTC breakout's entries", "build")]
                : [lab("Regime input for Trend rider", "pod-design")]),
            ]
          : e.kind === "app"
            ? [
                {
                  place: "Mini apps",
                  what: e.views?.length
                    ? "Open on the rail"
                    : "Runs headless on the server",
                  path: "/library",
                  query: `item=${e.id}`,
                },
                {
                  place: "Copilot",
                  what: "A target the copilot can call",
                  path: "/copilot",
                },
                ...(e.id === "news-sentiment"
                  ? [
                      {
                        place: "Home" as Place,
                        what: "Feeds the news on Home",
                        path: "/home",
                      },
                    ]
                  : []),
              ]
            : [
                lab("Opens in the editor", "build"),
                { place: "Home", what: "Runs listed on Home", path: "/home" },
              ];
    return {
      id: e.id,
      shelf: SHELF[e.kind],
      name: e.name,
      summary: e.summary,
      family:
        e.family ??
        (e.kind === "app"
          ? e.views?.length
            ? "Mini app"
            : "Headless"
          : undefined),
      version: e.version,
      stage: e.stage,
      updated: "This week",
      uses,
      entity: e,
    };
  });
}

/** Bots trading in Portfolio that have no full Library page in the demo yet. */
function moreBots(): LibraryItem[] {
  const known = new Set(DEMO_ENTITIES.map((e) => e.id));
  const seen = new Set<string>();
  return PODS.flatMap((p) => p.bots)
    .filter((b) => !known.has(b.id) && !seen.has(b.id) && seen.add(b.id))
    .map((b) => ({
      id: b.id,
      shelf: "bots" as const,
      name: b.name,
      summary: `${b.symbol === "Basket" ? "A basket of coins" : b.symbol} spot strategy`,
      family: /mom|rotat/.test(b.id) ? "Momentum" : "Breakout",
      stage: b.state === "trading" ? "Live" : "Paper",
      updated: "This week",
      uses: botUses(b.id, b.name),
    }));
}

function podItems(): LibraryItem[] {
  const designs = LAB_PODS.map((p) => ({
    id: `lab-${p.id}`,
    shelf: "pods" as const,
    name: p.name,
    summary: `Built from ${p.template}`,
    family: "Pod",
    version: p.version,
    stage: STAGE_LABEL[p.stage],
    updated: "Today",
    uses: [
      lab("Designed in the Lab", "pod-design"),
      lab("In the pod tests", "pod-test"),
      ...(p.stage === "paper" ? [lab("Soaking on paper", "pod-paper")] : []),
      ...(p.stage === "live"
        ? [portfolio("Running in Portfolio", "pods")]
        : []),
    ],
    details: SLOTS.map(
      (s) =>
        [
          s.label,
          p.stack[s.id]
            .map((b) => BLOCKS.find((x) => x.id === b)?.name ?? b)
            .join(", ") || "—",
        ] as [string, string],
    ),
  }));
  const running = PODS.map((p) => ({
    id: `pf-${p.id}`,
    shelf: "pods" as const,
    name: p.name,
    summary: `${p.method.label} · ${p.bots.length} ${p.bots.length === 1 ? "bot" : "bots"}`,
    family: "Pod",
    version: p.version,
    stage: p.mode === "LIVE" ? "Live" : "On paper",
    updated: "Today",
    uses: [
      portfolio(
        `${p.mode === "LIVE" ? "Live and paper" : "Paper"} in Portfolio`,
        "pods",
      ),
      portfolio("In the kill switch grid", "live"),
    ],
  }));
  return [...designs, ...running];
}

function blockItems(): LibraryItem[] {
  return BLOCKS.map((b) => ({
    id: `block-${b.id}`,
    shelf: "blocks" as const,
    name: b.name,
    summary: b.what,
    family: SLOTS.find((s) => s.id === b.slot)?.label,
    updated: "—",
    uses: LAB_PODS.filter((p) => p.stack[b.slot].includes(b.id)).map((p) =>
      lab(`In ${p.name} ${p.version}`, "pod-design"),
    ),
    details: [
      ["Slot", SLOTS.find((s) => s.id === b.slot)?.label ?? b.slot],
      ["Built as", b.kind === "form" ? "Built-in" : b.kind],
      ["Setting", b.setting],
    ],
  }));
}

function templateItems(): LibraryItem[] {
  const t = (
    id: string,
    name: string,
    summary: string,
    family: string,
    starts: Use,
  ): LibraryItem => ({
    id: `tpl-${id}`,
    shelf: "templates",
    name,
    summary,
    family,
    updated: "Built in",
    uses: [],
    starts,
  });
  return [
    t(
      "news",
      "News & sentiment workflow",
      "Fetch crypto news and the macro calendar, score sentiment, tag coins and pods",
      "Workflow",
      lab("Opens as a new workflow", "build"),
    ),
    t(
      "nightly",
      "Nightly evidence",
      "Refresh data, retest every bot in evidence, write reports",
      "Workflow",
      lab("Opens as a new workflow", "build"),
    ),
    t(
      "hypothesis",
      "Article to hypothesis",
      "Read an article, pull testable claims, draft a hypothesis with citations",
      "Workflow",
      lab("Opens as a new workflow", "build"),
    ),
    ...POD_TEMPLATES.map((p) =>
      t(
        `pod-${p.id}`,
        p.name,
        p.note,
        "Pod",
        lab("Starts a pod draft", "pod-design"),
      ),
    ),
    ...PORTFOLIO_TEMPLATES.map((p) =>
      t(
        `pf-${p.id}`,
        p.name,
        p.note,
        "Portfolio pod",
        portfolio("Adds a pod to Portfolio, on paper", "pods"),
      ),
    ),
    t(
      "lay-sweep",
      "Sweep and compare",
      "Lab layout: sweep grid, runs, equity and robustness",
      "Lab layout",
      lab("Opens the layout", "test"),
    ),
    t(
      "lay-paper",
      "Paper watch",
      "Lab layout: paper run, live decisions, ready for live",
      "Lab layout",
      lab("Opens the layout", "pod-paper"),
    ),
    t(
      "app-desk",
      "Scalping desk",
      "Mini app: a pod's knobs, live positions and the sweep grid on one screen",
      "Mini app",
      { place: "Mini apps", what: "Builds the mini app", path: "/copilot" },
    ),
  ];
}

function proofItems(): LibraryItem[] {
  const reports = RUNS.filter((r) => r.status === "done").map((r) => ({
    id: r.id,
    shelf: "reports" as const,
    name: `${r.procedure} · ${r.symbol} ${r.timeframe}`,
    summary: `${r.net === null ? "" : `${r.net > 0 ? "+" : ""}${r.net}% net · `}${r.trades} trades · ${r.role}`,
    family: r.procedure,
    updated: "This week",
    uses: [lab("In the runs list", "test"), lab("Ready to compare", "compare")],
  }));
  const paper = [
    ...PAPER_RUNS.map((p) => {
      const pod = LAB_PODS.find((x) => x.id === p.pod)!;
      return {
        id: `paper-${p.pod}`,
        shelf: "paper" as const,
        name: `${pod.name} ${p.version} on paper`,
        summary: `${p.money} · day ${p.day} of ${p.of}`,
        family: "Pod",
        stage: p.verdict === "ready" ? "Ready" : "Soaking",
        updated: "Live now",
        uses: [
          lab("Watched in the Lab", "pod-paper"),
          portfolio("Paper side in Portfolio", "pods"),
        ],
      };
    }),
    ...CANDIDATES.filter((c) => c.stage !== "live").map((c) => ({
      id: `paper-${c.entity.id}`,
      shelf: "paper" as const,
      name: `${c.entity.name} on paper`,
      summary: `Day ${c.days} · ${c.summary}`,
      family: c.entity.family,
      stage: c.stage === "ready" ? "Ready" : "Soaking",
      updated: "Live now",
      uses: [portfolio("On the road to live", "road")],
    })),
  ];
  const scenarios = [
    ...STRESS.map((s) => ({ ...s, by: "Built in" })),
    ...MY_STRESS,
  ].map((s) => ({
    id: `stress-${s.id}`,
    shelf: "scenarios" as const,
    name: s.name,
    summary: s.by,
    family: "Stress",
    updated: s.by === "Built in" ? "Built in" : "Today",
    uses: [lab("On the stress board", "pod-test")],
  }));
  return [...reports, ...paper, ...scenarios];
}

function inputItems(): LibraryItem[] {
  const setups = ASSETS.filter((a) =>
    ["test", "preset", "feature"].includes(a.kind),
  ).map((a) => ({
    id: a.id,
    shelf: "setups" as const,
    name: a.name,
    summary: a.meta,
    family: { test: "Test settings", preset: "Preset", feature: "Feature" }[
      a.kind as "test" | "preset" | "feature"
    ],
    updated: "This week",
    uses: [lab("In Lab resources", a.kind === "feature" ? "train" : "test")],
  }));
  const modelSetups = [
    {
      id: "cfg-gbm-fast",
      name: "GBM · fast",
      meta: "200 trees, depth 4, rate 0.05",
    },
    {
      id: "cfg-gbm-deep",
      name: "GBM · deep",
      meta: "800 trees, depth 8, rate 0.01",
    },
  ].map((m) => ({
    id: m.id,
    shelf: "setups" as const,
    name: m.name,
    summary: m.meta,
    family: "Model settings",
    updated: "This week",
    uses: [lab("Used by the breakout scorer", "train")],
  }));
  const datasets = ASSETS.filter((a) => a.kind === "dataset").map((a) => ({
    id: a.id,
    shelf: "datasets" as const,
    name: a.name,
    summary: a.meta,
    family: "Data",
    updated: "Today",
    uses: [lab("Training and tests read it", "train")],
  }));
  const files = DEMO_ARTIFACTS.map((f) => ({
    id: f.id,
    shelf: "files" as const,
    name: f.name,
    summary: `${f.type} · ${f.size}`,
    family: f.type,
    updated: f.date,
    uses: [
      lab(
        `Made by ${f.producedBy}`,
        f.type === "Model file" ? "train" : "test",
      ),
    ],
    details: [
      ["Made by", f.producedBy],
      ["Fingerprint", f.fp],
      ["Size", f.size],
    ] as [string, string][],
  }));
  return [...setups, ...modelSetups, ...datasets, ...files];
}

function sourceItems(): LibraryItem[] {
  const videos = [
    {
      id: "yt-quant",
      name: "Quant videos (YouTube)",
      how: "Talks and lectures; transcripts go to hypothesis research",
      url: "https://www.youtube.com/results?search_query=quantitative+trading",
    },
  ];
  return [
    ...SOURCES.map((s) => ({
      id: `src-${s.id}`,
      shelf: "sources" as const,
      name: s.name,
      summary: s.how,
      family: s.kind,
      stage: s.status === "ruled" ? "Ruled" : "Proposed",
      updated: "Daily",
      uses: [
        {
          place: "Home" as Place,
          what: "Feeds the news on Home",
          path: "/home",
        },
        lab("Hypothesis research reads it", "build"),
      ],
      details: [["Address", s.url]] as [string, string][],
    })),
    ...videos.map((v) => ({
      id: `src-${v.id}`,
      shelf: "sources" as const,
      name: v.name,
      summary: v.how,
      family: "Video",
      stage: "Proposed",
      updated: "Daily",
      uses: [lab("Hypothesis research reads it", "build")],
      details: [["Address", v.url]] as [string, string][],
    })),
  ];
}

export const LIBRARY: LibraryItem[] = [
  ...entityItems(),
  ...moreBots(),
  ...podItems(),
  ...blockItems(),
  ...templateItems(),
  ...proofItems(),
  ...inputItems(),
  ...sourceItems(),
];

export const itemById = (id: string) => LIBRARY.find((i) => i.id === id);

// Journals, logs and code live inside the things they belong to (operator,
// 2026-10-03: "journals should be connected in bots, models or pods").
const py = (lines: string[]) => lines.join("\n");

function blockCode(b: (typeof BLOCKS)[number]): string {
  const sig = {
    inputs: "def read(market: Market) -> dict:",
    guards: "def check(state: PodState) -> Verdict:",
    allocator:
      "def split(capital: float, bots: list[Bot]) -> dict[str, float]:",
    sizer: "def size(entry: Entry, state: PodState) -> float:",
    throttles: "def factor(state: PodState) -> float:  # 0.0 to 1.0",
    caps: "def cap(order: Order, book: Exposure) -> Order:",
    ledger: "def settle(fill: Fill, ledger: Ledger) -> Ledger:",
  }[b.slot];
  return py([
    `# ${b.name}: ${b.what}`,
    `# Setting: ${b.setting}. Pure: same inputs, same answer.`,
    "",
    sig,
    `    ...  # the daemon shows the real body once wired`,
  ]);
}

for (const item of LIBRARY) {
  const e = item.entity;
  if (item.shelf === "bots") {
    const id = item.id;
    item.journal = JOURNAL[id]
      ? JOURNAL[id].map((n) => ({
          time: n.time,
          text:
            n.r === undefined
              ? n.text
              : `${n.text} (${n.r > 0 ? "+" : ""}${n.r}R)`,
          tone: n.r === undefined ? undefined : n.r >= 0 ? "good" : "bad",
        }))
      : (e?.journal ?? []).map((t) => ({
          time: t.time,
          text: `${t.side} ${t.symbol} ${t.entry} → ${t.exit}${t.note ? `: ${t.note}` : ""}`,
          tone: t.pnl >= 0 ? ("good" as const) : ("bad" as const),
        }));
    item.logs = [
      "09:55:02 signal  breakout above 64,150 (score 0.68)",
      "09:55:02 sent    to pod for sizing",
      "09:55:03 sized   $743.60 after correlation cap ×0.6",
      "09:55:03 filled  0.01159 at 64,152.1, fee $0.74",
    ];
    item.code = {
      lang: "python",
      text: py([
        `# ${item.name}: ${item.summary}`,
        "# The bot decides when; the pod decides how much.",
        "",
        "def on_bar(bar: Bar, state: BotState) -> Signal | None:",
        "    if breaks_out(bar, state.range) and state.score(bar) > 0.60:",
        "        return Signal.buy(stop=bar.close - atr(bar, 14))",
        "    return None",
      ]),
    };
  } else if (item.shelf === "pods" && item.id.startsWith("lab-")) {
    const pod = LAB_PODS.find((p) => `lab-${p.id}` === item.id)!;
    item.journal = [...PAPER_INTERVENTIONS, ...INTERVENTIONS]
      .filter((x) => x.pod === pod.name)
      .map((x) => ({
        time: x.time,
        text: `${x.what} by ${x.by}`,
        tone: x.what.startsWith("Stood") ? ("bad" as const) : undefined,
      }));
    item.code = {
      lang: "yaml",
      text: [
        `pod: ${pod.name}`,
        `version: ${pod.version}`,
        "stack:",
        ...SLOTS.map((s) => `  ${s.id}: [${pod.stack[s.id].join(", ")}]`),
        "  venue_fit: always",
      ].join("\n"),
    };
  } else if (item.shelf === "pods") {
    item.journal = [
      { time: "Today 10:12", text: "Refused an entry: volatility spike" },
      {
        time: "Yesterday",
        text: "Paper side matched live within 0.4%",
        tone: "good",
      },
      { time: "Sep 30", text: "You raised risk per trade to 0.5% (v3)" },
    ];
  } else if (item.shelf === "blocks") {
    const b = BLOCKS.find((x) => `block-${x.id}` === item.id)!;
    item.code = { lang: "python", text: blockCode(b) };
  } else if (item.shelf === "models") {
    item.logs = [
      "epoch 1  train 0.684  valid 0.691",
      "epoch 40 train 0.612  valid 0.655",
      "fold 12/12 AUC 0.61 (±0.03)",
      "leakage checks 6/6 pass",
      "saved model file, fingerprint fp1:77f0…aa19",
    ];
    item.journal = [
      {
        time: "Today 12:08",
        text: "Retrained on data to Sep 30",
        tone: "good",
      },
      { time: "Sep 24", text: "You added funding rate as a feature" },
    ];
    item.code = {
      lang: "yaml",
      text: (e?.parameters ?? [])
        .map(([k, v]) => `${k.toLowerCase().replaceAll(" ", "_")}: ${v}`)
        .join("\n"),
    };
  } else if (item.shelf === "workflows" && e?.steps) {
    item.code = {
      lang: "yaml",
      text: [
        `workflow: ${item.name}`,
        "steps:",
        ...e.steps.map((s) => `  - ${s}`),
      ].join("\n"),
    };
    item.logs = [
      "02:00 started (schedule)",
      ...e.steps.map(
        (s, i) => `02:${String(3 + i * 4).padStart(2, "0")} ${s} ok`,
      ),
      "02:21 finished",
    ];
  } else if (item.shelf === "setups") {
    item.code = {
      lang: "yaml",
      text: [
        `name: ${item.name}`,
        `kind: ${item.family}`,
        `settings: ${item.summary}`,
      ].join("\n"),
    };
  }
}
