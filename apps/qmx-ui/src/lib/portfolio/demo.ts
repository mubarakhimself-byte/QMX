/**
 * DEMO data for Portfolio. Shapes follow the risk and trading-node docs:
 * venue → account → BMS (one per account) → Books → seats; the USD sizing
 * ladder; Book mode LIVE | PAPER; binding live | paper | stood-down; seat
 * active | benched; KSA levels; promotion vs activation. "Risk engine" per
 * Book (rules, a model, or both) is the operator's vision and new scope.
 * Nothing here is real money.
 */
import { equityWalk } from "$lib/qmx/charts";

export type Venue = {
  id: string;
  name: string;
  kind: "crypto" | "fx" | "prop";
  platform: string;
};
export const VENUES: Venue[] = [
  {
    id: "binance",
    name: "Binance",
    kind: "crypto",
    platform: "Spot + USDⓈ-M futures",
  },
  { id: "bybit", name: "Bybit", kind: "crypto", platform: "Unified account" },
  { id: "coinbase", name: "Coinbase", kind: "crypto", platform: "Advanced" },
  { id: "icm", name: "IC Markets", kind: "fx", platform: "cTrader" },
  { id: "ftmo", name: "FTMO", kind: "prop", platform: "cTrader" },
];

export type Role = "live" | "demo" | "prop-firm" | "sensing-only";
export type Account = {
  id: string;
  venue: string;
  name: string;
  role: Role;
  equity: number;
  today: number;
  settles: string;
  node: string;
  reconciled: "reconciled" | "drift" | "unknown";
  ksa: Ksa;
};
export type Ksa = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "BLACK";

export const ACCOUNTS: Account[] = [
  {
    id: "bn-main",
    venue: "binance",
    name: "Binance main",
    role: "live",
    equity: 24180,
    today: 1.9,
    settles: "USDT",
    node: "vps-tokyo",
    reconciled: "reconciled",
    ksa: "GREEN",
  },
  {
    id: "by-demo",
    venue: "bybit",
    name: "Bybit demo",
    role: "demo",
    equity: 10000,
    today: 0.6,
    settles: "USDT",
    node: "local",
    reconciled: "reconciled",
    ksa: "GREEN",
  },
  {
    id: "cb-watch",
    venue: "coinbase",
    name: "Coinbase",
    role: "sensing-only",
    equity: 3120,
    today: -0.4,
    settles: "USD",
    node: "vps-tokyo",
    reconciled: "reconciled",
    ksa: "GREEN",
  },
  {
    id: "ic-live",
    venue: "icm",
    name: "IC Markets live",
    role: "live",
    equity: 48630,
    today: 0.14,
    settles: "USD",
    node: "vps-london",
    reconciled: "drift",
    ksa: "YELLOW",
  },
  {
    id: "ic-demo",
    venue: "icm",
    name: "IC Markets demo",
    role: "demo",
    equity: 50000,
    today: 0.3,
    settles: "USD",
    node: "local",
    reconciled: "reconciled",
    ksa: "GREEN",
  },
  {
    id: "ftmo-1",
    venue: "ftmo",
    name: "FTMO challenge",
    role: "prop-firm",
    equity: 98420,
    today: -1.2,
    settles: "USD",
    node: "vps-london",
    reconciled: "reconciled",
    ksa: "ORANGE",
  },
];

export type Node = {
  id: string;
  name: string;
  where: string;
  latency: string;
  status: "up" | "degraded" | "down";
  mode: "live" | "paper";
};
export const NODES: Node[] = [
  {
    id: "vps-london",
    name: "London node",
    where: "Equinix LD4 · VPS",
    latency: "1.8 ms to IC Markets",
    status: "up",
    mode: "live",
  },
  {
    id: "vps-tokyo",
    name: "Tokyo node",
    where: "AWS ap-northeast-1",
    latency: "14 ms to Binance",
    status: "degraded",
    mode: "live",
  },
  {
    id: "local",
    name: "This laptop",
    where: "Dell Precision 5550",
    latency: "paper only",
    status: "up",
    mode: "paper",
  },
];

