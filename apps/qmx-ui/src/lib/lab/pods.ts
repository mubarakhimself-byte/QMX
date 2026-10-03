/**
 * DEMO data for building and testing pods in the Lab (design 2026-10-03):
 * a pod is a stack of blocks in seven fixed slots (inputs, guards,
 * allocator, sizer, throttles, caps, ledger), then venue fit. Every trade
 * gets a size trail. The docs' Book + BMS is the "Classic Book" template.
 * Nothing here ran.
 */
import { equityWalk } from "$lib/qmx/charts";

export const SLOTS = [
  { id: "inputs", label: "Inputs", note: "What the pod looks at" },
  { id: "guards", label: "Guards", note: "Can stop everything" },
  { id: "allocator", label: "Allocator", note: "Splits capital between bots" },
  { id: "sizer", label: "Sizer", note: "Turns an entry into a size" },
  { id: "throttles", label: "Throttles", note: "Shrink size (×0 to ×1)" },
  { id: "caps", label: "Caps", note: "Hard limits" },
  { id: "ledger", label: "Ledger", note: "Capital, periods, fees" },
] as const;
export type SlotId = (typeof SLOTS)[number]["id"];

export type BlockKind = "form" | "graph" | "code" | "model";
export type Block = {
  id: string;
  name: string;
  slot: SlotId;
  kind: BlockKind;
  setting: string;
  what: string;
  docs: "yes" | "partial" | "new";
  required?: boolean;
};

