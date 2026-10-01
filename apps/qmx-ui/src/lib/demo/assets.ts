/** DEMO ASSETS ONLY: sample bots, models, apps and workflows with sample ratings. */
import type { Asset } from "$lib/qmx/AssetCard.svelte";

function walk(seed: number, drift: number): number[] {
  let s = seed;
  let v = 100;
  return Array.from({ length: 30 }, () => {
    s = (s * 9301 + 49297) % 233280;
    v *= 1 + (s / 233280 - 0.5 + drift) * 0.03;
    return v;
  });
}

const TRADE = (
  ret: number,
  shp: number,
  dd: number,
  win: number,
  stb: number,
  cap: number,
) => [
  { key: "RET", label: "Return", value: ret },
  { key: "SHP", label: "Sharpe", value: shp },
  { key: "DD", label: "Drawdown resilience", value: dd },
  { key: "WIN", label: "Win rate", value: win },
  { key: "STB", label: "Stability across folds", value: stb },
  { key: "CAP", label: "Capacity", value: cap },
];

export const DEMO_ASSETS: Asset[] = [
  {
    id: "b1",
    kind: "bot",
    name: "US500 Trend",
    role: "H4 dual moving average",
    stage: "Live",
    rating: 88,
    attributes: TRADE(84, 86, 90, 71, 92, 88),
    spark: walk(5, 0.12),
    tags: ["index"],
  },
  {
    id: "b2",
    kind: "bot",
    name: "Gold Fade",
    role: "D1 Bollinger mean reversion",
    stage: "Paper",
    rating: 76,
    attributes: TRADE(72, 74, 63, 80, 70, 82),
    spark: walk(9, -0.05),
    tags: ["metals"],
  },
  {
    id: "b3",
    kind: "bot",
    name: "USDJPY Carry",
    role: "Rate differential",
    stage: "Paper",
    rating: 79,
    attributes: TRADE(77, 75, 81, 66, 84, 90),
    spark: walk(13, 0.06),
    tags: ["fx"],
  },
  {
    id: "m1",
    kind: "model",
    name: "EURUSD H1 GBM",
    role: "Gradient boosting · triple barrier",
    stage: "Research",
    rating: 86,
    attributes: [
      { key: "AUC", label: "AUC", value: 81 },
      { key: "SHP", label: "Backtest Sharpe", value: 87 },
      { key: "STB", label: "Fold stability", value: 84 },
      { key: "LEAK", label: "Leakage checks", value: 96 },
      { key: "SPD", label: "Inference speed", value: 92 },
      { key: "DATA", label: "Data coverage", value: 88 },
    ],
    spark: walk(3, 0.1),
    tags: ["fx", "ml"],
  },
  {
    id: "m2",
    kind: "model",
    name: "News Sentiment",
    role: "Transformer features",
    stage: "Research",
    rating: 71,
    attributes: [
      { key: "AUC", label: "AUC", value: 64 },
      { key: "SHP", label: "Backtest Sharpe", value: 58 },
      { key: "STB", label: "Fold stability", value: 69 },
      { key: "LEAK", label: "Leakage checks", value: 90 },
      { key: "SPD", label: "Inference speed", value: 61 },
      { key: "DATA", label: "Data coverage", value: 77 },
    ],
    spark: walk(41, -0.02),
    tags: ["nlp"],
  },
  {
    id: "a1",
    kind: "app",
    name: "Research · FX",
    role: "Charts, calendar, signals",
    stage: "Installed",
    rating: 90,
    attributes: [
      { key: "USE", label: "Weekly use", value: 94 },
      { key: "WID", label: "Widgets", value: 86 },
      { key: "REL", label: "Reliability", value: 92 },
      { key: "FRS", label: "Data freshness", value: 89 },
      { key: "AGT", label: "Agent support", value: 88 },
      { key: "SPD", label: "Load speed", value: 85 },
    ],
    tags: ["app"],
  },
  {
    id: "w1",
    kind: "workflow",
    name: "Nightly backtest",
    role: "Data → model → report",
    stage: "Installed",
    rating: 83,
    attributes: [
      { key: "RUN", label: "Runs this month", value: 90 },
      { key: "PAS", label: "Pass rate", value: 86 },
      { key: "SPD", label: "Duration", value: 74 },
      { key: "STEP", label: "Steps", value: 70 },
      { key: "REL", label: "Retries needed", value: 88 },
      { key: "COST", label: "Compute cost", value: 81 },
    ],
    tags: ["workflow"],
  },
  {
    id: "w2",
    kind: "workflow",
    name: "MQL5 idea miner",
    role: "Library scan → hypotheses",
    stage: "Draft",
    rating: 68,
    attributes: [
      { key: "RUN", label: "Runs this month", value: 42 },
      { key: "PAS", label: "Pass rate", value: 75 },
      { key: "SPD", label: "Duration", value: 58 },
      { key: "STEP", label: "Steps", value: 80 },
      { key: "REL", label: "Retries needed", value: 66 },
      { key: "COST", label: "Compute cost", value: 71 },
    ],
    tags: ["library"],
  },
];
