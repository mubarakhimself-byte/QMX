/**
 * The Portfolio copilot: it drafts, explains and proposes; you sign. Agents
 * never place orders, size trades or touch the kill switch, so every money
 * change it makes is a draft version waiting for your signature.
 */
import BookOpen from "@lucide/svelte/icons/book-open";
import Building2 from "@lucide/svelte/icons/building-2";
import FlaskConical from "@lucide/svelte/icons/flask-conical";
import Newspaper from "@lucide/svelte/icons/newspaper";
import type { CopilotContext } from "$lib/workbench/copilot-context";

export const PORTFOLIO_CONTEXT: CopilotContext = {
  id: "portfolio",
  tools: [
    {
      id: "book.draft_version",
      note: "Draft a new Book version (you sign)",
      group: "Books",
    },
    {
      id: "book.from_template",
      note: "Start a Book from a template",
      group: "Books",
    },
    {
      id: "book.attach_engine",
      note: "Use a model or Lab workflow for risk",
      group: "Books",
      scope: "new",
    },
    {
      id: "allocation.propose",
      note: "Propose an allocation across Books",
      group: "Allocate",
      scope: "new",
    },
    {
      id: "allocation.what_if",
      note: "Replay a what-if allocation",
      group: "Allocate",
      scope: "new",
    },
    {
      id: "promotion.prepare_card",
      note: "Assemble a promotion card for signing",
      group: "Promote",
    },
    {
      id: "risk.explain",
      note: "Explain a limit, a breach or a level",
      group: "Risk",
    },
    {
      id: "news.watch",
      note: "Watch events that hit what you hold",
      group: "Risk",
    },
  ],
  defaultTools: [
    "book.draft_version",
    "book.from_template",
    "promotion.prepare_card",
    "risk.explain",
    "news.watch",
  ],
  targets: [
    {
      id: "pm",
      name: "Portfolio Manager",
      kind: "Quant",
      note: "Proposes Book versions and allocations",
      blocked: null,
    },
    {
      id: "trader",
      name: "Trader",
      kind: "Quant",
      note: "Watches news windows and live state",
      blocked: null,
    },
    {
      id: "analyst",
      name: "Analyst",
      kind: "Quant",
      note: "Pulls evidence from the Lab",
      blocked: null,
    },
  ],
  attach: [
    {
      id: "book",
      label: "A Book",
      note: "Its version, rules and seats",
      icon: BookOpen,
      needs: null,
    },
    {
      id: "account",
      label: "An account",
      note: "Equity, Books and kill-switch level",
      icon: Building2,
      needs: null,
    },
    {
      id: "lab",
      label: "From the Lab",
      note: "A run, model or workflow",
      icon: FlaskConical,
      needs: null,
    },
    {
      id: "event",
      label: "An event",
      note: "From the calendar or news",
      icon: Newspaper,
      needs: null,
    },
  ],
};

export const PORTFOLIO_SESSIONS = [
  { id: "p1", title: "Let Binance take on Crypto momentum", when: "Today" },
  { id: "p2", title: "Why is the prop book near its limit?", when: "Today" },
  { id: "p3", title: "Rules vs the vol model for sizing", when: "Yesterday" },
];
