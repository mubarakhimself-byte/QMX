/**
 * DEMO data for Portfolio: spot crypto only (operator ruling 2026-10-03; no
 * CFDs, no FX broker, no prop firms). Money is run by **pods**: a pod is one
 * way of doing risk management and position sizing (a Book + BMS from the
 * docs is one method; models, Lab workflows and hybrids are others). Every
 * value here names the backend source it would come from. Nothing is real.
 */
import { equityWalk } from "$lib/qmx/charts";
import type { Entity } from "$lib/qmx/entities";

export type Venue = { id: string; name: string; market: string };
export const VENUES: Venue[] = [
  { id: "binance", name: "Binance", market: "Spot" },
  { id: "bybit", name: "Bybit", market: "Spot" },
  { id: "coinbase", name: "Coinbase", market: "Advanced spot" },
  { id: "kraken", name: "Kraken", market: "Spot" },
];

export type Ksa = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "BLACK";
export type Account = {
  id: string;
  venue: string;
  name: string;
  role: "live" | "paper" | "watch";
  equity: number;
  today: number;
  quote: string;
  node: string;
  ksa: Ksa;
};

export const ACCOUNTS: Account[] = [
  {
    id: "bn-spot",
    venue: "binance",
    name: "Binance spot",
    role: "live",
    equity: 38420,
    today: 1.6,
    quote: "USDT",
    node: "tokyo",
    ksa: "GREEN",
  },
  {
    id: "bn-test",
    venue: "binance",
    name: "Binance testnet",
    role: "paper",
    equity: 25000,
    today: 0.4,
    quote: "USDT",
    node: "local",
    ksa: "GREEN",
  },
  {
    id: "by-spot",
    venue: "bybit",
    name: "Bybit spot",
    role: "live",
    equity: 16210,
    today: 2.8,
    quote: "USDT",
    node: "tokyo",
    ksa: "YELLOW",
  },
  {
    id: "cb-spot",
    venue: "coinbase",
    name: "Coinbase",
    role: "live",
    equity: 6150,
    today: -0.7,
    quote: "USD",
    node: "frankfurt",
    ksa: "GREEN",
  },
  {
    id: "kr-watch",
    venue: "kraken",
    name: "Kraken",
    role: "watch",
    equity: 2040,
    today: 0.2,
    quote: "USD",
    node: "frankfurt",
    ksa: "GREEN",
  },
];

export type Node = {
  id: string;
  name: string;
  where: string;
  latency: { venue: string; ms: number }[];
  status: "up" | "degraded" | "down";
  mode: "live" | "paper";
  cpu: number;
  uptime: string;
};
export const NODES: Node[] = [
  {
    id: "tokyo",
    name: "Tokyo",
    where: "AWS ap-northeast-1",
    latency: [
      { venue: "Binance", ms: 9 },
      { venue: "Bybit", ms: 11 },
    ],
    status: "up",
    mode: "live",
    cpu: 34,
    uptime: "18 days",
  },
  {
    id: "frankfurt",
    name: "Frankfurt",
    where: "Hetzner FSN1",
    latency: [
      { venue: "Coinbase", ms: 21 },
      { venue: "Kraken", ms: 17 },
    ],
    status: "degraded",
    mode: "live",
    cpu: 71,
    uptime: "3 days",
  },
  {
    id: "local",
    name: "This laptop",
    where: "Dell Precision 5550",
    latency: [{ venue: "Binance testnet", ms: 140 }],
    status: "up",
    mode: "paper",
    cpu: 22,
    uptime: "6 hours",
  },
];

/** How a pod does risk and sizing. All but "book" are new scope. */
export type Method = {
  kind: "book" | "model" | "workflow" | "hybrid" | "rules";
  label: string;
  from: string;
};
export type Knob = {
  key: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
};
export type Guard = { name: string; now: string; limit: string; used: number };
export type PodBot = {
  id: string;
  name: string;
  symbol: string;
  weight: number;
  state: "trading" | "benched" | "paused";
  pnl: number;
};

