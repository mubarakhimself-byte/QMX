/**
 * UI projections of QMX entities shown in Library, Copilot and Home.
 * Shapes follow the contracts loosely (CT-33 bot, CT-32 evidence, CT-13
 * journal, pack operations) but these are display types, not contracts.
 * Evidence is shown as raw named measures: no composite scores, ratings
 * or tiers (QMB rule).
 */

export type EntityKind = "bot" | "model" | "app" | "workflow";

export type Stage =
  | "Hypothesis"
  | "Research"
  | "Evidence"
  | "Paper"
  | "Live"
  | "Installed"
  | "Draft";

export type Measure = {
  key: string;
  label: string;
  value: string;
  /** Plain-words definition shown on hover and in detail views. */
  help: string;
  tone?: "up" | "down";
};

export type EvidenceRun = {
  run: string;
  kind:
    | "Backtest"
    | "Walk-forward"
    | "Monte Carlo"
    | "Optimise"
    | "Significance"
    | "Sweep";
  role: "confirmation" | "trial" | "replicate";
  period: string;
  sharpe: string;
  maxDrawdown: string;
  trades: number;
  when: string;
};

export type JournalEntry = {
  time: string;
  symbol: string;
  side: "Buy" | "Sell";
  lots: number;
  entry: string;
  exit: string;
  pnl: number;
  note: string;
};

export type Connection = {
  /** The trading server it runs on. */
  server: string;
  /** The pod that sizes its trades. */
  pod: string;
  mode: "Paper" | "Live";
  seat: "active" | "benched";
};

export type Operation = {
  id: string;
  summary: string;
  effect: "read" | "compute" | "trade-adjacent";
  inputs: { name: string; type: string; required?: boolean }[];
};

export type Entity = {
  id: string;
  kind: EntityKind;
  name: string;
  summary: string;
  stage: Stage;
  version: string;
  /** Content fingerprint (fp1) shortened for display. */
  fp: string;
  family?: string;
  measures: Measure[];
  spark?: number[];
  evidence?: EvidenceRun[];
  journal?: JournalEntry[];
  connections?: Connection[];
  parameters?: [string, string][];
  streams?: string[];
  /** Mini apps: operations, views (empty = headless), copilot profile. */
  ops?: Operation[];
  views?: string[];
  copilotProfile?: boolean;
  /** Workflows: ordered steps and run history count. */
  steps?: string[];
  runs?: number;
  /** ML models: where in QMX the model can be plugged in. */
  slots?: string[];
  artifacts?: string[];
};

export const KIND_LABEL: Record<EntityKind, string> = {
  bot: "Bot",
  model: "ML model",
  app: "Mini app",
  workflow: "Workflow",
};

/** The pipeline every strategy walks (docs: QML Stage 0 → QMB → QMN). */
export const PIPELINE: Stage[] = [
  "Hypothesis",
  "Research",
  "Evidence",
  "Paper",
  "Live",
];
