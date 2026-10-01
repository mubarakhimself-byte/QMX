/**
 * DEMO ENTITIES AND ARTIFACTS ONLY: sample bots, ML models, mini apps and
 * workflows for design review. Numbers are invented; nothing here is
 * evidence.
 */
import type {
  Entity,
  EvidenceRun,
  JournalEntry,
  Measure,
} from "$lib/qmx/entities";

function walk(seed: number, drift: number, n = 60): number[] {
  let s = seed;
  let v = 100;
  return Array.from({ length: n }, () => {
    s = (s * 9301 + 49297) % 233280;
    v *= 1 + (s / 233280 - 0.5 + drift) * 0.03;
    return v;
  });
}

const M = {
  sharpe: (v: string): Measure => ({
    key: "sharpe",
    label: "Sharpe",
    value: v,
    help: "Return per unit of volatility, annualised. Above 1 is good.",
  }),
  dd: (v: string): Measure => ({
    key: "dd",
    label: "Max drawdown",
    value: v,
    help: "Largest fall from a peak before recovering.",
    tone: "down",
  }),
  win: (v: string): Measure => ({
    key: "win",
    label: "Win rate",
    value: v,
    help: "Share of trades that closed in profit.",
  }),
  ret: (v: string, up = true): Measure => ({
    key: "ret",
    label: "Net return",
    value: v,
    help: "Total return after costs over the evidence period.",
    tone: up ? "up" : "down",
  }),
  trades: (v: string): Measure => ({
    key: "trades",
    label: "Trades",
    value: v,
    help: "Closed trades in the evidence period.",
  }),
  r: (v: string): Measure => ({
    key: "r",
    label: "Avg R",
    value: v,
    help: "Average result per trade as a multiple of the risk taken.",
  }),
};

function runs(seed: number): EvidenceRun[] {
  return [
    {
      run: `run-${seed}41`,
      kind: "Walk-forward",
      role: "confirmation",
      period: "2024-01 → 2026-09",
      sharpe: "1.42",
      maxDrawdown: "−6.8%",
      trades: 187,
      when: "Today 12:10",
    },
    {
      run: `run-${seed}38`,
      kind: "Monte Carlo",
      role: "replicate",
      period: "1,000 shuffles",
      sharpe: "1.18 (p5)",
      maxDrawdown: "−11.2% (p95)",
      trades: 187,
      when: "Today 12:04",
    },
    {
      run: `run-${seed}31`,
      kind: "Optimise",
      role: "trial",
      period: "2019-01 → 2023-12",
      sharpe: "1.61",
      maxDrawdown: "−5.9%",
      trades: 412,
      when: "Yesterday",
    },
    {
      run: `run-${seed}22`,
      kind: "Significance",
      role: "confirmation",
      period: "vs zero-edge null",
      sharpe: "p = 0.012",
      maxDrawdown: "—",
      trades: 187,
      when: "Sep 29",
    },
    {
      run: `run-${seed}10`,
      kind: "Backtest",
      role: "trial",
      period: "2019-01 → 2026-09",
      sharpe: "1.27",
      maxDrawdown: "−8.4%",
      trades: 598,
      when: "Sep 27",
    },
  ];
}

const JOURNAL: JournalEntry[] = [
  {
    time: "Sep 30 14:02",
    symbol: "US500",
    side: "Buy",
    lots: 0.2,
    entry: "5498.2",
    exit: "5531.6",
    pnl: 66.8,
    note: "Trend resumed after London open",
  },
  {
    time: "Sep 29 09:15",
    symbol: "US500",
    side: "Buy",
    lots: 0.2,
    entry: "5512.0",
    exit: "5489.5",
    pnl: -45.0,
    note: "Stopped out on CPI spike",
  },
  {
    time: "Sep 26 16:40",
    symbol: "US500",
    side: "Sell",
    lots: 0.2,
    entry: "5541.3",
    exit: "5520.8",
    pnl: 41.0,
    note: "Moving averages crossed down",
  },
  {
    time: "Sep 24 10:05",
    symbol: "US500",
    side: "Buy",
    lots: 0.2,
    entry: "5470.4",
    exit: "5502.9",
    pnl: 65.0,
    note: "",
  },
];

