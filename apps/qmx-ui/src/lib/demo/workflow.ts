/**
 * DEMO WORKFLOW ONLY. A sample graph for design review: not a saved draft,
 * not daemon-issued, and it cannot run.
 */
import type { Edge, Node } from "@xyflow/svelte";

export type StepData = {
  kind: "Data" | "Feature" | "Model" | "Test" | "Output";
  label: string;
  detail: string;
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
    label: "MT5 bars",
    detail: "EURUSD · H1 · 2019–2026",
    x: 0,
    y: 80,
    settings: [
      ["Source", "MT5 terminal"],
      ["Symbol", "EURUSD"],
      ["Timeframe", "H1"],
      ["Range", "2019-01-01 → 2026-09-30"],
    ],
    code: `bars = mt5.bars("EURUSD", "H1", start="2019-01-01")\nbars = bars.dropna()`,
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
    code: `report(result).save_to_library("eurusd-h1-gbm")`,
  },
];

export const demoNodes = (): Node[] =>
  DEMO_STEPS.map((s) => ({
    id: s.id,
    type: "step",
    position: { x: s.x, y: s.y },
    data: { kind: s.kind, label: s.label, detail: s.detail },
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