export const BLOCKS: Block[] = [
  {
    id: "fixed-frac",
    name: "Fixed-fractional risk",
    slot: "sizer",
    kind: "form",
    setting: "0.5% to the stop",
    what: "Risk a share of equity per trade",
    docs: "yes",
  },
  {
    id: "fixed-usd",
    name: "Fixed notional",
    slot: "sizer",
    kind: "form",
    setting: "$100",
    what: "Same dollar amount every trade",
    docs: "new",
  },
  {
    id: "vol-target",
    name: "Volatility target",
    slot: "sizer",
    kind: "form",
    setting: "1% a day",
    what: "Size so each position moves a set share of equity",
    docs: "new",
  },
  {
    id: "kelly",
    name: "Quarter Kelly",
    slot: "sizer",
    kind: "form",
    setting: "¼, cap 2%",
    what: "From win rate and payoff; 0.5% until 100 trades",
    docs: "new",
  },
  {
    id: "model-sizer",
    name: "Model sizer",
    slot: "sizer",
    kind: "model",
    setting: "ceiling 1%",
    what: "A model picks ×0–1 under a rule ceiling",
    docs: "new",
  },
  {
    id: "equal",
    name: "Equal split",
    slot: "allocator",
    kind: "form",
    setting: "—",
    what: "Equal capital per bot",
    docs: "new",
  },
  {
    id: "parity",
    name: "Risk parity",
    slot: "allocator",
    kind: "form",
    setting: "monthly, 90 days",
    what: "Equal risk per bot",
    docs: "new",
  },
  {
    id: "tilt",
    name: "Performance tilt",
    slot: "allocator",
    kind: "form",
    setting: "±50%, quarterly",
    what: "Lean toward better bots (overfit warning)",
    docs: "new",
  },
  {
    id: "ladder",
    name: "Drawdown ladder",
    slot: "throttles",
    kind: "form",
    setting: "−5% ×0.5 · −10% ×0.25",
    what: "Shrink as drawdown deepens",
    docs: "partial",
  },
  {
    id: "regime",
    name: "Regime throttle",
    slot: "throttles",
    kind: "model",
    setting: "trend 1 · chop 0.5 · crash 0",
    what: "Multiplier per market regime",
    docs: "partial",
  },
  {
    id: "vol-spike",
    name: "Volatility spike",
    slot: "throttles",
    kind: "form",
    setting: "3× for 2h",
    what: "No entries when 1h vol jumps",
    docs: "new",
  },
  {
    id: "thin-hours",
    name: "Thin hours",
    slot: "throttles",
    kind: "form",
    setting: "weekends ×0.5",
    what: "Smaller size when books are thin",
    docs: "new",
  },
  {
    id: "streak",
    name: "Losing-streak bench",
    slot: "guards",
    kind: "form",
    setting: "4 losses",
    what: "Bench a bot until the next UTC day",
    docs: "yes",
  },
  {
    id: "cooldown",
    name: "Cooldown",
    slot: "guards",
    kind: "form",
    setting: "30 min",
    what: "No re-entry right after an exit",
    docs: "new",
  },
  {
    id: "kill",
    name: "Kill line",
    slot: "guards",
    kind: "form",
    setting: "−20%",
    what: "Floor: flatten and stand down",
    docs: "yes",
    required: true,
  },
  {
    id: "brakes",
    name: "Daily stop and health",
    slot: "guards",
    kind: "form",
    setting: "−3% · data 60s · peg $0.98",
    what: "Halt for the day, or on bad data or a depeg",
    docs: "partial",
  },
  {
    id: "news-kill",
    name: "News-aware kill switch",
    slot: "guards",
    kind: "graph",
    setting: "high-impact ±30 min",
    what: "Your graph: halt around big events",
    docs: "new",
  },
  {
    id: "caps",
    name: "Exposure caps",
    slot: "caps",
    kind: "form",
    setting: "25% coin · 8 positions",
    what: "Per coin, gross, open positions",
    docs: "yes",
  },
  {
    id: "corr-cap",
    name: "Correlation cap",
    slot: "caps",
    kind: "form",
    setting: "40% per cluster",
    what: "Coins moving together share one cap",
    docs: "partial",
  },
  {
    id: "liq-cap",
    name: "Liquidity cap",
    slot: "caps",
    kind: "form",
    setting: "1% of 1h volume",
    what: "Never be the market",
    docs: "new",
  },
  {
    id: "venue-cap",
    name: "Exchange and stablecoin cap",
    slot: "caps",
    kind: "form",
    setting: "60% · 50%",
    what: "Limit per exchange and per stablecoin",
    docs: "new",
  },
  {
    id: "vol-input",
    name: "Volatility (30d EWMA)",
    slot: "inputs",
    kind: "form",
    setting: "30 days",
    what: "Feeds sizers and throttles",
    docs: "new",
  },
  {
    id: "regime-input",
    name: "Regime label",
    slot: "inputs",
    kind: "model",
    setting: "Regime HMM v1",
    what: "From MIS or a Lab model",
    docs: "partial",
  },
  {
    id: "peg-input",
    name: "Stablecoin peg",
    slot: "inputs",
    kind: "form",
    setting: "USDT, USDC",
    what: "Watches the cash you hold",
    docs: "new",
  },
  {
    id: "ledger-usd",
    name: "Daily UTC ledger",
    slot: "ledger",
    kind: "form",
    setting: "USD, fees on",
    what: "Capital, periods and fees",
    docs: "partial",
  },
];
export const blockById = (id: string) => BLOCKS.find((b) => b.id === id);

export type LabPod = {
  id: string;
  name: string;
  version: string;
  template: string;
  color: string;
  /** Where this version is on its way to money. */
  stage: "draft" | "tested" | "paper" | "live";
  stack: Record<SlotId, string[]>;
};