export const DEMO_ENTITIES: Entity[] = [
  {
    id: "us500-trend",
    kind: "bot",
    name: "US500 Trend",
    summary: "H4 dual moving average with volatility filter",
    stage: "Live",
    version: "v3",
    fp: "fp1:3b9e…c12d",
    family: "Trend following",
    measures: [M.sharpe("1.10"), M.dd("−7.9%"), M.win("48%"), M.ret("+21.6%")],
    spark: walk(5, 0.12),
    evidence: runs(3),
    journal: JOURNAL,
    connections: [
      {
        node: "Live node · VPS London",
        book: "IDX-L",
        mode: "Live",
        seat: "active",
      },
    ],
    parameters: [
      ["Fast average", "20 bars"],
      ["Slow average", "80 bars"],
      ["Volatility filter", "ATR 14 > median"],
      ["Exit", "Opposite cross or 2.5 ATR stop"],
    ],
    streams: ["US500 · H4 bars", "Economic calendar (news windows)"],
    artifacts: ["r3"],
  },
  {
    id: "gold-fade",
    kind: "bot",
    name: "Gold Fade",
    summary: "D1 Bollinger band mean reversion",
    stage: "Paper",
    version: "v5",
    fp: "fp1:41ab…77c3",
    family: "Mean reversion",
    measures: [M.sharpe("0.88"), M.dd("−4.0%"), M.win("61%"), M.ret("+6.2%")],
    spark: walk(9, -0.02),
    evidence: runs(7),
    connections: [
      {
        node: "Paper node · this machine",
        book: "GOLD-P",
        mode: "Paper",
        seat: "benched",
      },
    ],
    parameters: [
      ["Band length", "20 bars"],
      ["Band width", "2.2 σ"],
      ["Drawdown limit", "4% (hit Sep 30)"],
    ],
    streams: ["XAUUSD · D1 bars"],
    artifacts: ["r2"],
  },
  {
    id: "eurusd-h1-gbm",
    kind: "bot",
    name: "EURUSD H1 GBM",
    summary: "Gradient-boosted breakout entries, London session",
    stage: "Evidence",
    version: "v7 draft",
    fp: "fp1:9c41…e2a0",
    family: "Breakout · ML-assisted",
    measures: [M.sharpe("1.42"), M.dd("−6.8%"), M.win("54%"), M.ret("+18.4%")],
    spark: walk(3, 0.1),
    evidence: runs(4),
    connections: [],
    parameters: [
      ["Entry score", "> 0.60"],
      ["Take profit", "2 × ATR"],
      ["Stop", "1 × ATR"],
      ["Session", "London open ± 2h"],
    ],
    streams: ["EURUSD · H1 bars", "Model: EURUSD breakout scorer"],
    artifacts: ["r1", "r4"],
  },
  {
    id: "breakout-scorer",
    kind: "model",
    name: "EURUSD breakout scorer",
    summary: "LightGBM classifier on ATR, RSI and session features",
    stage: "Research",
    version: "v7",
    fp: "fp1:77f0…aa19",
    family: "Gradient boosting",
    measures: [
      {
        key: "auc",
        label: "AUC",
        value: "0.61",
        help: "How well the model ranks winners above losers. 0.5 is a coin flip.",
      },
      {
        key: "folds",
        label: "Fold stability",
        value: "±0.03",
        help: "How much AUC moves across the 12 walk-forward folds.",
      },
      {
        key: "leak",
        label: "Leakage checks",
        value: "6 / 6 pass",
        help: "Purge, embargo and look-ahead checks.",
      },
      {
        key: "lat",
        label: "Inference",
        value: "0.4 ms",
        help: "Time to score one bar.",
      },
    ],
    spark: walk(13, 0.06),
    evidence: runs(5),
    slots: ["Entry signal", "Position sizing (confidence)"],
    parameters: [
      ["Trees", "400"],
      ["Learning rate", "0.03"],
      ["Validation", "Walk-forward, 12 folds, 24-bar embargo"],
    ],
    streams: ["fx-majors H1 2019–2026 (dataset)"],
    artifacts: ["r4", "r5"],
  },
  {
    id: "regime-hmm",
    kind: "model",
    name: "Market regime HMM",
    summary: "Three-state hidden Markov model on returns and volatility",
    stage: "Research",
    version: "v2",
    fp: "fp1:a1c7…093e",
    family: "Hidden Markov model",
    measures: [
      {
        key: "states",
        label: "Regimes",
        value: "3",
        help: "Calm trend, choppy, stressed.",
      },
      {
        key: "persist",
        label: "Avg regime length",
        value: "11 days",
        help: "How long a regime usually lasts.",
      },
      {
        key: "ll",
        label: "Out-of-sample fit",
        value: "−1.92",
        help: "Log-likelihood per bar on unseen data; higher is better.",
      },
      {
        key: "lat",
        label: "Inference",
        value: "0.1 ms",
        help: "Time to label one bar.",
      },
    ],
    spark: walk(21, 0.0),
    slots: ["Market intelligence (regime)", "Risk (exposure throttle)"],
    parameters: [
      ["States", "3"],
      ["Inputs", "Daily returns, ATR percentile"],
    ],
    streams: ["Index and FX D1 bars"],
  },
  {
    id: "research-fx",
    kind: "app",
    name: "Research · FX",
    summary: "Charts, calendar, signals and correlation for FX majors",
    stage: "Installed",
    version: "1.4.0",
    fp: "fp1:5d20…71bb",
    measures: [
      {
        key: "views",
        label: "Views",
        value: "3",
        help: "Screens the app adds to its navigation.",
      },
      {
        key: "ops",
        label: "Operations",
        value: "5",
        help: "Actions the app can run through the daemon.",
      },
      {
        key: "copilot",
        label: "App copilot",
        value: "Yes",
        help: "Has its own copilot with this app's tools.",
      },
      {
        key: "grants",
        label: "Granted",
        value: "4 of 5",
        help: "Operations you have allowed it to run.",
      },
    ],
    views: ["Overview", "Signals", "Risk"],
    copilotProfile: true,
    ops: [
      {
        id: "fx.quote",
        summary: "Latest quotes for a watchlist",
        effect: "read",
        inputs: [{ name: "symbols", type: "string[]", required: true }],
      },
      {
        id: "fx.signals",
        summary: "Score current bars with the breakout scorer",
        effect: "compute",
        inputs: [
          { name: "symbol", type: "string", required: true },
          { name: "timeframe", type: "H1 | H4 | D1" },
        ],
      },
      {
        id: "fx.correlation",
        summary: "Rolling correlation matrix",
        effect: "compute",
        inputs: [{ name: "window", type: "days", required: true }],
      },
    ],
  },
  {
    id: "calendar-sync",
    kind: "app",
    name: "Calendar sync",
    summary: "Pulls the free economic calendar and opens news windows",
    stage: "Installed",
    version: "0.9.2",
    fp: "fp1:c0e4…2a71",
    measures: [
      {
        key: "views",
        label: "Views",
        value: "None",
        help: "Headless: it has no screens.",
      },
      {
        key: "ops",
        label: "Operations",
        value: "2",
        help: "Actions the app can run through the daemon.",
      },
      {
        key: "last",
        label: "Last run",
        value: "14:00",
        help: "When it last finished.",
      },
      {
        key: "next",
        label: "Next run",
        value: "15:00",
        help: "Scheduled by the daemon.",
      },
    ],
    views: [],
    copilotProfile: false,
    ops: [
      {
        id: "calendar.refresh",
        summary: "Fetch this week's calendar",
        effect: "read",
        inputs: [],
      },
      {
        id: "calendar.windows",
        summary: "List news windows that block new entries",
        effect: "read",
        inputs: [
          { name: "from", type: "date" },
          { name: "to", type: "date" },
        ],
      },
    ],
  },
  {
    id: "nightly-evidence",
    kind: "workflow",
    name: "Nightly evidence",
    summary:
      "Refresh data, re-run evidence for every bot in Evidence stage, write reports",
    stage: "Installed",
    version: "v4",
    fp: "fp1:e88a…14f0",
    measures: [
      {
        key: "runs",
        label: "Runs this month",
        value: "30",
        help: "Completed runs.",
      },
      {
        key: "pass",
        label: "Finished cleanly",
        value: "28",
        help: "Runs with no failed step.",
      },
      {
        key: "dur",
        label: "Typical duration",
        value: "21 min",
        help: "Median wall-clock time.",
      },
      {
        key: "steps",
        label: "Steps",
        value: "5",
        help: "Operations in the graph.",
      },
    ],
    steps: [
      "data.refresh",
      "qmb walk-forward",
      "qmb monte-carlo",
      "report.write",
      "library.save",
    ],
    runs: 30,
  },
  {
    id: "idea-miner",
    kind: "workflow",
    name: "Hypothesis miner",
    summary:
      "Scan Library articles and papers, propose hypotheses with citations",
    stage: "Draft",
    version: "v1 draft",
    fp: "fp1:—",
    measures: [
      {
        key: "runs",
        label: "Runs this month",
        value: "3",
        help: "Completed runs.",
      },
      {
        key: "out",
        label: "Hypotheses proposed",
        value: "17",
        help: "Candidates written to Stage 0.",
      },
      {
        key: "dur",
        label: "Typical duration",
        value: "48 min",
        help: "Median wall-clock time.",
      },
      {
        key: "steps",
        label: "Steps",
        value: "4",
        help: "Operations in the graph.",
      },
    ],
    steps: [
      "library.search",
      "copilot.summarise",
      "qml.stage0.propose",
      "library.save",
    ],
    runs: 3,
  },
];

