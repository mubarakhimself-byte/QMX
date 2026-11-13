// What the navigation shows, and how it fits without scrolling. Places come
// from the shell's place list (minus Usage, Settings and Needs you, which
// are reached from the top bar and the counts). Mini apps are guests: their
// own group, their own colours.
import { shell } from "../state.svelte";
import { things } from "../things.svelte";
import { guestInk, guestWash, type Guest } from "../model";
import type { Place } from "../data";

export type { Guest };

export const nav = {
  get places(): Place[] {
    return shell.places.filter((p) => !p.foot);
  },
  get apps(): Guest[] {
    return things.guests;
  },
  // The count on a place: what in it waits for him.
  badge(p: Place): number | undefined {
    if (shell.fixture === "first") return undefined;
    const n =
      p.id === "overview"
        ? things.needs.length
        : p.id === "sessions"
          ? things.needs.filter((o) => o.kind === "session").length
          : p.id === "workflows"
            ? things.needs.filter((o) => o.kind === "workflow").length
            : 0;
    return n || undefined;
  },
};

export const guestColour = (g: Guest) => guestInk(g.hue);
export const guestFill = (g: Guest) => guestWash(g.hue);

// Root font size in px for the current text size (matches app.css). Read
// from state, not the DOM, so it is right on the very first render.
const sizes: Record<string, number> = { standard: 17, large: 19, larger: 21 };
export function rem() {
  return sizes[shell.text] ?? 17;
}

// Show what fits in `slots`. When some do not fit, the last slot becomes
// "More" and holds the rest, so a list never scrolls.
export function fit<T>(items: T[], slots: number): { shown: T[]; more: T[] } {
  const n = Math.max(0, Math.floor(slots));
  if (items.length <= n) return { shown: items, more: [] };
  const keep = Math.max(0, n - 1);
  return { shown: items.slice(0, keep), more: items.slice(keep) };
}

// Each pill folds on its own to a small handle. Kept across places.
export const fold = $state({ places: false, apps: false });

// Keep a box's size in state. Re-reads on resize, on a text-size change and
// after the next frame, so the first layout at a new size is never missed.
export function size(el: HTMLElement, set: (w: number, h: number) => void) {
  const read = () => set(el.clientWidth, el.clientHeight);
  const ro = new ResizeObserver(read);
  ro.observe(el);
  ro.observe(document.documentElement);
  window.addEventListener("resize", read);
  const mo = new MutationObserver(() => requestAnimationFrame(read));
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-text"] });
  // Read now and on the next tick too: a page in a background tab gets no
  // animation frames, and the pills must still fit there.
  read();
  const t = setTimeout(read, 0);
  requestAnimationFrame(read);
  return {
    destroy() {
      clearTimeout(t);
      ro.disconnect();
      mo.disconnect();
      window.removeEventListener("resize", read);
    },
  };
}