export const LAB_PODS: LabPod[] = [
  {
    id: "classic",
    name: "Classic Book",
    version: "v3",
    template: "Classic Book (Book + BMS)",
    color: "var(--muted-foreground)",
    stage: "live",
    stack: {
      inputs: [],
      guards: ["kill", "streak", "brakes"],
      allocator: [],
      sizer: ["fixed-frac"],
      throttles: [],
      caps: ["caps"],
      ledger: ["ledger-usd"],
    },
  },
  {
    id: "trend",
    name: "Trend rider",
    version: "v2",
    template: "Trend rider",
    color: "var(--chart-2)",
    stage: "paper",
    stack: {
      inputs: ["regime-input", "vol-input"],
      guards: ["kill", "brakes", "news-kill"],
      allocator: ["equal"],
      sizer: ["fixed-frac"],
      throttles: ["regime", "vol-spike"],
      caps: ["caps", "corr-cap"],
      ledger: ["ledger-usd"],
    },
  },
  {
    id: "voltarget",
    name: "Vol-targeted core",
    version: "v1",
    template: "Vol-targeted core",
    color: "var(--chart-4)",
    stage: "paper",
    stack: {
      inputs: ["vol-input", "peg-input"],
      guards: ["kill", "brakes"],
      allocator: ["parity"],
      sizer: ["vol-target"],
      throttles: ["ladder", "thin-hours"],
      caps: ["caps", "corr-cap", "venue-cap"],
      ledger: ["ledger-usd"],
    },
  },
];

export const POD_TEMPLATES = [
  {
    id: "starter",
    name: "Paper starter",
    note: "$50 a trade, equal split. For learning.",
  },
  {
    id: "classic",
    name: "Classic Book",
    note: "The docs' Book + BMS. Baseline in every comparison.",
  },
  {
    id: "voltarget",
    name: "Vol-targeted core",
    note: "Volatility target, risk parity, drawdown ladder.",
  },
  {
    id: "trend",
    name: "Trend rider",
    note: "0.75% risk, regime and spike throttles.",
  },
  {
    id: "scalper",
    name: "Alt scalper",
    note: "0.25% risk, liquidity cap, cooldown, thin hours.",
  },
  {
    id: "kelly",
    name: "Kelly-lite growth",
    note: "Quarter Kelly with a performance tilt, kill at −15%.",
  },
  {
    id: "parity",
    name: "Risk-parity multi-bot",
    note: "Equal risk per bot, correlation cap.",
  },
  {
    id: "guard",
    name: "Capital guard",
    note: "0.3% risk, daily −2%, kill at −8%.",
  },
  {
    id: "canary",
    name: "Canary",
    note: "$25, one position, kill at −5%. First live week.",
  },
  {
    id: "model",
    name: "Model-sized hybrid",
    note: "A model sizes under a 1% ceiling; rules bound it.",
  },
];

/** One trade, step by step through the pod. */
export const SIZE_TRAIL = [
  { step: "Sizer · 0.5% risk to the stop", usd: 1240 },
  { step: "Drawdown ladder ×0.5", usd: 620 },
  { step: "Thin hours ×0.5", usd: 310 },
  { step: "Caps · within limits", usd: 310 },
  { step: "Venue fit · 0.00483 BTC, fee $0.31", usd: 309.8 },
];

/** Drawdown percentiles over 90 days for each pod (from 1,000 paths). */
export const FAN: Record<
  string,
  { p5: number[]; p50: number[]; p95: number[]; pKill: number }
> = Object.fromEntries(
  LAB_PODS.map((p, i) => {
    const n = 60;
    const depth = [0.22, 0.14, 0.1][i];
    const p50 = Array.from(
      { length: n },
      (_, k) => -depth * 0.45 * Math.sqrt(k / n) * 100,
    );
    const p95 = Array.from(
      { length: n },
      (_, k) => -depth * Math.sqrt(k / n) * 100,
    );
    const p5 = Array.from(
      { length: n },
      (_, k) => -depth * 0.12 * Math.sqrt(k / n) * 100,
    );
    return [p.id, { p5, p50, p95, pKill: [7.4, 2.1, 0.6][i] }];
  }),
);

