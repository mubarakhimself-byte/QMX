/**
 * Panel size modes (DESIGN-RULES.md). A tile measures its body and every
 * panel inside can ask which mode it is in: compact shows a summary, regular
 * the working view, expanded the full controls.
 */
import { getContext, setContext } from "svelte";

export type PanelSize = "compact" | "regular" | "expanded";

/** Thresholds in rem, so a larger Text size setting reaches compact sooner. */
export const COMPACT_BELOW = { width: 24, height: 13 };
export const EXPANDED_FROM = { width: 56, height: 30 };

export function sizeMode(
  box: { width: number; height: number },
  rem: number,
  maximised: boolean,
): PanelSize {
  if (maximised) return "expanded";
  const w = box.width / rem;
  const h = box.height / rem;
  if (w < COMPACT_BELOW.width || h < COMPACT_BELOW.height) return "compact";
  if (w >= EXPANDED_FROM.width && h >= EXPANDED_FROM.height) return "expanded";
  return "regular";
}

export type PanelSizeReader = { readonly mode: PanelSize };

const KEY = Symbol("panel-size");
const OUTSIDE_A_TILE: PanelSizeReader = { mode: "regular" };

export function providePanelSize(reader: PanelSizeReader) {
  setContext(KEY, reader);
}

/**
 * Call during component setup. Read `.mode` in markup or `$derived`; it
 * updates as the tile is resized. Outside a tile it is always "regular".
 */
export function panelSize(): PanelSizeReader {
  return getContext<PanelSizeReader | undefined>(KEY) ?? OUTSIDE_A_TILE;
}