export type Pod = {
  id: string;
  name: string;
  method: Method;
  account: string;
  mode: "LIVE" | "PAPER";
  version: string;
  equity: number;
  start: number;
  floor: number;
  today: number;
  curve: number[];
  knobs: Knob[];
  guards: Guard[];
  bots: PodBot[];
};

export const PODS: Pod[] = [
  {
    id: "core",
    name: "BTC & ETH core",
    method: { kind: "book", label: "Book + BMS", from: "Docs default ladder" },
    account: "bn-spot",
    mode: "LIVE",
    version: "v3",
    equity: 24180,
    start: 20000,
    floor: 17000,
    today: 1.4,
    curve: equityWalk(12, 120, 0.0016, 0.009),
    knobs: [
      {
        key: "risk",
        label: "Risk per trade",
        value: 0.5,
        min: 0.1,
        max: 2,
        step: 0.05,
        unit: "%",
      },
      {
        key: "daily",
        label: "Daily loss stop",
        value: 2,
        min: 0.5,
        max: 6,
        step: 0.25,
        unit: "%",
      },
      {
        key: "exposure",
        label: "Most in one coin",
        value: 60,
        min: 10,
        max: 100,
        step: 5,
        unit: "%",
      },
      {
        key: "floor",
        label: "Kill line",
        value: 17000,
        min: 12000,
        max: 20000,
        step: 500,
        unit: "$",
      },
    ],
    guards: [
      { name: "Daily loss", now: "$96", limit: "$484", used: 0.2 },
      { name: "BTC share", now: "54%", limit: "60%", used: 0.9 },
      {
        name: "Above kill line",
        now: "$7,180",
        limit: "$7,180 room",
        used: 0.3,
      },
    ],
    bots: [
      {
        id: "btc-breakout",
        name: "BTC breakout",
        symbol: "BTCUSDT",
        weight: 55,
        state: "trading",
        pnl: 1240,
      },
      {
        id: "eth-trend",
        name: "ETH trend",
        symbol: "ETHUSDT",
        weight: 45,
        state: "trading",
        pnl: 410,
      },
    ],
  },
  {
    id: "alts",
    name: "Alt momentum",
    method: {
      kind: "model",
      label: "Volatility target",
      from: "Lab model · Vol forecaster v2",
    },
    account: "by-spot",
    mode: "LIVE",
    version: "v2",
    equity: 16210,
    start: 15000,
    floor: 12000,
    today: 2.8,
    curve: equityWalk(23, 120, 0.0021, 0.016),
    knobs: [
      {
        key: "target",
        label: "Yearly volatility target",
        value: 35,
        min: 10,
        max: 80,
        step: 5,
        unit: "%",
      },
      {
        key: "cap",
        label: "Most in one coin",
        value: 25,
        min: 5,
        max: 50,
        step: 5,
        unit: "%",
      },
      {
        key: "daily",
        label: "Daily loss stop",
        value: 3,
        min: 1,
        max: 8,
        step: 0.5,
        unit: "%",
      },
    ],
    guards: [
      { name: "Volatility now", now: "41%", limit: "35% target", used: 1 },
      { name: "SOL share", now: "23%", limit: "25%", used: 0.92 },
      { name: "Daily loss", now: "$0", limit: "$486", used: 0 },
    ],
    bots: [
      {
        id: "sol-mom",
        name: "SOL momentum",
        symbol: "SOLUSDT",
        weight: 40,
        state: "trading",
        pnl: 620,
      },
      {
        id: "avax-mom",
        name: "AVAX momentum",
        symbol: "AVAXUSDT",
        weight: 30,
        state: "trading",
        pnl: 180,
      },
      {
        id: "link-mom",
        name: "LINK momentum",
        symbol: "LINKUSDT",
        weight: 30,
        state: "benched",
        pnl: -95,
      },
    ],
  },
  {
    id: "rotation",
    name: "Weekly rotation",
    method: {
      kind: "workflow",
      label: "Rotation workflow",
      from: "Lab workflow · Top-5 rotation v2",
    },
    account: "cb-spot",
    mode: "LIVE",
    version: "v1",
    equity: 6150,
    start: 6000,
    floor: 5100,
    today: -0.7,
    curve: equityWalk(31, 120, 0.0005, 0.011),
    knobs: [
      {
        key: "coins",
        label: "Coins held",
        value: 5,
        min: 2,
        max: 10,
        step: 1,
        unit: "",
      },
      {
        key: "drift",
        label: "Rebalance when off by",
        value: 10,
        min: 2,
        max: 30,
        step: 1,
        unit: "%",
      },
    ],
    guards: [
      {
        name: "Next rebalance",
        now: "Monday 00:00",
        limit: "weekly",
        used: 0.6,
      },
      { name: "Above kill line", now: "$1,050", limit: "$900 room", used: 0.5 },
    ],
    bots: [
      {
        id: "rotator",
        name: "Top-5 rotator",
        symbol: "Basket",
        weight: 100,
        state: "trading",
        pnl: 150,
      },
    ],
  },
  {
    id: "meanrev",
    name: "Mean reversion",
    method: {
      kind: "hybrid",
      label: "Rules + regime model",
      from: "Lab · Regime HMM v1 throttles the rules",
    },
    account: "bn-test",
    mode: "PAPER",
    version: "v4",
    equity: 25640,
    start: 25000,
    floor: 21000,
    today: 0.4,
    curve: equityWalk(41, 120, 0.0009, 0.006),
    knobs: [
      {
        key: "risk",
        label: "Risk per trade",
        value: 0.4,
        min: 0.1,
        max: 2,
        step: 0.05,
        unit: "%",
      },
      {
        key: "throttle",
        label: "Size in trending regime",
        value: 30,
        min: 0,
        max: 100,
        step: 10,
        unit: "%",
      },
    ],
    guards: [
      { name: "Regime", now: "trending", limit: "size cut to 30%", used: 0.7 },
      { name: "Daily loss", now: "$40", limit: "$512", used: 0.08 },
    ],
    bots: [
      {
        id: "eth-mr",
        name: "ETH mean reversion",
        symbol: "ETHUSDT",
        weight: 100,
        state: "trading",
        pnl: 640,
      },
    ],
  },
];

