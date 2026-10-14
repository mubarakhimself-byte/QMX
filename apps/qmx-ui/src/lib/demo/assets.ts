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
    symbol: "ETHUSDT",
    side: "Buy",
    lots: 0.8,
    entry: "3098.2",
    exit: "3181.7",
    pnl: 66.8,
    note: "Trend resumed after the US open",
  },
  {
    time: "Sep 29 09:15",
    symbol: "ETHUSDT",
    side: "Buy",
    lots: 0.8,
    entry: "3112.0",
    exit: "3055.8",
    pnl: -45.0,
    note: "Stopped out on CPI spike",
  },
  {
    time: "Sep 26 16:40",
    symbol: "ETHUSDT",
    side: "Sell",
    lots: 0.8,
    entry: "3141.3",
    exit: "3090.1",
    pnl: 41.0,
    note: "Moving averages crossed down",
  },
  {
    time: "Sep 24 10:05",
    symbol: "ETHUSDT",
    side: "Buy",
    lots: 0.8,
    entry: "3070.4",
    exit: "3151.6",
    pnl: 65.0,
    note: "",
  },
];

const GOLD_JOURNAL: JournalEntry[] = [
  {
    time: "Oct 14 08:02",
    symbol: "XAUUSD",
    side: "Buy",
    lots: 0.5,
    entry: "2381.40",
    exit: "2384.10",
    pnl: 135.0,
    note: "London open push; target hit",
  },
  {
    time: "Oct 13 14:31",
    symbol: "XAUUSD",
    side: "Sell",
    lots: 0.5,
    entry: "2390.20",
    exit: "2391.60",
    pnl: -70.0,
    note: "Stopped out; spread widened before US data",
  },
  {
    time: "Oct 13 08:10",
    symbol: "XAUUSD",
    side: "Buy",
    lots: 0.5,
    entry: "2376.90",
    exit: "2379.30",
    pnl: 120.0,
    note: "",
  },
];