export const STRESS = [
  { id: "flash", name: "Flash crash −30% in 15 min" },
  { id: "outage", name: "Exchange outage 2h" },
  { id: "depeg", name: "Stablecoin depeg to $0.87" },
  { id: "weekend", name: "Weekend thin book" },
  { id: "ftx", name: "Nov 2022 (FTX) replay" },
  { id: "bear", name: "Slow bear −70% over a year" },
];
export type StressCell = {
  loss: number;
  ofRoom: number;
  fired: string;
  stoodDown: boolean;
};
export const STRESS_GRID: Record<string, Record<string, StressCell>> = {
  classic: {
    flash: {
      loss: -2840,
      ofRoom: 0.71,
      fired: "Daily stop after 9 min",
      stoodDown: false,
    },
    outage: {
      loss: -620,
      ofRoom: 0.16,
      fired: "Health brake (data stale)",
      stoodDown: false,
    },
    depeg: { loss: -1900, ofRoom: 0.48, fired: "Nothing", stoodDown: false },
    weekend: { loss: -310, ofRoom: 0.08, fired: "Nothing", stoodDown: false },
    ftx: { loss: -4100, ofRoom: 1, fired: "Kill line", stoodDown: true },
    bear: {
      loss: -3600,
      ofRoom: 0.9,
      fired: "Daily stop ×6",
      stoodDown: false,
    },
  },
  trend: {
    flash: {
      loss: -1460,
      ofRoom: 0.37,
      fired: "Vol spike in 2 min",
      stoodDown: false,
    },
    outage: {
      loss: -540,
      ofRoom: 0.14,
      fired: "Health brake",
      stoodDown: false,
    },
    depeg: { loss: -1700, ofRoom: 0.43, fired: "Nothing", stoodDown: false },
    weekend: { loss: -260, ofRoom: 0.07, fired: "Nothing", stoodDown: false },
    ftx: {
      loss: -2200,
      ofRoom: 0.55,
      fired: "Regime → crash ×0",
      stoodDown: false,
    },
    bear: {
      loss: -2100,
      ofRoom: 0.52,
      fired: "Regime throttle",
      stoodDown: false,
    },
  },
  voltarget: {
    flash: { loss: -980, ofRoom: 0.25, fired: "Ladder ×0.5", stoodDown: false },
    outage: {
      loss: -410,
      ofRoom: 0.1,
      fired: "Health brake",
      stoodDown: false,
    },
    depeg: {
      loss: -520,
      ofRoom: 0.13,
      fired: "Peg brake → move to USDC",
      stoodDown: false,
    },
    weekend: {
      loss: -120,
      ofRoom: 0.03,
      fired: "Thin hours ×0.5",
      stoodDown: false,
    },
    ftx: { loss: -1500, ofRoom: 0.38, fired: "Ladder ×0.25", stoodDown: false },
    bear: { loss: -1600, ofRoom: 0.4, fired: "Ladder ×0.25", stoodDown: false },
  },
};

export const INTERVENTIONS = [
  {
    time: "Mar 12 2024 09:14",
    pod: "Vol-targeted core",
    what: "Shrunk ×0.5",
    by: "Drawdown ladder at −5.2%",
  },
  {
    time: "Mar 12 2024 09:02",
    pod: "Trend rider",
    what: "Refused SOL entry",
    by: "Volatility spike (3.4×)",
  },
  {
    time: "Nov 09 2022 02:40",
    pod: "Classic Book",
    what: "Stood down",
    by: "Kill line",
  },
  {
    time: "Nov 09 2022 01:15",
    pod: "Trend rider",
    what: "Halted new entries",
    by: "Regime turned crash",
  },
  {
    time: "Aug 17 2024 22:00",
    pod: "Vol-targeted core",
    what: "Shrunk ×0.5",
    by: "Thin hours (weekend)",
  },
];

export const POD_EQUITY: Record<string, number[]> = {
  // Seeds picked so each curve's deepest dip and gain match Head to head.
  classic: equityWalk(8, 120, 0.0035, 0.035),
  trend: equityWalk(4, 120, 0.0015, 0.03),
  voltarget: equityWalk(1, 120, 0.0015, 0.03),
};