export const accountById = (id: string) => ACCOUNTS.find((a) => a.id === id);
export const venueById = (id: string) => VENUES.find((v) => v.id === id);
export const nodeById = (id: string) => NODES.find((n) => n.id === id);
export const podById = (id: string) => PODS.find((p) => p.id === id);

/** Trading bots across pods, for the per-bot charts on Live. */
export const TRADING_BOTS = PODS.flatMap((p) =>
  p.bots
    .filter((b) => b.symbol !== "Basket")
    .map((b) => ({ ...b, pod: p.name, mode: p.mode })),
);
export const BASE_PRICE: Record<string, [number, number]> = {
  BTCUSDT: [64210, 0],
  ETHUSDT: [3118, 1],
  SOLUSDT: [152.4, 2],
  AVAXUSDT: [27.6, 2],
  LINKUSDT: [11.84, 3],
};

/** Bots on the road to live: paper first (anything earlier stays in the Lab). */
export type Candidate = {
  entity: Entity;
  stage: "paper" | "ready" | "live";
  pod: string;
  days: number;
  checks: { name: string; ok: boolean | null }[];
  summary: string;
};

const bot = (
  id: string,
  name: string,
  summary: string,
  stage: Entity["stage"],
  m: [string, string, string, string],
): Entity => ({
  id,
  kind: "bot",
  name,
  summary,
  stage,
  version: "v1",
  fp: "fp1:" + id.slice(0, 4),
  family: "Momentum",
  measures: [
    {
      key: "net",
      label: "Net",
      value: m[0],
      help: "Return over the paper period",
      tone: m[0].startsWith("−") ? "down" : "up",
    },
    {
      key: "dd",
      label: "Max drawdown",
      value: m[1],
      help: "Worst fall from a peak",
      tone: "down",
    },
    {
      key: "win",
      label: "Win rate",
      value: m[2],
      help: "Share of trades that made money",
    },
    {
      key: "trades",
      label: "Trades",
      value: m[3],
      help: "Closed trades on paper",
    },
  ],
  spark: equityWalk(id.length * 13, 40, 0.002, 0.012),
});