/** DEMO ARTIFACTS: files QMX produced or stored, each with its producer and a content fingerprint. */
export type DemoArtifact = {
  id: string;
  type:
    | "Backtest report"
    | "Dataset"
    | "Model file"
    | "Trade journal"
    | "Paper results"
    | "Chart pack";
  name: string;
  producedBy: string;
  size: string;
  date: string;
  fp: string;
};

export const DEMO_ARTIFACTS: DemoArtifact[] = [
  {
    id: "r1",
    type: "Backtest report",
    name: "eurusd-h1-gbm · v7 walk-forward",
    producedBy: "EURUSD H1 GBM · run 441",
    size: "2.4 MB",
    date: "Today 12:10",
    fp: "fp1:9c41…e2a0",
  },
  {
    id: "r2",
    type: "Paper results",
    name: "Gold Fade · September paper",
    producedBy: "Paper node · book GOLD-P",
    size: "380 KB",
    date: "Sep 30",
    fp: "fp1:41ab…77c3",
  },
  {
    id: "r3",
    type: "Trade journal",
    name: "US500 Trend · live journal Q3",
    producedBy: "Live node · book IDX-L",
    size: "1.1 MB",
    date: "Sep 30",
    fp: "fp1:0d9e…b151",
  },
  {
    id: "r4",
    type: "Model file",
    name: "eurusd-breakout-scorer.lgbm · v7",
    producedBy: "Nightly evidence workflow",
    size: "18.7 MB",
    date: "Today 12:08",
    fp: "fp1:77f0…aa19",
  },
  {
    id: "r5",
    type: "Dataset",
    name: "fx-majors H1 2019–2026",
    producedBy: "data.refresh",
    size: "214 MB",
    date: "Today 14:05",
    fp: "fp1:c3d2…0f8e",
  },
  {
    id: "r6",
    type: "Chart pack",
    name: "Crypto majors correlation",
    producedBy: "Copilot session · Sep 27",
    size: "640 KB",
    date: "Sep 27",
    fp: "fp1:5e1a…3c47",
  },
];