export const STAGE_LABEL: Record<LabPod["stage"], string> = {
  draft: "Draft",
  tested: "Tested",
  paper: "On paper",
  live: "Live",
};

/** Bots a pod test can run over (published versions from the Library). */
export const TEST_BOTS = [
  { id: "btc-breakout", name: "BTC breakout", symbol: "BTCUSDT" },
  { id: "eth-trend", name: "ETH trend", symbol: "ETHUSDT" },
  { id: "sol-mom", name: "SOL momentum", symbol: "SOLUSDT" },
  { id: "avax-mom", name: "AVAX momentum", symbol: "AVAXUSDT" },
  { id: "eth-mr", name: "ETH mean reversion", symbol: "ETHUSDT" },
  { id: "rotator", name: "Top-5 rotator", symbol: "Basket" },
];

/** Paper money a pod can soak on before it touches real money. */
export const PAPER_MONEY = [
  {
    id: "bn-test",
    name: "Binance testnet",
    note: "The exchange's own test market",
    balance: 25000,
  },
  {
    id: "by-test",
    name: "Bybit testnet",
    note: "The exchange's own test market",
    balance: 10000,
  },
  {
    id: "ledger",
    name: "Node paper ledger",
    note: "Any exchange; fills simulated on live prices",
    balance: 20000,
  },
];

/** Head to head: each pod's measures as numbers, and which way is better. */
export type PodAttr = {
  id: string;
  label: string;
  note: string;
  better: "high" | "low" | "none";
  unit: "usd" | "pct";
  values: Record<string, number>;
  /** Differences smaller than this are inside the Monte Carlo noise. */
  noise: number;
};
export const POD_ATTRS: PodAttr[] = [
  {
    id: "profit",
    label: "Profit",
    note: "Net on $20,000, after fees",
    better: "high",
    unit: "usd",
    values: { classic: 6440, trend: 5340, voltarget: 4400 },
    noise: 400,
  },
  {
    id: "dip",
    label: "Deepest dip",
    note: "Largest fall from a high",
    better: "low",
    unit: "pct",
    values: { classic: -24, trend: -15, voltarget: -10 },
    noise: 2,
  },
  {
    id: "crash",
    label: "Worst crash",
    note: "Worst loss on the stress board",
    better: "low",
    unit: "usd",
    values: { classic: -4100, trend: -2200, voltarget: -1600 },
    noise: 300,
  },
  {
    id: "kill",
    label: "Kill-line risk",
    note: "Chance of hitting it in 90 days",
    better: "low",
    unit: "pct",
    values: { classic: 7.4, trend: 2.1, voltarget: 0.6 },
    noise: 1,
  },
  {
    id: "luck",
    label: "Luck share",
    note: "Profit that came from the top 5 trades",
    better: "low",
    unit: "pct",
    values: { classic: 41, trend: 33, voltarget: 24 },
    noise: 5,
  },
  {
    id: "steps",
    label: "Steps in",
    note: "Trades it shrank or refused",
    better: "none",
    unit: "pct",
    values: { classic: 3, trend: 18, voltarget: 26 },
    noise: 0,
  },
];

/** A pod version soaking on paper: the Lab watches it against its own test. */
export type PaperRun = {
  pod: string;
  version: string;
  money: string;
  server: string;
  day: number;
  of: number;
  started: string;
  /** Paper equity so far, and the band its test said to expect. */
  equity: number[];
  p5: number[];
  p95: number[];
  verdict: "as-tested" | "drifting" | "ready";
  checks: { label: string; done: boolean; note: string }[];
};

function band(seed: number, n: number, drift: number, width: number) {
  const mid = equityWalk(seed, n, drift, 0.003);
  return {
    p5: mid.map((v, i) => v * (1 - width * Math.sqrt((i + 1) / n))),
    p95: mid.map((v, i) => v * (1 + width * Math.sqrt((i + 1) / n))),
  };
}