export const CANDIDATES: Candidate[] = [
  {
    entity: bot(
      "eth-mr",
      "ETH mean reversion",
      "Fades 2σ moves on ETH in calm regimes",
      "Paper",
      ["+2.6%", "−1.1%", "61%", "38"],
    ),
    stage: "paper",
    pod: "Mean reversion",
    days: 12,
    checks: [
      { name: "30 days on paper", ok: false },
      { name: "Paper drawdown under 5%", ok: true },
      { name: "Matches its Lab evidence", ok: true },
    ],
    summary:
      "Keep on paper until day 30, then move ETH mean reversion to Binance spot inside a new pod.",
  },
  {
    entity: bot(
      "doge-brk",
      "DOGE breakout",
      "Breakouts on DOGE with volume confirmation",
      "Paper",
      ["−0.8%", "−3.9%", "44%", "21"],
    ),
    stage: "paper",
    pod: "Alt momentum (paper copy)",
    days: 9,
    checks: [
      { name: "30 days on paper", ok: false },
      { name: "Paper drawdown under 5%", ok: true },
      { name: "Matches its Lab evidence", ok: false },
    ],
    summary:
      "Paper results trail the Lab evidence; review before going further.",
  },
  {
    entity: bot(
      "avax-mom",
      "AVAX momentum v2",
      "Momentum on AVAX with a volatility filter",
      "Paper",
      ["+4.1%", "−2.2%", "53%", "47"],
    ),
    stage: "ready",
    pod: "Alt momentum",
    days: 31,
    checks: [
      { name: "30 days on paper", ok: true },
      { name: "Paper drawdown under 5%", ok: true },
      { name: "Matches its Lab evidence", ok: true },
      { name: "Your signature", ok: null },
    ],
    summary:
      "Replace AVAX momentum v1 with v2 in Alt momentum on Bybit spot. Activates at the next day boundary.",
  },
  {
    entity: bot(
      "sol-mom",
      "SOL momentum",
      "Momentum on SOL, sized by the volatility target",
      "Live",
      ["+6.3%", "−3.4%", "55%", "64"],
    ),
    stage: "live",
    pod: "Alt momentum",
    days: 18,
    checks: [
      { name: "Signed", ok: true },
      { name: "Activated", ok: true },
      { name: "First 30 live days", ok: null },
    ],
    summary: "Live since Sep 15 in Alt momentum.",
  },
];

export type JournalNote = {
  time: string;
  kind: "trade" | "note" | "event";
  text: string;
  r?: number;
};
export const JOURNAL: Record<string, JournalNote[]> = {
  "avax-mom": [
    {
      time: "Today 09:40",
      kind: "trade",
      text: "Bought 110 AVAX at 28.30 on a breakout with volume.",
      r: 0,
    },
    {
      time: "Yesterday 18:10",
      kind: "trade",
      text: "Sold 95 AVAX at 27.95; trailing stop.",
      r: 0.8,
    },
    {
      time: "Sep 30",
      kind: "event",
      text: "Day 30 on paper: all checks passed.",
    },
  ],
  "sol-mom": [
    {
      time: "Today 07:55",
      kind: "trade",
      text: "Bought 24 SOL at 146.10; volatility target allows 0.9 R.",
      r: 0,
    },
    {
      time: "Yesterday 15:20",
      kind: "event",
      text: "SOL token unlock announced for Friday; size held.",
    },
  ],
  "doge-brk": [
    {
      time: "Today 10:05",
      kind: "trade",
      text: "Bought DOGE at 0.1172; stopped at 0.1151.",
      r: -1,
    },
    {
      time: "Yesterday",
      kind: "note",
      text: "Paper results trail the Lab by 2.1%; slippage looks higher than modelled.",
    },
  ],
  "eth-mr": [
    {
      time: "Today 11:20",
      kind: "trade",
      text: "Sold 0.6 ETH at 3,131 after a 2.1σ spike; target hit.",
      r: 1.2,
    },
    {
      time: "Today 08:05",
      kind: "event",
      text: "Regime turned trending; size cut to 30%.",
    },
    {
      time: "Yesterday 22:40",
      kind: "trade",
      text: "Bought 0.8 ETH at 3,052; stopped out at 3,021.",
      r: -1,
    },
    {
      time: "Yesterday 09:15",
      kind: "note",
      text: "You: watch how it behaves around the CPI print.",
    },
  ],
};

