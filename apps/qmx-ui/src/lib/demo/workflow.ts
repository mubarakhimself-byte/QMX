/**
 * DEMO WORKFLOW ONLY. A sample graph for design review: not a saved draft,
 * not daemon-issued, and it cannot run.
 */
import type { Edge, Node } from "@xyflow/svelte";

export type StepData = {
  kind: "Data" | "Feature" | "Model" | "Test" | "Output";
  label: string;
  detail: string;
  /** Tiny preview of the step's last output (values 0..1). */
  preview?: number[];
  /** Last run of the published version. */
  status?: "ok" | "warn" | "stale";
};

type Step = StepData & {
  id: string;
  x: number;
  y: number;
  settings: [string, string][];
  code: string;
};

export const DEMO_STEPS: Step[] = [
  {
    id: "src",
    kind: "Data",
    label: "Exchange bars",
    detail: "BTCUSDT · H1 · 2019–2026",
    x: 0,
    y: 80,
    settings: [
      ["Source", "Binance spot"],
      ["Symbol", "BTCUSDT"],
      ["Timeframe", "H1"],
      ["Range", "2019-01-01 → 2026-09-30"],
    ],
    code: `bars = binance.bars("BTCUSDT", "H1", start="2019-01-01")\nbars = bars.dropna()`,
  },
  {
    id: "feat",
    kind: "Feature",
    label: "Indicators",
    detail: "ATR 14 · RSI 14 · session",
    x: 260,
    y: 0,
    settings: [
      ["ATR period", "14"],
      ["RSI period", "14"],
      ["Session flags", "London, New York"],
    ],
    code: `X = pd.DataFrame({\n    "atr": ta.atr(bars, 14),\n    "rsi": ta.rsi(bars.close, 14),\n    "session": sessions(bars.index),\n})`,
  },
  {
    id: "label",
    kind: "Feature",
    label: "Labels",
    detail: "Triple barrier · 2R / 1R",
    x: 260,
    y: 160,
    settings: [
      ["Method", "Triple barrier"],
      ["Take profit", "2 × ATR"],
      ["Stop", "1 × ATR"],
      ["Max hold", "24 bars"],
    ],
    code: `y = triple_barrier(bars, tp=2.0, sl=1.0, horizon=24)`,
  },
  {
    id: "model",
    kind: "Model",
    label: "Gradient boosting",
    detail: "Walk-forward · 12 folds",
    x: 520,
    y: 80,
    settings: [
      ["Algorithm", "LightGBM"],
      ["Validation", "Walk-forward, 12 folds"],
      ["Purge / embargo", "24 bars"],
    ],
    code: `model = lgb.LGBMClassifier(n_estimators=400, learning_rate=0.03)\npreds = walk_forward(model, X, y, folds=12, embargo=24)`,
  },
  {
    id: "bt",
    kind: "Test",
    label: "Backtest",
    detail: "Spread 0.8 · risk 0.5%",
    x: 780,
    y: 80,
    settings: [
      ["Spread", "0.8 pips"],
      ["Risk per trade", "0.5%"],
      ["Slippage", "0.2 pips"],
    ],
    code: `result = backtest(bars, signals=preds > 0.6, risk=0.005, spread=0.8)`,
  },
  {
    id: "out",
    kind: "Output",
    label: "Report",
    detail: "Equity curve · metrics",
    x: 1040,
    y: 80,
    settings: [
      ["Format", "Library artifact"],
      ["Includes", "Equity, drawdown, trades"],
    ],
    code: `report(result).save_to_library("btc-breakout")`,
  },
];

const wave = (seed: number, n = 24) =>
  Array.from(
    { length: n },
    (_, i) =>
      0.5 + 0.35 * Math.sin(i / 3 + seed) + 0.1 * Math.sin(i * 1.7 + seed * 2),
  );
const PREVIEWS: Record<string, number[]> = {
  src: wave(1),
  feat: wave(2),
  label: [0.38, 0.41, 0.21],
  model: Array.from(
    { length: 24 },
    (_, i) => 0.9 - 0.6 * (1 - Math.exp(-i / 6)),
  ),
  bt: Array.from({ length: 24 }, (_, i) => 0.2 + i * 0.03 + 0.05 * Math.sin(i)),
  out: wave(5),
};

/** Operations the palette offers (from published contributions in the real app). */
export const PALETTE: {
  group: StepData["kind"];
  items: { label: string; detail: string }[];
}[] = [
  {
    group: "Data",
    items: [
      { label: "Exchange bars", detail: "Pair, timeframe, range" },
      { label: "Dataset from Library", detail: "Any stored dataset" },
      { label: "Economic calendar", detail: "Events and news windows" },
    ],
  },
  {
    group: "Feature",
    items: [
      { label: "Indicators", detail: "ATR, RSI, moving averages" },
      { label: "Labels", detail: "Triple barrier, fixed horizon" },
      { label: "Regime", detail: "From a regime model" },
    ],
  },
  {
    group: "Model",
    items: [
      { label: "Gradient boosting", detail: "LightGBM / XGBoost" },
      { label: "Hidden Markov model", detail: "Regimes" },
      { label: "Rules", detail: "Plain entry and exit rules" },
    ],
  },
  {
    group: "Test",
    items: [
      { label: "Backtest", detail: "qmb backtest" },
      { label: "Walk-forward", detail: "qmb walk-forward" },
      { label: "Monte Carlo", detail: "qmb robustness" },
    ],
  },
  {
    group: "Output",
    items: [
      { label: "Report", detail: "Save to Library" },
      { label: "Alert", detail: "Notify on a condition" },
    ],
  },
];

export const demoNodes = (): Node[] =>
  DEMO_STEPS.map((s) => ({
    id: s.id,
    type: "step",
    position: { x: s.x, y: s.y },
    data: {
      kind: s.kind,
      label: s.label,
      detail: s.detail,
      preview: PREVIEWS[s.id],
      status: s.id === "label" ? "warn" : "ok",
    },
  }));

export const demoEdges = (): Edge[] =>
  [
    ["src", "feat"],
    ["src", "label"],
    ["feat", "model"],
    ["label", "model"],
    ["model", "bt"],
    ["bt", "out"],
  ].map(([source, target]) => ({
    id: `${source}-${target}`,
    source,
    target,
    animated: source === "model",
  }));
