/**
 * WidgetBoard: the one layout model every mini app uses, so widget
 * controls behave the same everywhere (add to copilot, minimise,
 * expand/return, close and add in edit mode). Layout is client-local
 * (UI EXPERIENCE §1): it never goes to the daemon.
 */
import { SvelteSet } from "svelte/reactivity";
import { workbench } from "./workbench.svelte";

/** Width on the 12-column grid; tall widgets take two rows. */
export type WidgetSize = "sm" | "md" | "lg" | "xl" | "full";

export type WidgetSpec = {
  id: string;
  title: string;
  size?: WidgetSize;
  tall?: boolean;
};

export const SPAN: Record<WidgetSize, string> = {
  sm: "col-span-12 md:col-span-6 xl:col-span-3",
  md: "col-span-12 md:col-span-6 xl:col-span-4",
  lg: "col-span-12 xl:col-span-6",
  xl: "col-span-12 xl:col-span-8",
  full: "col-span-12",
};

export class WidgetBoard {
  /** Widgets per view, in order. */
  layout = $state<Record<string, WidgetSpec[]>>({});
  /** Every widget the app offers (for "Add widget"). */
  catalog: WidgetSpec[];
  view = $state("");
  editing = $state(false);
  expanded = $state<string | null>(null);
  minimized = new SvelteSet<string>();

  constructor(views: Record<string, WidgetSpec[]>) {
    this.layout = structuredClone(views);
    this.view = Object.keys(views)[0] ?? "";
    // Every widget once, in first-seen order.
    this.catalog = Object.values(views)
      .flat()
      .filter((w, i, all) => all.findIndex((x) => x.id === w.id) === i);
  }

  get views(): string[] {
    return Object.keys(this.layout);
  }
  get shown(): WidgetSpec[] {
    return this.layout[this.view] ?? [];
  }
  get addable(): WidgetSpec[] {
    return this.catalog.filter((w) => !this.shown.some((x) => x.id === w.id));
  }
  spec(id: string): WidgetSpec | undefined {
    return this.catalog.find((w) => w.id === id);
  }

  setView(v: string) {
    this.view = v;
    this.expanded = null;
  }
  toggleMin(id: string) {
    if (this.minimized.has(id)) this.minimized.delete(id);
    else this.minimized.add(id);
  }
  toggleExpand(id: string) {
    this.expanded = this.expanded === id ? null : id;
  }
  close(id: string) {
    this.layout[this.view] = this.shown.filter((w) => w.id !== id);
    if (this.expanded === id) this.expanded = null;
  }
  add(id: string) {
    const w = this.spec(id);
    if (w) this.layout[this.view] = [...this.shown, w];
  }
  /** Message-only context chip in the copilot composer (UI CHAT §8). */
  mention(appName: string, id: string) {
    const w = this.spec(id);
    if (w) workbench.addRef(`${appName} · ${w.title}`);
  }
}
