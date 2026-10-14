/**
 * DEMO data for the Lab. Shapes follow the docs where they exist (QMB runs
 * and run roles, CT-46 execution environments, CT-12 splits) and are marked
 * "new scope" where the operator's vision runs ahead of them (model objects,
 * model slots, external GPU providers). Nothing here is evidence.
 */
import { equityWalk, seeded } from "$lib/qmx/charts";

export type EnvKind = "local" | "remote_host" | "remote_container";
export type Environment = {
  id: string;
  name: string;
  where: string;
  kind: EnvKind;
  hardware: string;
  status: "ready" | "busy" | "offline";
  /** Concurrent run slots the governor allows, and how many are used. */
  slots: [used: number, total: number];
  cost?: string;
  /** B-9: only the controlled machine sees sealed or governed data. */
  evidence: boolean;
};

export const ENVIRONMENTS: Environment[] = [
  {
    id: "local",
    name: "This laptop",
    where: "Dell Precision 5550",
    kind: "local",
    hardware: "6 cores · 32 GB · Quadro T2000",
    status: "busy",
    slots: [3, 6],
    evidence: true,
  },
  {
    id: "vps-fsn",
    name: "Research VPS",
    where: "Hetzner, Falkenstein",
    kind: "remote_host",
    hardware: "16 vCPU · 64 GB",
    status: "busy",
    slots: [5, 12],
    cost: "$0.09/h",
    evidence: false,
  },
  {
    id: "colab",
    name: "Colab",
    where: "Google Colab Pro",
    kind: "remote_container",
    hardware: "T4 GPU · 15 GB",
    status: "busy",
    slots: [1, 1],
    cost: "1.8 units/h",
    evidence: false,
  },
  {
    id: "aws",
    name: "AWS GPU",
    where: "eu-west-2 · g5.xlarge",
    kind: "remote_container",
    hardware: "A10G GPU · 24 GB",
    status: "offline",
    slots: [0, 4],
    cost: "$1.01/h",
    evidence: false,
  },
];

export const envById = (id: string) => ENVIRONMENTS.find((e) => e.id === id);

/** Where data and artifacts are kept besides this laptop (new scope). */
export const STORAGE = [
  {
    id: "disk",
    name: "This laptop",
    where: "C: drive",
    used: "412 GB free of 1 TB",
    status: "ready",
  },
  {
    id: "b2",
    name: "Research data",
    where: "Backblaze B2 bucket",
    used: "38 GB · $0.23/month",
    status: "ready",
  },
  {
    id: "s3",
    name: "Model store",
    where: "AWS S3 bucket",
    used: "Not connected",
    status: "offline",
  },
] as const;

/**
 * How much work a machine has for a layout kind. Drafts are edited on this
 * laptop; tests and comparisons are runs; training is the training job.
 * The daemon reports this per environment once wired.
 */
export function activity(env: string, layout: string): number {
  const runsHere = RUNS.filter(
    (r) => r.env === env && r.procedure !== "Training",
  );
  switch (layout) {
    case "build":
      return env === "local" ? 1 : 0;
    case "test":
      return runsHere.length;
    case "train":
      return RUNS.filter((r) => r.env === env && r.procedure === "Training")
        .length;
    case "compare":
      return runsHere.filter((r) => r.status === "done").length;
    // Pods: drafts live on this laptop, pod tests queue like runs, and the
    // paper runs the Lab watches sit on whichever server trades them.
    case "pod-design":
      return env === "local" ? 3 : 0;
    case "pod-test":
      return ({ local: 1, "vps-fsn": 2 } as Record<string, number>)[env] ?? 0;
    case "pod-paper":
      return env === "local" ? 1 : 0;
    default:
      return RUNS.filter((r) => r.env === env).length;
  }
}

export const SYMBOLS = [
  "XAUUSD",
  "NAS100",
  "EURUSD",
  "USOIL",
  "BTCUSDT",
  "ETHUSDT",
];
export const TIMEFRAMES = ["M15", "H1", "H4"];

export type RunStatus =
  "queued" | "running" | "done" | "failed" | "aborted" | "unknown";
export type Run = {
  id: string;
  procedure:
    | "Backtest"
    | "Sweep"
    | "Walk-forward"
    | "Monte Carlo"
    | "Optimise"
    | "Significance"
    | "Training";
  symbol: string;
  timeframe: string;
  role: "confirmation" | "trial" | "replicate" | "aborted";
  status: RunStatus;
  env: string;
  /** Percent. */
  net: number | null;
  /** Percent, negative. */
  maxDd: number | null;
  sharpe: number | null;
  trades: number;
  progress?: number;
  equity: number[];
  changed?: string[];
};

