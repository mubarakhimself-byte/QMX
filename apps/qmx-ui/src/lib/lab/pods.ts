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
  stack: Record<SlotId, string[]>;
};

export const LAB_PODS: LabPod[] = [
  {
    id: "classic",
    name: "Classic Book",
    version: "v3",
    template: "Classic Book (Book + BMS)",
    color: "var(--muted-foreground)",
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

/** Measures per pod for the comparison grid: raw numbers, no total score. */
export const POD_MEASURES: {
  group: string;
  label: string;
  values: Record<string, string>;
  best?: string;
}[] = [
  {
    group: "Return",
    label: "Net (USD)",
    values: { classic: "+$6,420", trend: "+$5,880", voltarget: "+$4,910" },
    best: "classic",
  },
  {
    group: "Return",
    label: "Return ÷ max drawdown",
    values: { classic: "1.1", trend: "1.6", voltarget: "2.0" },
    best: "voltarget",
  },
  {
    group: "Pain",
    label: "Max drawdown",
    values: { classic: "−24%", trend: "−15%", voltarget: "−10%" },
    best: "voltarget",
  },
  {
    group: "Pain",
    label: "Worst week",
    values: { classic: "−9.8%", trend: "−6.1%", voltarget: "−4.4%" },
    best: "voltarget",
  },
  {
    group: "Tail",
    label: "Chance of hitting the kill line (90 days)",
    values: { classic: "7.4%", trend: "2.1%", voltarget: "0.6%" },
    best: "voltarget",
  },
  {
    group: "Tail",
    label: "Worst stress loss",
    values: { classic: "−$4,100", trend: "−$2,200", voltarget: "−$1,600" },
    best: "voltarget",
  },
  {
    group: "Behaviour",
    label: "Trades shrunk or refused",
    values: { classic: "3%", trend: "18%", voltarget: "26%" },
  },
  {
    group: "Behaviour",
    label: "Time halted",
    values: { classic: "1.2%", trend: "4.0%", voltarget: "0.8%" },
  },
  {
    group: "Fragility",
    label: "Profit from top 5 trades",
    values: { classic: "41%", trend: "33%", voltarget: "24%" },
    best: "voltarget",
  },
];

export const POD_EQUITY: Record<string, number[]> = {
  classic: equityWalk(201, 120, 0.0015, 0.014),
  trend: equityWalk(202, 120, 0.0014, 0.01),
  voltarget: equityWalk(203, 120, 0.0012, 0.007),
};

export const ALLOCATION = [
  { pod: "Classic Book", now: 40, proposed: 25, band: [18, 33] },
  { pod: "Trend rider", now: 35, proposed: 35, band: [28, 41] },
  { pod: "Vol-targeted core", now: 25, proposed: 40, band: [35, 46] },
];