export type NewsItem = {
  when: string;
  title: string;
  kind: "crypto" | "fx";
  impact: "high" | "medium" | "low";
  sentiment: number;
  affects: string[];
  source: string;
};
export const NEWS: NewsItem[] = [
  {
    when: "in 2h",
    title: "US CPI (Sep)",
    kind: "fx",
    impact: "high",
    sentiment: -0.2,
    affects: ["BTC", "ETH"],
    source: "Forex Factory calendar",
  },
  {
    when: "in 5h",
    title: "FOMC minutes",
    kind: "fx",
    impact: "high",
    sentiment: -0.1,
    affects: ["BTC", "ETH", "SOL"],
    source: "Forex Factory calendar",
  },
  {
    when: "now",
    title: "Dollar index up 0.6% today",
    kind: "fx",
    impact: "medium",
    sentiment: -0.4,
    affects: ["BTC"],
    source: "Price feed (DXY)",
  },
  {
    when: "12m ago",
    title: "Spot BTC ETFs took in $412M yesterday",
    kind: "crypto",
    impact: "high",
    sentiment: 0.7,
    affects: ["BTC"],
    source: "The Block RSS",
  },
  {
    when: "40m ago",
    title: "SOL token unlock of 2.1M on Friday",
    kind: "crypto",
    impact: "medium",
    sentiment: -0.3,
    affects: ["SOL"],
    source: "CryptoPanic",
  },
  {
    when: "1h ago",
    title: "Binance lists a new AVAX pair",
    kind: "crypto",
    impact: "low",
    sentiment: 0.3,
    affects: ["AVAX"],
    source: "Binance announcements RSS",
  },
  {
    when: "2h ago",
    title: "Crowd mood on ETH turns bullish",
    kind: "crypto",
    impact: "medium",
    sentiment: 0.5,
    affects: ["ETH"],
    source: "Sentiment workflow (template)",
  },
];

export const CORR: { names: string[]; m: number[][] } = {
  names: ["Core", "Alt mom.", "Rotation", "Mean rev."],
  m: [
    [1, 0.64, 0.58, 0.12],
    [0.64, 1, 0.71, 0.08],
    [0.58, 0.71, 1, 0.1],
    [0.12, 0.08, 0.1, 1],
  ],
};

export const EXPOSURE = [
  { asset: "BTC", share: 41 },
  { asset: "ETH", share: 24 },
  { asset: "SOL", share: 11 },
  { asset: "AVAX", share: 6 },
  { asset: "LINK", share: 2 },
  { asset: "Stablecoins", share: 16 },
];

export const TEMPLATES = [
  {
    id: "t-core",
    name: "BTC & ETH core",
    note: "Book + BMS, 0.5% per trade, 2% daily stop, kill line at −15%",
  },
  {
    id: "t-vol",
    name: "Volatility target",
    note: "A model sizes to a yearly volatility; hard caps per coin",
  },
  {
    id: "t-rotation",
    name: "Weekly rotation",
    note: "Hold the top N coins by momentum; rebalance on drift",
  },
  {
    id: "t-dca",
    name: "Accumulation ladder",
    note: "Buy in steps on dips; never sells below cost",
  },
  {
    id: "t-meanrev",
    name: "Mean reversion with regime",
    note: "Rules size; a regime model cuts size when trending",
  },
  {
    id: "t-canary",
    name: "Canary",
    note: "Tiny live size for a new bot, ramps up on a schedule",
  },
  {
    id: "t-sandbox",
    name: "Paper sandbox",
    note: "Testnet capital, sanity caps only, report after N days",
  },
  {
    id: "t-news",
    name: "News-aware",
    note: "Pauses entries around high-impact events; uses the news workflow",
  },
  {
    id: "t-own",
    name: "Build your own in the Lab",
    note: "Wire your own blocks; the copilot brings it here",
  },
];
