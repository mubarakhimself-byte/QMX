/**
 * Board layouts, one per place, kept on this machine. A place with no saved
 * layout shows its default; Reset forgets the saved one.
 */
import type { Place } from "$lib/shell/data";
import { defaultLayout } from "./defaults";
import { parseLayout, type Layout } from "./tree";

// v2: round 5 changed the starting layouts and replaced a widget, so
// layouts saved before it are set aside.
const KEY = "qmx-desk.tiles.v2";

function load(): Record<string, Layout> {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Record<string, unknown>;
    const out: Record<string, Layout> = {};
    for (const [k, v] of Object.entries(raw)) {
      const l = parseLayout(v);
      if (l) out[k] = l;
    }
    return out;
  } catch {
    return {};
  }
}

class TileStore {
  saved = $state<Record<string, Layout>>(typeof localStorage === "undefined" ? {} : load());
  /** Arrange mode: remove buttons on every widget, grips always shown. */
  arranging = $state(false);
  #timer: ReturnType<typeof setTimeout> | undefined;

  layout(place: Place): Layout {
    return this.saved[place.id] ?? { root: defaultLayout(place), docked: [] };
  }
  isEdited(place: string) {
    return place in this.saved;
  }
  set(place: string, next: Layout) {
    this.saved = { ...this.saved, [place]: next };
    this.#persist();
  }
  reset(place: string) {
    const { [place]: _gone, ...rest } = this.saved;
    this.saved = rest;
    this.#persist();
  }
  #persist() {
    clearTimeout(this.#timer);
    this.#timer = setTimeout(() => {
      try {
        localStorage.setItem(KEY, JSON.stringify(this.saved));
      } catch {
        /* storage unavailable: the layout lasts for this window */
      }
    }, 200);
  }
}

export const tiles = new TileStore();