export const DEMO_ENTITIES: Entity[] = [
  {
    id: "xau-scalp",
    kind: "bot",
    name: "Gold scalper",
    summary:
      "Short scalps on gold (XAUUSD CFD) around the London and New York opens",
    stage: "Live",
    version: "v4",
    fp: "fp1:9c41…e2b7",
    family: "Scalper",
    measures: [M.sharpe("1.42"), M.dd("−2.6%"), M.win("58%"), M.ret("+5.1%")],
    spark: walk(17, 0.1),
    evidence: runs(4),
    journal: GOLD_JOURNAL,
    connections: [
      {
        server: "London",
        pod: "Gold & indices",
        mode: "Live",
        seat: "active",
      },
    ],
    parameters: [
      ["Market", "XAUUSD CFD at IC Markets (cTrader)"],
      ["Sessions", "London and New York opens, 30 minutes each"],
      ["Loss per trade", "0.3% of the pod, fixed"],
      ["Leverage", "Up to 10× of the account's 30×"],
      ["News", "Pauses 15 minutes around high-impact events"],
    ],
    streams: ["XAUUSD · 1m bars and spread", "Economic calendar"],
    artifacts: ["r3"],
  },
  {
    id: "eth-trend",
    kind: "bot",
    name: "ETH trend",
    summary: "4h dual moving average with a volatility filter",
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
        server: "Tokyo",
        pod: "BTC & ETH core",
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
    streams: ["ETHUSDT · 4h bars", "Crypto news (event windows)"],
    artifacts: ["r3"],
  },
  {
    id: "eth-mr",
    kind: "bot",
    name: "ETH mean reversion",
    summary: "Daily Bollinger band mean reversion",
    stage: "Paper",
    version: "v5",
    fp: "fp1:41ab…77c3",
    family: "Mean reversion",
    measures: [M.sharpe("0.88"), M.dd("−4.0%"), M.win("61%"), M.ret("+6.2%")],
    spark: walk(9, -0.02),
    evidence: runs(7),
    connections: [
      {
        server: "This laptop",
        pod: "Mean reversion",
        mode: "Paper",
        seat: "benched",
      },
    ],
    parameters: [
      ["Band length", "20 bars"],
      ["Band width", "2.2 σ"],
      ["Drawdown limit", "4% (hit Sep 30)"],
    ],
    streams: ["ETHUSDT · 1d bars"],
    artifacts: ["r2"],
  },
  {
    id: "btc-breakout",
    kind: "bot",
    name: "BTC breakout",
    summary: "Gradient-boosted breakout entries, Asia-to-Europe handover",
    stage: "Evidence",
    version: "v7 draft",
    fp: "fp1:9c41…e2a0",
    family: "Breakout · ML-assisted",
    measures: [M.sharpe("1.42"), M.dd("−6.8%"), M.win("54%"), M.ret("+18.4%")],
    spark: walk(3, 0.1),
    evidence: runs(4),
    connections: [
      {
        server: "Tokyo",
        pod: "BTC & ETH core",
        mode: "Live",
        seat: "active",
      },
    ],
    parameters: [
      ["Entry score", "> 0.60"],
      ["Take profit", "2 × ATR"],
      ["Stop", "1 × ATR"],
      ["Hours", "06:00–10:00 UTC"],
    ],
    streams: ["BTCUSDT · 1h bars", "Model: BTC breakout scorer"],
    artifacts: ["r1", "r4"],
  },
  {
    id: "breakout-scorer",
    kind: "model",
    name: "BTC breakout scorer",
    summary: "LightGBM classifier on ATR, RSI and funding-rate features",
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
    streams: ["Binance spot 1h 2019–2026 (dataset)"],
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
    streams: ["BTC and ETH daily bars"],
  },
  {
    id: "research-crypto",
    kind: "app",
    name: "Research · Crypto",
    summary: "Charts, news, signals and correlation for the top coins",
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
        id: "crypto.quote",
        summary: "Latest quotes for a watchlist",
        effect: "read",
        inputs: [{ name: "symbols", type: "string[]", required: true }],
      },
      {
        id: "crypto.signals",
        summary: "Score current bars with the breakout scorer",
        effect: "compute",
        inputs: [
          { name: "symbol", type: "string", required: true },
          { name: "timeframe", type: "1h | 4h | 1d" },
        ],
      },
      {
        id: "crypto.correlation",
        summary: "Rolling correlation matrix",
        effect: "compute",
        inputs: [{ name: "window", type: "days", required: true }],
      },
    ],
  },
  {
    id: "news-sentiment",
    kind: "app",
    name: "News & sentiment",
    summary:
      "Pulls crypto news and the macro calendar, scores sentiment, opens news windows",
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
        id: "news.refresh",
        summary: "Fetch the latest news and this week's calendar",
        effect: "read",
        inputs: [],
      },
      {
        id: "news.windows",
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
    name: "btc-breakout · v7 walk-forward",
    producedBy: "BTC breakout · run 441",
    size: "2.4 MB",
    date: "Today 12:10",
    fp: "fp1:9c41…e2a0",
  },
  {
    id: "r2",
    type: "Paper results",
    name: "ETH mean reversion · September paper",
    producedBy: "Paper · Mean reversion pod",
    size: "380 KB",
    date: "Sep 30",
    fp: "fp1:41ab…77c3",
  },
  {
    id: "r3",
    type: "Trade journal",
    name: "ETH trend · live journal Q3",
    producedBy: "Live · BTC & ETH core pod",
    size: "1.1 MB",
    date: "Sep 30",
    fp: "fp1:0d9e…b151",
  },
  {
    id: "r4",
    type: "Model file",
    name: "btc-breakout-scorer.lgbm · v7",
    producedBy: "Nightly evidence workflow",
    size: "18.7 MB",
    date: "Today 12:08",
    fp: "fp1:77f0…aa19",
  },
  {
    id: "r5",
    type: "Dataset",
    name: "Binance spot 1h 2019–2026",
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
