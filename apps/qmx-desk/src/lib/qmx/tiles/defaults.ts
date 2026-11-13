import type { Panel, Place } from "$lib/shell/data";
import { pane, panes, split, type Node } from "./tree";

/** A widget's reference in a layout: the place that supplies it, then its id. */
export const refOf = (place: string, panel: string) => `${place}/${panel}`;

/** Every widget a place offers: the ones on its board and its spares. */
export const offered = (place: Place): Panel[] => [...place.board.flat(), ...(place.spare ?? [])];

export function resolve(places: readonly Place[], ref: string): Panel | null {
  const cut = ref.indexOf("/");
  const place = places.find((p) => p.id === ref.slice(0, cut));
  return (place && offered(place).find((p) => p.id === ref.slice(cut + 1))) ?? null;
}

type Hand = (r: (id: string) => Node) => Node;

// Hand-set starting layouts, sized from what each widget holds (SPACE-RULES
// 2): the units and pods in the wide middle; "Running now" gets the tall
// right slot for its machines and runs; "Markets today" sits under it with
// its three bars and the day's agenda. Every widget has a neighbour on each
// axis it can be resized along.
const hand: Record<string, Hand> = {
  overview: (r) =>
    split("row", [
      [split("col", [[r("waiting"), 56], [r("since"), 44]]), 27],
      [split("col", [[r("units"), 57], [r("pods"), 43]]), 42],
      [split("col", [[r("running"), 55], [r("markets"), 45]]), 31],
    ]),
  trading: (r) =>
    split("col", [
      [split("row", [[r("t:u-gold"), 31], [r("t:u-btc"), 23], [r("t:u-london"), 23], [r("t:u-index"), 23]]), 52],
      [split("row", [[r("positions"), 62], [r("nodes"), 38]]), 48],
    ]),
};

/**
 * The layout a place starts with. A hand-set one when every widget it names
 * still exists; otherwise the place's own board, column by column.
 */
export function defaultLayout(place: Place): Node | null {
  const have = new Set(place.board.flat().map((p) => p.id));
  const r = (id: string) => pane(refOf(place.id, id));
  const h = hand[place.id]?.(r);
  if (h && panes(h).every((ref) => have.has(ref.slice(place.id.length + 1)))) return h;

  const n = Math.max(0, ...place.board.map((row) => row.length));
  const cols: [Node, number][] = [];
  for (let i = 0; i < n; i++) {
    const all = place.board.map((row) => row[i]).filter(Boolean);
    if (!all.length) continue;
    const col = all.length === 1 ? r(all[0].id) : split("col", all.map((p) => [r(p.id), p.grow ?? 1]));
    cols.push([col, Math.max(...all.map((p) => p.grow ?? 1))]);
  }
  if (cols.length === 0) return null;
  return cols.length === 1 ? cols[0][0] : split("row", cols);
}
