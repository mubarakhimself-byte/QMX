/**
 * Panel size modes, ported from the October UI (workbench/tiles/panel-size.ts).
 * Every widget frame measures its own body and tells the widget inside which
 * mode it is in, so a big tile is never a small view with a hole under it:
 *   compact  - the fewest things that still answer the widget's question
 *   regular  - the working view
 *   expanded - everything, with full controls; always used in a widget's own tab
 */
import { getContext, setContext } from "svelte";

export type PanelSize = "compact" | "regular" | "expanded";

/** Thresholds in rem of the widget's body, so larger text reaches compact sooner. */
export const COMPACT_BELOW = { width: 21, height: 15 };
export const EXPANDED_FROM = { width: 42, height: 24 };

export function sizeMode(box: { width: number; height: number }, rem: number, maximised: boolean): PanelSize {
  if (maximised) return "expanded";
  const w = box.width / rem;
  const h = box.height / rem;
  if (w < COMPACT_BELOW.width || h < COMPACT_BELOW.height) return "compact";
  if (w >= EXPANDED_FROM.width && h >= EXPANDED_FROM.height) return "expanded";
  return "regular";
}

export type PanelSizeReader = { readonly mode: PanelSize; readonly width: number; readonly height: number };

const KEY = Symbol("panel-size");
const OUTSIDE_A_TILE: PanelSizeReader = { mode: "regular", width: 0, height: 0 };

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
