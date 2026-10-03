/**
 * How the app looks beyond the theme: the surface style (glass, liquid
 * glass, solid, brutalist), an optional custom theme the operator edits
 * like a VS Code theme, and whether the background art rotates. All per
 * machine; parsed defensively because they come from storage.
 */

export const SURFACES = [
  {
    id: "glass",
    label: "Glass",
    note: "Frosted panels over the art. The default.",
  },
  {
    id: "liquid",
    label: "Liquid glass",
    note: "Brighter edges and deeper blur on the frame; data stays solid.",
  },
  {
    id: "solid",
    label: "Solid",
    note: "Minimal and opaque. Calmest for long sessions.",
  },
  {
    id: "brutal",
    label: "Brutalist",
    note: "Square, thick outlines, hard shadows. Very high contrast.",
  },
] as const;
export type Surface = (typeof SURFACES)[number]["id"];

export type CustomTheme = {
  on: boolean;
  accent: string;
  background: string;
  /** Panel opacity 0.5–1. */
  panel: number;
  /** Corner radius in px, 0–16. */
  radius: number;
  /** Base text size in px, 13–18. */
  text: number;
};

export const DEFAULT_CUSTOM: CustomTheme = {
  on: false,
  accent: "#e0a64a",
  background: "#0d0e10",
  panel: 0.8,
  radius: 10,
  text: 15,
};

export const ROTATIONS = [
  { id: "off", label: "Off" },
  { id: "visit", label: "Each visit" },
  { id: "hourly", label: "Every hour" },
  { id: "daily", label: "Every day" },
] as const;
export type Rotation = (typeof ROTATIONS)[number]["id"];

const hex = (v: unknown, d: string) =>
  typeof v === "string" && /^#[0-9a-f]{6}$/i.test(v) ? v : d;
const num = (v: unknown, lo: number, hi: number, d: number) =>
  typeof v === "number" && Number.isFinite(v)
    ? Math.min(hi, Math.max(lo, v))
    : d;

export function parseCustom(raw: unknown): CustomTheme {
  const o = (raw && typeof raw === "object" ? raw : {}) as Record<
    string,
    unknown
  >;
  return {
    on: o.on === true,
    accent: hex(o.accent, DEFAULT_CUSTOM.accent),
    background: hex(o.background, DEFAULT_CUSTOM.background),
    panel: num(o.panel, 0.5, 1, DEFAULT_CUSTOM.panel),
    radius: num(o.radius, 0, 16, DEFAULT_CUSTOM.radius),
    text: num(o.text, 13, 18, DEFAULT_CUSTOM.text),
  };
}

export const parseSurface = (v: unknown): Surface =>
  SURFACES.some((s) => s.id === v) ? (v as Surface) : "glass";

export const parseRotation = (v: unknown): Rotation =>
  ROTATIONS.some((r) => r.id === v) ? (v as Rotation) : "off";

/** Milliseconds between rotations, or null when it only rotates per visit or never. */
export const ROTATE_EVERY: Record<Rotation, number | null> = {
  off: null,
  visit: null,
  hourly: 60 * 60 * 1000,
  daily: 24 * 60 * 60 * 1000,
};
