/**
 * The Portfolio copilot: it explains, watches and wires things in from the
 * Lab; you sign. Agents never place orders, size trades or touch the kill
 * switch, so any money change is a draft waiting for your signature.
 * Building risk systems and allocation experiments happen in the Lab.
 */
import Boxes from "@lucide/svelte/icons/boxes";
import Building2 from "@lucide/svelte/icons/building-2";
import FlaskConical from "@lucide/svelte/icons/flask-conical";
import Newspaper from "@lucide/svelte/icons/newspaper";
import type { CopilotContext } from "$lib/workbench/copilot-context";

export const PORTFOLIO_CONTEXT: CopilotContext = {
  id: "portfolio",
  tools: [
    {
      id: "pod.bring_from_lab",
      note: "Bring a tested pod or risk system from the Lab",
      group: "Pods",
      scope: "new",
    },
    {
      id: "pod.draft_version",
      note: "Draft a new pod version (you sign)",
      group: "Pods",
    },
    {
      id: "pod.from_template",
      note: "Start a pod from a template",
      group: "Pods",
    },
    {
      id: "promotion.prepare_card",
      note: "Assemble a promotion card for signing",
      group: "Road to live",
    },
    {
      id: "journal.summarise",
      note: "Summarise a bot's journal",
      group: "Road to live",
    },
    {
      id: "risk.explain",
      note: "Explain a limit, a breach or a level",
      group: "Watch",
    },
    {
      id: "news.watch",
      note: "Watch events that hit what you hold",
      group: "Watch",
    },
  ],
  defaultTools: [
    "pod.draft_version",
    "pod.from_template",
    "promotion.prepare_card",
    "risk.explain",
    "news.watch",
  ],
  targets: [
    {
      id: "pm",
      name: "Portfolio Manager",
      kind: "Quant",
      note: "Proposes pod versions from Lab results",
      blocked: null,
    },
    {
      id: "trader",
      name: "Trader",
      kind: "Quant",
      note: "Watches news windows and live state",
      blocked: null,
    },
  ],
  attach: [
    {
      id: "pod",
      label: "A pod",
      note: "Its version, limits and bots",
      icon: Boxes,
      needs: null,
    },
    {
      id: "account",
      label: "An account",
      note: "Equity, pods and kill-switch level",
      icon: Building2,
      needs: null,
    },
    {
      id: "lab",
      label: "From the Lab",
      note: "A tested pod, model or workflow",
      icon: FlaskConical,
      needs: null,
    },
    {
      id: "event",
      label: "A news item",
      note: "From the events stream",
      icon: Newspaper,
      needs: null,
    },
  ],
};

export const PORTFOLIO_SESSIONS = [
  { id: "p1", title: "Let Bybit take on Alt momentum", when: "Today" },
  { id: "p2", title: "Why is SOL near its cap?", when: "Today" },
  {
    id: "p3",
    title: "Bring the vol-target pod from the Lab",
    when: "Yesterday",
  },
];
