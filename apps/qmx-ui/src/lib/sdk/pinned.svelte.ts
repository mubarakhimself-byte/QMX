/**
 * Panels pinned from the copilot onto a screen. A pinned panel is only its
 * description, so adding one is instant and needs no restart; removing the
 * tile removes it. Kept in this browser for the demo; the daemon stores
 * them (with versions) once wired.
 */
import type { PanelSpec } from "./spec";

const KEY = "qmx.pinned.panels";

function load(): Record<string, PanelSpec> {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "{}");
  } catch {
    return {};
  }
}

class Pinned {
  /** Tile id → description. */
  panels = $state<Record<string, PanelSpec>>(load());

  add(tileId: string, spec: PanelSpec) {
    this.panels[tileId] = spec;
    this.save();
  }

  private save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(this.panels));
    } catch {
      /* storage unavailable: lasts for this window */
    }
  }
}

export const pinned = new Pinned();