export const PAPER_RUNS: PaperRun[] = [
  {
    pod: "trend",
    version: "v2",
    money: "Binance testnet",
    server: "This laptop",
    day: 4,
    of: 7,
    started: "Sep 29",
    equity: equityWalk(311, 32, 0.0012, 0.004),
    ...band(311, 56, 0.0012, 0.03),
    verdict: "as-tested",
    checks: [
      { label: "Soak time", done: false, note: "Day 4 of 7" },
      { label: "Inside the tested band", done: true, note: "Every day so far" },
      {
        label: "Kill line kept its distance",
        done: true,
        note: "Closest: 71% of room left",
      },
      {
        label: "Every fill matched the exchange",
        done: true,
        note: "112 of 112",
      },
      { label: "No unknown positions", done: true, note: "None" },
    ],
  },
  {
    pod: "voltarget",
    version: "v1",
    money: "Bybit testnet",
    server: "Tokyo",
    day: 9,
    of: 7,
    started: "Sep 24",
    equity: equityWalk(322, 56, 0.0011, 0.003),
    ...band(322, 56, 0.0011, 0.025),
    verdict: "ready",
    checks: [
      { label: "Soak time", done: true, note: "9 of 7 days" },
      { label: "Inside the tested band", done: true, note: "Every day" },
      {
        label: "Kill line kept its distance",
        done: true,
        note: "Closest: 88% of room left",
      },
      {
        label: "Every fill matched the exchange",
        done: true,
        note: "204 of 204",
      },
      { label: "No unknown positions", done: true, note: "None" },
    ],
  },
];

/** Decisions arriving from a paper run: each trade with the steps that sized it. */
export type PaperDecision = {
  at: string;
  bot: string;
  side: "Buy" | "Sell";
  symbol: string;
  steps: { by: string; usd: number }[];
  refused?: string;
};
export const PAPER_FEED: PaperDecision[] = [
  {
    at: "10:41",
    bot: "SOL momentum",
    side: "Buy",
    symbol: "SOLUSDT",
    steps: [
      { by: "Sizer 0.75%", usd: 860 },
      { by: "Regime ×1", usd: 860 },
      { by: "Caps", usd: 860 },
    ],
  },
  {
    at: "10:12",
    bot: "AVAX momentum",
    side: "Buy",
    symbol: "AVAXUSDT",
    steps: [{ by: "Sizer 0.75%", usd: 640 }],
    refused: "Volatility spike 3.1×",
  },
  {
    at: "09:55",
    bot: "BTC breakout",
    side: "Buy",
    symbol: "BTCUSDT",
    steps: [
      { by: "Sizer 0.75%", usd: 1240 },
      { by: "Correlation cap ×0.6", usd: 744 },
      { by: "Venue fit", usd: 743.6 },
    ],
  },
  {
    at: "09:20",
    bot: "ETH trend",
    side: "Sell",
    symbol: "ETHUSDT",
    steps: [{ by: "Exit at target", usd: 910 }],
  },
];

/** Stress scenarios you made yourself (here, one drafted with the copilot). */
export const MY_STRESS = [
  {
    id: "mine-1",
    name: "BTC −15% while Binance pauses withdrawals",
    by: "You, with the copilot",
  },
];

/** Today's interventions from the pods on paper. */
export const PAPER_INTERVENTIONS = [
  {
    time: "Today 10:12",
    pod: "Trend rider",
    what: "Refused AVAX entry",
    by: "Volatility spike (3.1×)",
  },
  {
    time: "Today 09:55",
    pod: "Trend rider",
    what: "Shrunk ×0.6",
    by: "Correlation cap (BTC with ETH open)",
  },
  {
    time: "Today 03:00",
    pod: "Vol-targeted core",
    what: "Shrunk ×0.5",
    by: "Thin hours",
  },
  {
    time: "Yesterday 21:40",
    pod: "Vol-targeted core",
    what: "Shrunk ×0.75",
    by: "Drawdown ladder at −3.1%",
  },
];
