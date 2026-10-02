/**
 * What a copilot can use depends on where it lives. Each surface (the main
 * copilot, the Lab, a mini app) declares its own tools, who a message can be
 * aimed at, and where attachments come from. A surface that needs no
 * attachments or targets says so with null, and the composer hides them.
 * Tool and target lists come from the daemon's registries once wired.
 */
import type { Component } from "svelte";
import LibraryBig from "@lucide/svelte/icons/library-big";
import Upload from "@lucide/svelte/icons/upload";
import { TARGETS, TOOLS } from "./workbench.svelte";

export type CopilotTool = {
  id: string;
  note: string;
  group?: string;
  scope?: "new";
};
export type CopilotTarget = {
  id: string;
  name: string;
  kind: string;
  note: string;
  /** Plain reason it can't take messages right now, or null when ready. */
  blocked: string | null;
};
export type AttachSource = {
  id: string;
  label: string;
  note?: string;
  icon: Component;
  /** Plain reason it needs the daemon, or null when it works now. */
  needs: string | null;
  href?: string;
};

export type CopilotContext = {
  id: string;
  tools: CopilotTool[];
  defaultTools: string[];
  targets: CopilotTarget[] | null;
  attach: AttachSource[] | null;
};

const AXES = [
  "published",
  "configured",
  "granted",
  "reachable",
  "healthy",
] as const;

export const MAIN_CONTEXT: CopilotContext = {
  id: "main",
  tools: TOOLS.map((t) => ({ id: t.id, note: t.note })),
  defaultTools: ["get_candles", "run_backtest", "library.search"],
  targets: TARGETS.map((t) => {
    const missing = AXES.find((a) => !t.axes[a]);
    return {
      id: t.id,
      name: t.name,
      kind: t.kind,
      note: t.ops.join(" · "),
      blocked: missing ? `not ${missing}` : null,
    };
  }),
  attach: [
    {
      id: "library",
      label: "From Library…",
      icon: LibraryBig,
      needs: null,
      href: "/library",
    },
    {
      id: "upload",
      label: "Upload a file",
      icon: Upload,
      needs: "needs daemon",
    },
  ],
};