export type Engine = {
  kind: "rules" | "model" | "hybrid";
  label: string;
  note: string;
};
export type Rule = {
  name: string;
  value: string;
  limit: string;
  used: number;
  state: "ok" | "near" | "tripped";
};
export type Seat = {
  bot: string;
  state: "active" | "benched";
  r: string;
  pnl: number;
};
export type Book = {
  id: string;
  name: string;
  template: string;
  version: string;
  account: string;
  mode: "LIVE" | "PAPER";
  binding: "live" | "paper" | "stood-down";
  engine: Engine;
  capital: number;
  killLine: number;
  runwayPeriods: number;
  seatAllowance: number;
  equity: number;
  lossToday: number;
  equitySeries: number[];
  rules: Rule[];
  seats: Seat[];
};

function ladder(
  b: Pick<Book, "capital" | "killLine" | "runwayPeriods" | "seatAllowance">,
) {
  const runway = b.capital - b.killLine;
  const budget = runway / b.runwayPeriods;
  return { runway, budget, rPrice: budget / b.seatAllowance };
}
export const sizing = ladder;

export const BOOKS: Book[] = [
  {
    id: "fx-core",
    name: "FX core",
    template: "Conservative FX",
    version: "v3",
    account: "ic-live",
    mode: "LIVE",
    binding: "live",
    engine: { kind: "rules", label: "Rules", note: "Default sizing ladder" },
    capital: 25000,
    killLine: 21500,
    runwayPeriods: 10,
    seatAllowance: 5,
    equity: 25840,
    lossToday: 120,
    equitySeries: equityWalk(11, 90, 0.0012, 0.006),
    rules: [
      {
        name: "Risk per trade",
        value: "0.28%",
        limit: "0.30%",
        used: 0.93,
        state: "near",
      },
      {
        name: "Daily loss",
        value: "$120",
        limit: "$350",
        used: 0.34,
        state: "ok",
      },
      {
        name: "Correlated pairs",
        value: "2",
        limit: "3",
        used: 0.67,
        state: "ok",
      },
      {
        name: "News window",
        value: "USD CPI in 2h",
        limit: "blocks new entries",
        used: 0.5,
        state: "near",
      },
    ],
    seats: [
      { bot: "EURUSD H1 GBM", state: "active", r: "1.2 R", pnl: 412 },
      { bot: "US500 Trend", state: "active", r: "0.8 R", pnl: -43 },
      { bot: "Gold Fade", state: "benched", r: "0 R", pnl: -96 },
    ],
  },
  {
    id: "crypto-mom",
    name: "Crypto momentum",
    template: "Crypto momentum",
    version: "v1",
    account: "bn-main",
    mode: "LIVE",
    binding: "live",
    engine: {
      kind: "model",
      label: "Vol forecaster",
      note: "Sizes by forecast volatility (model, new scope)",
    },
    capital: 15000,
    killLine: 12000,
    runwayPeriods: 8,
    seatAllowance: 4,
    equity: 16210,
    lossToday: 0,
    equitySeries: equityWalk(23, 90, 0.0022, 0.014),
    rules: [
      {
        name: "Per-bot cap",
        value: "18%",
        limit: "20%",
        used: 0.9,
        state: "near",
      },
      {
        name: "Portfolio trailing stop",
        value: "−3.1%",
        limit: "−8%",
        used: 0.39,
        state: "ok",
      },
      {
        name: "Rebalance drift",
        value: "6%",
        limit: "10%",
        used: 0.6,
        state: "ok",
      },
    ],
    seats: [
      { bot: "BTC breakout", state: "active", r: "1.0 R", pnl: 640 },
      { bot: "ETH trend", state: "active", r: "0.7 R", pnl: 210 },
      { bot: "SOL momentum", state: "active", r: "0.5 R", pnl: -88 },
    ],
  },
  {
    id: "crypto-mr",
    name: "Crypto neutral",
    template: "Market-neutral",
    version: "v2",
    account: "by-demo",
    mode: "PAPER",
    binding: "paper",
    engine: {
      kind: "hybrid",
      label: "Rules + regime HMM",
      note: "Rules size; the regime model throttles (new scope)",
    },
    capital: 10000,
    killLine: 8500,
    runwayPeriods: 10,
    seatAllowance: 5,
    equity: 10240,
    lossToday: 35,
    equitySeries: equityWalk(31, 90, 0.0008, 0.005),
    rules: [
      {
        name: "Net exposure",
        value: "4%",
        limit: "±10%",
        used: 0.4,
        state: "ok",
      },
      {
        name: "Funding cost",
        value: "0.02%/8h",
        limit: "0.05%",
        used: 0.4,
        state: "ok",
      },
    ],
    seats: [{ bot: "Basis carry", state: "active", r: "0.6 R", pnl: 75 }],
  },
  {
    id: "prop",
    name: "Prop challenge",
    template: "Prop-firm challenge",
    version: "v1",
    account: "ftmo-1",
    mode: "LIVE",
    binding: "live",
    engine: {
      kind: "rules",
      label: "Rules",
      note: "Hard daily and total loss",
    },
    capital: 100000,
    killLine: 90000,
    runwayPeriods: 2,
    seatAllowance: 5,
    equity: 98420,
    lossToday: 3900,
    equitySeries: equityWalk(41, 90, -0.0002, 0.006),
    rules: [
      {
        name: "Daily loss",
        value: "$3,900",
        limit: "$5,000",
        used: 0.78,
        state: "near",
      },
      {
        name: "Total loss",
        value: "$1,580",
        limit: "$10,000",
        used: 0.16,
        state: "ok",
      },
      {
        name: "Reducing mode",
        value: "on at 60%",
        limit: "flatten at 80%",
        used: 0.78,
        state: "near",
      },
    ],
    seats: [{ bot: "US500 Trend", state: "active", r: "0.4 R", pnl: -1200 }],
  },
  {
    id: "gold",
    name: "Gold",
    template: "Drawdown recovery",
    version: "v2",
    account: "ic-live",
    mode: "PAPER",
    binding: "stood-down",
    engine: {
      kind: "rules",
      label: "Rules",
      note: "Halves size after 5% drawdown",
    },
    capital: 8000,
    killLine: 7000,
    runwayPeriods: 5,
    seatAllowance: 4,
    equity: 6980,
    lossToday: 0,
    equitySeries: equityWalk(51, 90, -0.0012, 0.008),
    rules: [
      {
        name: "Kill line",
        value: "$6,980",
        limit: "$7,000",
        used: 1,
        state: "tripped",
      },
    ],
    seats: [{ bot: "Gold Fade", state: "benched", r: "0 R", pnl: 0 }],
  },
];