function sweep(): Run[] {
  const r = seeded(77);
  const out: Run[] = [];
  let n = 500;
  for (const tf of TIMEFRAMES) {
    for (const s of SYMBOLS) {
      n++;
      const edge =
        (s.startsWith("BTC") || s === "XAUUSD" ? 0.0012 : 0.0002) +
        (tf === "H1" ? 0.0006 : 0) +
        (r() - 0.5) * 0.0018;
      const status: RunStatus =
        s === "EURUSD" && tf === "H4"
          ? "running"
          : s === "USOIL" && tf === "M15"
            ? "failed"
            : s === "NAS100" && tf === "H4"
              ? "queued"
              : "done";
      const eq =
        status === "done"
          ? equityWalk(n, 120, edge, 0.01)
          : status === "running"
            ? equityWalk(n, 64, edge, 0.01)
            : [];
      const last = eq.at(-1) ?? 100;
      let peak = 100;
      let dd = 0;
      for (const v of eq) {
        peak = Math.max(peak, v);
        dd = Math.min(dd, (v / peak - 1) * 100);
      }
      out.push({
        id: `run-${n}`,
        procedure: "Sweep",
        symbol: s,
        timeframe: tf,
        role: "trial",
        status,
        env: n % 3 === 0 ? "local" : "vps-fsn",
        net: status === "done" ? +(last - 100).toFixed(1) : null,
        maxDd: status === "done" ? +dd.toFixed(1) : null,
        sharpe:
          status === "done"
            ? +(edge * 900 + (r() - 0.5) * 0.3).toFixed(2)
            : null,
        trades: status === "done" ? Math.round(80 + r() * 260) : 0,
        progress: status === "running" ? 53 : undefined,
        equity: eq,
        changed: ["symbol", "timeframe"],
      });
    }
  }
  return out;
}

export const RUNS: Run[] = [
  {
    id: "run-441",
    procedure: "Walk-forward",
    symbol: "BTCUSDT",
    timeframe: "H1",
    role: "confirmation",
    status: "done",
    env: "local",
    net: 18.4,
    maxDd: -6.8,
    sharpe: 1.42,
    trades: 187,
    equity: equityWalk(441, 120, 0.0016, 0.009),
  },
  {
    id: "run-442",
    procedure: "Monte Carlo",
    symbol: "BTCUSDT",
    timeframe: "H1",
    role: "replicate",
    status: "running",
    env: "vps-fsn",
    net: null,
    maxDd: null,
    sharpe: null,
    trades: 187,
    progress: 61,
    equity: equityWalk(442, 70, 0.0014, 0.01),
  },
  {
    id: "run-443",
    procedure: "Training",
    symbol: "BTCUSDT",
    timeframe: "H1",
    role: "trial",
    status: "running",
    env: "colab",
    net: null,
    maxDd: null,
    sharpe: null,
    trades: 0,
    progress: 35,
    equity: [],
  },
  ...sweep(),
];

export type AssetKind =
  | "template"
  | "bot"
  | "model"
  | "dataset"
  | "feature"
  | "test"
  | "preset"
  | "report";

export const ASSET_GROUPS: {
  kind: AssetKind;
  label: string;
  add: string;
  scope?: "new";
}[] = [
  { kind: "template", label: "Workflows", add: "New workflow" },
  { kind: "bot", label: "Bots", add: "New bot" },
  { kind: "model", label: "Models", add: "Import model", scope: "new" },
  { kind: "dataset", label: "Datasets", add: "Add dataset" },
  { kind: "feature", label: "Features", add: "New feature" },
  { kind: "test", label: "Saved tests", add: "Save a test", scope: "new" },
  { kind: "preset", label: "Presets", add: "New preset" },
  { kind: "report", label: "Reports", add: "New report", scope: "new" },
];

export type Asset = {
  id: string;
  kind: AssetKind;
  name: string;
  meta: string;
  env?: string;
};

