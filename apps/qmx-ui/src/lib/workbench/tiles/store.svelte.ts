/**
 * Saved tiling layouts for one surface: built-ins that can be edited and
 * reset, plus the operator's own. Kept per machine in browser storage.
 * Portfolio uses it; the Lab has its own copy of the same rules.
 */
import { parseLayouts, type TileLayout } from "./tiles";

const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

export class LayoutStore {
  stored = $state<TileLayout[]>([]);
  activeId = $state("");
  editing = $state(false);

  constructor(
    private key: string,
    private builtins: TileLayout[],
  ) {
    this.activeId = builtins[0].id;
    try {
      const raw = localStorage.getItem(key);
      this.stored = raw ? parseLayouts(JSON.parse(raw), () => true) : [];
    } catch {
      this.stored = [];
    }
  }

  get layouts(): TileLayout[] {
    return [
      ...this.builtins.map((b) => this.stored.find((s) => s.id === b.id) ?? b),
      ...this.stored.filter((s) => !this.builtins.some((b) => b.id === s.id)),
    ];
  }

  get active(): TileLayout {
    return this.layouts.find((l) => l.id === this.activeId) ?? this.layouts[0];
  }

  isBuiltin(id: string) {
    return this.builtins.some((b) => b.id === id);
  }

  isEdited(id: string) {
    return this.isBuiltin(id) && this.stored.some((s) => s.id === id);
  }

  private persist() {
    try {
      localStorage.setItem(this.key, JSON.stringify(this.stored));
    } catch {
      /* storage unavailable: edits last for this window */
    }
  }

  update(next: TileLayout) {
    this.stored = [...this.stored.filter((s) => s.id !== next.id), next];
    this.persist();
  }

  saveAs(name: string) {
    const copy: TileLayout = {
      ...clone(this.active),
      id: `u-${Date.now().toString(36)}`,
      name: name.trim().slice(0, 40) || "My layout",
    };
    this.stored = [...this.stored, copy];
    this.activeId = copy.id;
    this.persist();
    return copy;
  }

  reset(id: string) {
    this.stored = this.stored.filter((s) => s.id !== id);
    if (!this.isBuiltin(id) && this.activeId === id)
      this.activeId = this.builtins[0].id;
    this.persist();
  }
}