export const accountById = (id: string) => ACCOUNTS.find((a) => a.id === id);
export const venueById = (id: string) => VENUES.find((v) => v.id === id);
export const nodeById = (id: string) => NODES.find((n) => n.id === id);
export const bookById = (id: string) => BOOKS.find((b) => b.id === id);
export const isLive = (b: Book) => b.mode === "LIVE";

export type Promotion = {
  id: string;
  what: string;
  kind: "bot" | "model" | "book";
  stage: "research-paper" | "node-paper" | "live";
  book: string;
  detail: string;
  gates: { name: string; ok: boolean | null }[];
  summary: string;
};

export const PROMOTIONS: Promotion[] = [
  {
    id: "pr-1",
    what: "EURUSD H1 GBM v8",
    kind: "bot",
    stage: "research-paper",
    book: "fx-core",
    detail: "Walk-forward 12 folds · Sharpe 1.51",
    gates: [
      { name: "Evidence attached (CT-32)", ok: true },
      { name: "Admission layers 1–3", ok: true },
      { name: "Capability check on IC Markets", ok: true },
      { name: "No unsigned money-rule change", ok: false },
    ],
    summary:
      "Promote EURUSD H1 GBM v8 to node-paper on IC Markets demo, replacing v7 after a 7-day soak.",
  },
  {
    id: "pr-2",
    what: "Breakout scorer",
    kind: "model",
    stage: "research-paper",
    book: "crypto-mom",
    detail: "AUC 0.61 · plugs into entry signal",
    gates: [
      { name: "Evidence attached", ok: true },
      { name: "Sealed year opened once", ok: true },
      { name: "Model object defined (new scope)", ok: null },
    ],
    summary:
      "Use the breakout scorer as the entry signal for BTC breakout in Crypto momentum.",
  },
  {
    id: "pr-3",
    what: "Gold Fade v4",
    kind: "bot",
    stage: "node-paper",
    book: "gold",
    detail: "Soak day 4 of 7 on IC Markets demo",
    gates: [
      { name: "Soak complete", ok: false },
      { name: "Paper equity above floor", ok: true },
    ],
    summary: "Return Gold Fade v4 to live on Gold after the soak.",
  },
  {
    id: "pr-4",
    what: "US500 Trend v12",
    kind: "bot",
    stage: "live",
    book: "fx-core",
    detail: "Signed · activates at the next day boundary",
    gates: [
      { name: "Promotion card signed", ok: true },
      { name: "Activation", ok: null },
    ],
    summary: "Activate US500 Trend v12 on FX core. Takes effect at 00:00 UTC.",
  },
];