export const ASSETS: Asset[] = [
  {
    id: "wf-breakout",
    kind: "template",
    name: "Breakout research",
    meta: "8 steps · v7 draft",
  },
  {
    id: "wf-nightly",
    kind: "template",
    name: "Nightly evidence",
    meta: "5 steps · published v3",
  },
  {
    id: "wf-regime",
    kind: "template",
    name: "Regime study",
    meta: "6 steps · v1 draft",
  },
  {
    id: "bot-gbm",
    kind: "bot",
    name: "BTC breakout",
    meta: "v7 · research-paper",
  },
  { id: "bot-trend", kind: "bot", name: "ETH trend", meta: "v12 · live" },
  { id: "bot-fade", kind: "bot", name: "Gold scalper", meta: "v4 · live" },
  {
    id: "m-scorer",
    kind: "model",
    name: "Breakout scorer",
    meta: "GBM · AUC 0.61",
    env: "local",
  },
  {
    id: "m-hmm",
    kind: "model",
    name: "Market regime HMM",
    meta: "3 regimes",
    env: "vps-fsn",
  },
  {
    id: "m-lstm",
    kind: "model",
    name: "Vol forecaster",
    meta: "ONNX · imported",
    env: "colab",
  },
  {
    id: "d-fx",
    kind: "dataset",
    name: "IC Markets CFDs 1m 2019–2026",
    meta: "cTrader history · FX, indices, metals, energy · 52 GB",
  },
  {
    id: "d-crypto",
    kind: "dataset",
    name: "Binance spot 1m 2019–2026",
    meta: "Binance public data · 38 GB",
  },
  {
    id: "d-news",
    kind: "dataset",
    name: "Calendar events",
    meta: "Forex Factory + market news · daily",
  },
  {
    id: "d-csv",
    kind: "dataset",
    name: "Broker fills export",
    meta: "CSV upload · 4 MB",
  },
  { id: "f-atr", kind: "feature", name: "ATR(14) ratio", meta: "Indicator" },
  { id: "f-sess", kind: "feature", name: "Session flags", meta: "Structure" },
  {
    id: "f-sent",
    kind: "feature",
    name: "News sentiment",
    meta: "Model output",
  },
  {
    id: "t-mc",
    kind: "test",
    name: "Monte Carlo 1,000 shuffles",
    meta: "Robustness",
  },
  {
    id: "t-wf",
    kind: "test",
    name: "Walk-forward 12 folds",
    meta: "Embargo 24 bars",
  },
  { id: "t-stress", kind: "test", name: "Spread ×2 stress", meta: "What-if" },
  { id: "p-spread", kind: "preset", name: "Stress spread", meta: "Costs" },
  {
    id: "p-london",
    kind: "preset",
    name: "London session only",
    meta: "Filter",
  },
  {
    id: "r-weekly",
    kind: "report",
    name: "Weekly evidence pack",
    meta: "PDF + charts",
  },
];

export type AgentNode = {
  id: string;
  name: string;
  role: string;
  task: string;
  status: RunStatus;
  env: string;
  children?: AgentNode[];
};

export const AGENTS: AgentNode[] = [
  {
    id: "q-research",
    name: "Researcher",
    role: "Quant · research desk",
    task: "Scanning articles for exit ideas",
    status: "running",
    env: "vps-fsn",
    children: [
      {
        id: "s-1",
        name: "Reader 1",
        role: "Subagent",
        task: "MQL5 trailing-stop articles",
        status: "running",
        env: "vps-fsn",
      },
      {
        id: "s-2",
        name: "Reader 2",
        role: "Subagent",
        task: "arXiv q-fin exits",
        status: "running",
        env: "vps-fsn",
      },
      {
        id: "s-3",
        name: "Reader 3",
        role: "Subagent",
        task: "SSRN volatility stops",
        status: "done",
        env: "vps-fsn",
      },
      {
        id: "s-4",
        name: "Summariser",
        role: "Subagent",
        task: "Waiting for readers",
        status: "queued",
        env: "local",
      },
    ],
  },
  {
    id: "q-analyst",
    name: "Analyst",
    role: "Quant · analysis desk",
    task: "Coordinating the 18-run sweep",
    status: "running",
    env: "local",
    children: [
      {
        id: "s-5",
        name: "Checker",
        role: "Subagent",
        task: "Lost contact mid-check",
        status: "unknown",
        env: "colab",
      },
    ],
  },
];

export const TRAINING = {
  model: "Breakout scorer",
  kind: "Gradient-boosted trees",
  env: "colab",
  epoch: 14,
  epochs: 40,
  train: Array.from({ length: 14 }, (_, i) => 0.69 * Math.exp(-i / 9) + 0.18),
  valid: Array.from(
    { length: 14 },
    (_, i) => 0.69 * Math.exp(-i / 10) + 0.24 + (i > 10 ? (i - 10) * 0.004 : 0),
  ),
  split: {
    train: "2015–2022",
    validation: "2023–2024",
    sealed: "2025 (sealed)",
  },
  purge: "24 bars",
  embargo: "24 bars",
};

export type Slot = {
  id: string;
  label: string;
  model: string | null;
  owner: string;
  scope: "docs" | "new";
};

export const SLOTS: Slot[] = [
  {
    id: "entry",
    label: "Entry signal",
    model: "Breakout scorer",
    owner: "Inside the bot's code",
    scope: "docs",
  },
  {
    id: "sizing",
    label: "Position sizing",
    model: null,
    owner: "The pod decides today",
    scope: "new",
  },
  {
    id: "regime",
    label: "Regime",
    model: "Market regime HMM",
    owner: "Node labeler today",
    scope: "new",
  },
  {
    id: "throttle",
    label: "Risk throttle",
    model: null,
    owner: "Kill switch today",
    scope: "new",
  },
];
