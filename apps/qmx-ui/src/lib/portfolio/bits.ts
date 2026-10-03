/** Small shared helpers for Portfolio panels. */
import type { Ksa } from "./demo";

export const usd = (n: number, digits = 0) =>
  `${n < 0 ? "−" : ""}$${Math.abs(n).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits })}`;

export const pct = (n: number, digits = 1) =>
  `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toFixed(digits)}%`;

export const KSA_TONE: Record<Ksa, string> = {
  GREEN: "bg-success",
  YELLOW: "bg-warning",
  ORANGE: "bg-[oklch(0.72_0.17_55)]",
  RED: "bg-destructive",
  BLACK: "bg-foreground",
};

export const KSA_EFFECT: Record<Ksa, string> = {
  GREEN: "Normal trading",
  YELLOW: "Watch: alerts only",
  ORANGE: "No new entries",
  RED: "Drain: close as exits fire",
  BLACK: "Flatten everything",
};

export const RULE_TONE = {
  ok: "bg-success",
  near: "bg-warning",
  tripped: "bg-destructive",
} as const;

/** Paper and live tones for tile borders (operator, 2026-10-02). */
export const MODE_BORDER = {
  live: "color-mix(in oklab, var(--tone-live) 70%, transparent)",
  paper: "color-mix(in oklab, var(--tone-paper) 70%, transparent)",
} as const;