export type ApprovalRequest = {
  id: string;
  from: string;
  what: string;
  moneyPath: boolean;
  diff?: [string, string, string][];
  when: string;
};

/** QMA approval_request messages: separate from node signatures (DEC-0345). */
export const APPROVALS: ApprovalRequest[] = [
  {
    id: "ap-1",
    from: "Portfolio Manager quant",
    what: "Crypto momentum v2: give BTC breakout more room",
    moneyPath: true,
    diff: [
      ["Per-bot cap", "20%", "25%"],
      ["Rebalance drift", "10%", "8%"],
    ],
    when: "12 min ago",
  },
  {
    id: "ap-2",
    from: "Analyst quant",
    what: "Run a 120-run sweep on the Research VPS (about $1.10)",
    moneyPath: false,
    when: "40 min ago",
  },
];

export type NewsItem = {
  when: string;
  title: string;
  impact: "high" | "medium";
  affects: string[];
};
export const EVENTS: NewsItem[] = [
  {
    when: "in 2h",
    title: "US CPI (Sep)",
    impact: "high",
    affects: ["FX core", "Prop challenge"],
  },
  {
    when: "in 5h",
    title: "FOMC minutes",
    impact: "high",
    affects: ["FX core", "Crypto momentum"],
  },
  {
    when: "tomorrow",
    title: "ETH Pectra upgrade window",
    impact: "medium",
    affects: ["Crypto momentum", "Crypto neutral"],
  },
];

/** Allocation what-if (new scope: no allocation object in the docs, DEC-0154). */
export const ALLOC = BOOKS.filter((b) => b.binding !== "stood-down").map(
  (b, i) => ({
    book: b.name,
    now: [32, 20, 13, 35][i] ?? 0,
    proposed: [30, 28, 17, 25][i] ?? 0,
    vol: [6.1, 14.2, 4.3, 7.8][i] ?? 0,
  }),
);

export const CORR: { names: string[]; m: number[][] } = {
  names: ["FX core", "Crypto mom.", "Crypto neutral", "Prop"],
  m: [
    [1, 0.18, 0.05, 0.72],
    [0.18, 1, 0.31, 0.12],
    [0.05, 0.31, 1, 0.02],
    [0.72, 0.12, 0.02, 1],
  ],
};

export const TEMPLATES = [
  {
    id: "t-fx",
    name: "Conservative FX",
    note: "0.25% per trade, 1.5% daily, 6% max drawdown, news blackout",
  },
  {
    id: "t-mom",
    name: "Crypto momentum",
    note: "Volatility target, per-bot cap 20%, trailing portfolio stop",
  },
  {
    id: "t-neutral",
    name: "Market-neutral crypto",
    note: "Gross and net exposure caps, funding-cost limit",
  },
  {
    id: "t-prop",
    name: "Prop-firm challenge",
    note: "Hard 5% daily, 10% total, reduce at 60%, flatten at 80%",
  },
  {
    id: "t-parity",
    name: "Risk parity",
    note: "Equal risk per bot, monthly reweight, correlation alert at 0.7",
  },
  {
    id: "t-core",
    name: "Core and satellite",
    note: "80% steady bots, 20% high-variance with its own cap",
  },
  {
    id: "t-sandbox",
    name: "Paper sandbox",
    note: "Simulated capital, sanity caps only, report after N days",
  },
  {
    id: "t-recovery",
    name: "Drawdown recovery",
    note: "Halve size after 5% drawdown, restore at half recovered",
  },
  {
    id: "t-canary",
    name: "Single-venue canary",
    note: "Tiny live size for a new promotion, ramp on schedule",
  },
  {
    id: "t-model",
    name: "Model-sized book",
    note: "A model sizes trades; rules stay as hard limits (new scope)",
  },
];
