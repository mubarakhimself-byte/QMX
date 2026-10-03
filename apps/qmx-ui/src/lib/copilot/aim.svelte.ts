/**
 * "Aim this message at", rethought (operator, 2026-10-03): three plain
 * questions instead of a target list. How much may it do (Ask, Plan, Do)?
 * Which parts of QMX may it touch (its reach)? And who answers (the main
 * copilot, a screen's copilot, a mini app, or one of its running agents)?
 * Real money is never in reach: it always needs your signature.
 */
export type Mode = "ask" | "plan" | "do";
export const MODES: { id: Mode; label: string; note: string }[] = [
  { id: "ask", label: "Ask", note: "Answers and explains; changes nothing" },
  {
    id: "plan",
    label: "Plan",
    note: "Writes a plan; you approve it before anything changes",
  },
  {
    id: "do",
    label: "Do",
    note: "Acts inside its reach; asks before anything it can't undo",
  },
];

export const REACH = [
  { id: "lab", label: "Lab", note: "Build, test, train, pods" },
  { id: "portfolio", label: "Portfolio (paper)", note: "Paper sides, layouts" },
  { id: "library", label: "Library", note: "Read and save items" },
  { id: "apps", label: "Mini apps", note: "Run their operations" },
  { id: "servers", label: "Servers", note: "Start jobs and schedules" },
  { id: "settings", label: "Settings", note: "Themes, layouts, models" },
] as const;

export const ANSWERERS = [
  { id: "main", label: "Main copilot", note: "Reaches everything you allow" },
  { id: "lab", label: "Lab copilot", note: "Lab tools only" },
  { id: "portfolio", label: "Portfolio copilot", note: "Portfolio tools only" },
  { id: "research", label: "Research · Crypto", note: "A mini app's copilot" },
  {
    id: "tester",
    label: "Tester (running agent)",
    note: "Weekend-safe pod session",
  },
] as const;

class Aim {
  mode = $state<Mode>("do");
  reach = $state<string[]>(["lab", "portfolio", "library", "servers"]);
  answerer = $state<string>("main");

  toggle(id: string) {
    this.reach = this.reach.includes(id)
      ? this.reach.filter((r) => r !== id)
      : [...this.reach, id];
  }
}

export const aim = new Aim();
