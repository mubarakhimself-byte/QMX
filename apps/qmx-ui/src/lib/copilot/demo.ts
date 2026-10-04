/**
 * DEMO copilot sessions, written as the blocks a session is made of, so
 * the daemon can later stream the same shapes: messages, plans, sub-agents,
 * tool calls, changes made elsewhere in QMX, artifacts, questions for you
 * and permission requests. Nothing here ran.
 */
import { DEMO_ENTITIES } from "$lib/demo/assets";
import type { Entity } from "$lib/qmx/entities";
import { SAMPLE_PANEL, type PanelSpec } from "$lib/sdk/spec";

export type Origin = "Main" | "Lab" | "Portfolio" | "Library" | "Mini apps";
export type SessionStatus = "running" | "waiting" | "done";

export type Session = {
  id: string;
  title: string;
  origin: Origin;
  status: SessionStatus;
  /** How long it has been going, or when it last moved. */
  age: string;
  agents?: number;
  pinned?: boolean;
  /** Sub-agent sessions point at the session that started them. */
  parent?: string;
};

export type StepState = "done" | "running" | "waiting" | "scheduled";
export type Block =
  | { kind: "user"; text: string; attached?: string[] }
  | { kind: "text"; text: string; demo?: boolean }
  | {
      kind: "panel";
      spec: PanelSpec;
      /** draft until you keep, discard or pin it */
      state: "draft" | "kept" | "discarded" | "pinned";
    }
  | {
      kind: "plan";
      title: string;
      steps: { text: string; state: StepState; where?: string }[];
    }
  | {
      kind: "agents";
      agents: {
        id: string;
        name: string;
        role: string;
        state: "done" | "running";
        where: string;
        last: string;
        progress?: number;
      }[];
    }
  | {
      kind: "tools";
      calls: { name: string; args: string; ms: number; ok: boolean }[];
    }
  | {
      kind: "changes";
      changes: {
        place: string;
        what: string;
        path: string;
        query?: string;
      }[];
    }
  | {
      kind: "artifact";
      id: string;
      title: string;
      type: string;
      note: string;
    }
  | {
      kind: "table";
      title: string;
      head: string[];
      rows: string[][];
    }
  | { kind: "cards"; before: Entity; after: Entity; changed: string[] }
  | {
      kind: "ask";
      question: string;
      options: { label: string; note: string; recommended?: boolean }[];
    }
  | {
      kind: "permission";
      action: string;
      detail: string;
      guard: string;
    }
  | { kind: "handoff"; from: Origin; note: string };

export const SESSIONS: Session[] = [
  {
    id: "weekend",
    title: "Weekend-safe pod, end to end",
    origin: "Main",
    status: "waiting",
    age: "2 days",
    agents: 3,
    pinned: true,
  },
  {
    id: "regime",
    title: "Regime study v3 against v1",
    origin: "Lab",
    status: "running",
    age: "3 days",
    agents: 2,
  },
  {
    id: "breakout",
    title: "BTC breakout: tighten the stop",
    origin: "Main",
    status: "done",
    age: "Today",
  },
  {
    id: "avax",
    title: "Why was the AVAX entry refused?",
    origin: "Portfolio",
    status: "done",
    age: "Today",
  },
  {
    id: "hmc",
    title: "Explain the HMC sampling article",
    origin: "Library",
    status: "done",
    age: "Yesterday",
  },
  {
    id: "news",
    title: "News sentiment as a feature",
    origin: "Mini apps",
    status: "done",
    age: "Sep 30",
  },
  {
    id: "lab-sweep",
    title: "Sweep the top coins on 1h and 4h",
    origin: "Lab",
    status: "done",
    age: "Today",
  },
  {
    id: "lab-import",
    title: "Import the vol forecaster",
    origin: "Lab",
    status: "done",
    age: "Yesterday",
  },
  {
    id: "pf-bybit",
    title: "Let Bybit take on Alt momentum",
    origin: "Portfolio",
    status: "done",
    age: "Today",
  },
  {
    id: "pf-volpod",
    title: "Bring the vol-target pod from the Lab",
    origin: "Portfolio",
    status: "done",
    age: "Yesterday",
  },
  {
    id: "weekend/tester",
    title: "Tester: replays, stress, head to head",
    origin: "Main",
    status: "running",
    age: "2 days",
    parent: "weekend",
  },
  {
    id: "weekend/builder",
    title: "Builder: writes the pod's blocks",
    origin: "Main",
    status: "done",
    age: "2 days",
    parent: "weekend",
  },
  {
    id: "weekend/reader",
    title: "Researcher: weekend liquidity",
    origin: "Main",
    status: "done",
    age: "2 days",
    parent: "weekend",
  },
];

const breakout = DEMO_ENTITIES.find((e) => e.id === "btc-breakout")!;
const tightened: Entity = {
  ...breakout,
  version: "v8 draft",
  measures: breakout.measures.map((m) =>
    m.key === "sharpe"
      ? { ...m, value: "1.31" }
      : m.key === "dd"
        ? { ...m, value: "−5.1%" }
        : m.key === "win"
          ? { ...m, value: "47%" }
          : m,
  ),
};

export const THREADS: Record<string, Block[]> = {
  "weekend/tester": [
    {
      kind: "user",
      text: "Task from the main session: replay Weekend rider and Trend rider on SOL and AVAX momentum, 2023–2025, run the stress board with FTX week and weekend thin book, then put them head to head.",
    },
    {
      kind: "tools",
      calls: [
        {
          name: "pod.test",
          args: "2 pods · 3 bots · full rerun",
          ms: 41200,
          ok: true,
        },
        {
          name: "pod.stress_scenario",
          args: "FTX week, weekend thin book",
          ms: 9800,
          ok: true,
        },
        {
          name: "pod.monte_carlo",
          args: "1,000 paths · running",
          ms: 0,
          ok: true,
        },
      ],
    },
    {
      kind: "text",
      text: "Replay and stress board done. Monte Carlo is at 640 of 1,000 paths; head to head follows when it finishes.",
    },
  ],
  "weekend/builder": [
    {
      kind: "user",
      text: "Task: copy Trend rider into a new pod and halve size from Friday 20:00 to Sunday 20:00 UTC.",
    },
    {
      kind: "tools",
      calls: [
        {
          name: "pod.edit",
          args: "copy Trend rider → Weekend rider",
          ms: 300,
          ok: true,
        },
        { name: "pod.edit", args: "add Thin hours ×0.5", ms: 210, ok: true },
      ],
    },
    { kind: "text", text: "Saved Weekend rider v1 as a draft in the Lab." },
  ],
  "weekend/reader": [
    {
      kind: "user",
      text: "Task: find what is known about crypto liquidity on weekends.",
    },
    {
      kind: "text",
      text: "Read 3 papers; 2 were useful. Weekend order books are thinner and gaps are larger after Asian Sunday sessions. Notes saved to the Library.",
    },
  ],
  "lab-sweep": [
    { kind: "handoff", from: "Lab", note: "Started in the Lab copilot." },
    {
      kind: "user",
      text: "Sweep BTC breakout across the top coins on 1h and 4h.",
    },
    {
      kind: "text",
      text: "Queued 12 cells on this laptop; 11 finished. LINK 15m has too little data. Best: SOL 4h, then BTC 1h.",
    },
  ],
  "lab-import": [
    { kind: "handoff", from: "Lab", note: "Started in the Lab copilot." },
    { kind: "user", text: "Import the vol forecaster I trained on Colab." },
    {
      kind: "text",
      text: "Imported as an ONNX model, fingerprinted, and placed in Model slots under “Risk throttle”. It needs a leakage check before use.",
    },
  ],
  "pf-bybit": [
    {
      kind: "handoff",
      from: "Portfolio",
      note: "Started in the Portfolio copilot.",
    },
    { kind: "user", text: "Should Bybit take on Alt momentum's paper side?" },
    {
      kind: "text",
      text: "Bybit is at YELLOW today, so I'd wait. The paper side can move to the Bybit testnet without touching live money; say if you want me to draft it.",
    },
  ],
  "pf-volpod": [
    {
      kind: "handoff",
      from: "Portfolio",
      note: "Started in the Portfolio copilot.",
    },
    {
      kind: "user",
      text: "Bring the vol-target pod from the Lab into Portfolio.",
    },
    {
      kind: "text",
      text: "Vol-targeted core v1 passed its paper soak. The promotion card is ready for your signature on Road to live.",
    },
  ],
  weekend: [
    {
      kind: "user",
      text: "Build me a pod that stays safe over weekends for the momentum bots. Test it on the last two years and the FTX crash, and if it holds up, put it on paper next to Trend rider.",
      attached: ["Trend rider v2", "SOL momentum", "AVAX momentum"],
    },
    {
      kind: "plan",
      title: "Plan",
      steps: [
        {
          text: "Draft “Weekend rider” from Trend rider, halving size from Friday 20:00 to Sunday 20:00 UTC",
          state: "done",
          where: "Lab",
        },
        {
          text: "Replay 2023–2025 and run the stress board, FTX included",
          state: "done",
          where: "Lab",
        },
        {
          text: "Put it head to head with Trend rider",
          state: "running",
          where: "Lab",
        },
        {
          text: "Put it on paper on a testnet (needs your yes)",
          state: "waiting",
          where: "Portfolio",
        },
        {
          text: "Watch it for 7 days; report each morning",
          state: "scheduled",
          where: "Server",
        },
      ],
    },
    {
      kind: "agents",
      agents: [
        {
          id: "builder",
          name: "Builder",
          role: "Writes the pod's blocks",
          state: "done",
          where: "This laptop",
          last: "Saved Weekend rider v1 as a draft",
        },
        {
          id: "tester",
          name: "Tester",
          role: "Replays, stress, head to head",
          state: "running",
          where: "vps-fsn",
          last: "Monte Carlo 640 of 1,000 paths",
          progress: 64,
        },
        {
          id: "reader",
          name: "Researcher",
          role: "Reads on weekend liquidity",
          state: "done",
          where: "This laptop",
          last: "3 papers, 2 useful; notes saved to the Library",
        },
      ],
    },
    {
      kind: "tools",
      calls: [
        {
          name: "pod.edit",
          args: "copy Trend rider → Weekend rider",
          ms: 300,
          ok: true,
        },
        {
          name: "pod.edit",
          args: "add Thin hours ×0.5, Fri 20:00–Sun 20:00",
          ms: 210,
          ok: true,
        },
        {
          name: "pod.test",
          args: "3 bots · 2023–2025 · full rerun",
          ms: 41200,
          ok: true,
        },
        {
          name: "pod.stress_scenario",
          args: "FTX week, weekend thin book",
          ms: 9800,
          ok: true,
        },
      ],
    },
    {
      kind: "changes",
      changes: [
        {
          place: "Lab",
          what: "New pod draft: Weekend rider v1",
          path: "/lab",
          query: "layout=pod-design",
        },
        {
          place: "Lab",
          what: "Stress board: 2 scenarios run",
          path: "/lab",
          query: "layout=pod-test",
        },
        {
          place: "Library",
          what: "Notes on weekend liquidity (3 papers)",
          path: "/library",
          query: "shelf=articles",
        },
      ],
    },
    {
      kind: "text",
      text: "So far it holds up. Weekend rider gives up about $380 of profit over two years, but its worst weekend falls from −$1,240 to −$560, and the FTX week costs $1,100 instead of $2,200. Head to head is still running on the server.",
    },
    {
      kind: "artifact",
      id: "art-h2h",
      title: "Weekend rider against Trend rider",
      type: "Interactive report",
      note: "Equity, worst weekends and the stress board, side by side",
    },
    {
      kind: "ask",
      question: "Which paper money should it soak on?",
      options: [
        {
          label: "Binance testnet",
          note: "Real exchange rules, test money. Trend rider is there too.",
          recommended: true,
        },
        {
          label: "Node paper ledger",
          note: "Any exchange; fills simulated on live prices.",
        },
        { label: "Bybit testnet", note: "Real exchange rules, test money." },
      ],
    },
    {
      kind: "permission",
      action: "Put Weekend rider v1 on paper",
      detail:
        "Drafts the wiring (bots, testnet account, $10,000 paper money) for your signature, then starts a 7-day soak.",
      guard: "Paper only. Real money always needs your signature in Portfolio.",
    },
  ],
  regime: [
    {
      kind: "handoff",
      from: "Lab",
      note: "Started in the Lab copilot. Continue it here and the main copilot takes over with everything it can reach.",
    },
    {
      kind: "user",
      text: "Compare regime study v3 with v1 on 2022–2025 and tell me which labels hold up out of sample.",
      attached: ["Market regime HMM v2", "Regime study v3"],
    },
    {
      kind: "agents",
      agents: [
        {
          id: "trainer",
          name: "Trainer",
          role: "Refits both versions walk-forward",
          state: "running",
          where: "colab",
          last: "Fold 9 of 12",
          progress: 75,
        },
        {
          id: "checker",
          name: "Checker",
          role: "Leakage and stability checks",
          state: "running",
          where: "vps-fsn",
          last: "Purge and embargo pass on folds 1–8",
          progress: 66,
        },
      ],
    },
    {
      kind: "text",
      text: "v3's “stressed” label is more stable (it lasts 9 days on average against 4), but v1 separates calm trends better. I'll have the full comparison when fold 12 finishes, about 40 minutes from now.",
    },
  ],
  breakout: [
    {
      kind: "user",
      text: "Backtest BTC breakout on 2024–2026 and compare it with simply holding BTC.",
      attached: ["BTC breakout v7"],
    },
    {
      kind: "tools",
      calls: [
        {
          name: "get_candles",
          args: "BTCUSDT · 1h · 2024–2026",
          ms: 420,
          ok: true,
        },
        {
          name: "run_backtest",
          args: "btc-breakout v7 · draft",
          ms: 8100,
          ok: true,
        },
        { name: "compare_benchmark", args: "buy and hold", ms: 260, ok: true },
      ],
    },
    {
      kind: "text",
      text: "The strategy beat holding BTC with well under half the drawdown. Most of the edge came from breakouts at the Asia-to-Europe handover; the 2025 summer chop is its worst losing streak.",
    },
    {
      kind: "table",
      title: "BTC breakout against holding BTC",
      head: ["Measure", "Strategy", "Hold BTC"],
      rows: [
        ["Net return", "+18.4%", "+31.0%"],
        ["Sharpe", "1.42", "0.88"],
        ["Max drawdown", "−6.8%", "−27.9%"],
        ["Trades", "187", "1"],
        ["Win rate", "54.1%", "—"],
      ],
    },
    {
      kind: "user",
      text: "Tighten the stop to 0.8 ATR and show me what changes.",
    },
    {
      kind: "text",
      text: "With a 0.8 ATR stop the drawdown falls but more trades get stopped out early. This is a draft; it becomes evidence only after you publish and re-run it.",
    },
    {
      kind: "cards",
      before: breakout,
      after: tightened,
      changed: ["sharpe", "dd", "win"],
    },
  ],
  avax: [
    {
      kind: "handoff",
      from: "Portfolio",
      note: "Started in the Portfolio copilot.",
    },
    { kind: "user", text: "Why was the AVAX entry refused this morning?" },
    {
      kind: "text",
      text: "Trend rider's volatility-spike throttle refused it: AVAX's 15-minute volatility was 3.1 times its usual level at 10:12, above the 3× limit. Nothing was wrong; the pod did what it was built to do.",
    },
    {
      kind: "changes",
      changes: [
        {
          place: "Lab",
          what: "See it in Trend rider's live decisions",
          path: "/lab",
          query: "layout=pod-paper",
        },
      ],
    },
  ],
  hmc: [
    {
      kind: "handoff",
      from: "Library",
      note: "Started from an article in the Library.",
    },
    {
      kind: "user",
      text: "Explain this article in plain words, then list the claims I could test.",
      attached: [
        "Markov Chain Monte Carlo Sampling Methods: The HMC Algorithm",
      ],
    },
    {
      kind: "text",
      text: "HMC moves through possible answers in long, guided steps instead of small random ones, so it explores big models faster. Claims you could test: it needs fewer samples than random-walk sampling for the same accuracy; its step size can tune itself during warm-up.",
    },
  ],
  news: [
    {
      kind: "handoff",
      from: "Mini apps",
      note: "Started in News & sentiment.",
    },
    {
      kind: "user",
      text: "Can sentiment be a feature for the breakout scorer?",
    },
    {
      kind: "text",
      text: "Yes, as a daily score per coin, lagged by one day so it never sees the future. I added it to Saved setups as “News sentiment”; it needs a retrain to test.",
    },
  ],
};

/** Background work across every session, for the Activity tab. */
export const TASKS = [
  {
    id: "t-h2h",
    name: "Pod test: Weekend rider against Trend rider",
    session: "weekend",
    where: "vps-fsn",
    state: "running" as const,
    progress: 64,
    log: [
      "replay 2023-01 → 2025-12 · 3 bots · 2 pods",
      "fills simulated with Binance fees and lot sizes",
      "monte carlo: 640 / 1000 paths",
    ],
  },
  {
    id: "t-wf",
    name: "Walk-forward: regime v3 and v1",
    session: "regime",
    where: "colab",
    state: "running" as const,
    progress: 75,
    log: ["fold 9/12 fitting", "GPU T4 · 41% busy"],
  },
  {
    id: "t-sweep",
    name: "Sweep: BTC breakout, 6 coins × 4 timeframes",
    session: "breakout",
    where: "This laptop",
    state: "running" as const,
    progress: 75,
    log: ["18 / 24 cells done", "LINK 15m failed: not enough data"],
  },
  {
    id: "t-watch",
    name: "Paper watch: Weekend rider, 7 days",
    session: "weekend",
    where: "Tokyo",
    state: "waiting" as const,
    progress: 0,
    log: ["starts after you sign the paper wiring"],
  },
  {
    id: "t-nightly",
    name: "Nightly evidence (schedule)",
    session: null,
    where: "vps-fsn",
    state: "scheduled" as const,
    progress: 0,
    log: ["next run 02:00 UTC"],
  },
];

/** Things the copilot made, across sessions. */
export const ARTIFACTS: {
  id: string;
  title: string;
  type: string;
  session: string;
  spec?: PanelSpec;
}[] = [
  {
    id: "art-h2h",
    title: "Weekend rider against Trend rider",
    type: "Interactive report",
    session: "weekend",
    spec: SAMPLE_PANEL,
  },
  {
    id: "art-notes",
    title: "Weekend liquidity: notes from 3 papers",
    type: "Notes",
    session: "weekend",
  },
  {
    id: "art-hmc",
    title: "HMC in plain words",
    type: "Explainer",
    session: "hmc",
  },
];

/** Slash commands: shortcuts for things the copilot does often. */
export const COMMANDS = [
  { cmd: "/backtest", note: "Test a bot on a period" },
  { cmd: "/sweep", note: "Markets × timeframes × settings" },
  { cmd: "/pod", note: "Build or change a pod" },
  { cmd: "/stress", note: "Make a stress scenario" },
  { cmd: "/paper", note: "Put something on paper (asks you first)" },
  { cmd: "/explain", note: "Explain an article or result your way" },
  { cmd: "/schedule", note: "Run something on a server on a timer" },
  { cmd: "/panel", note: "Build a new panel for any screen" },
  { cmd: "/help", note: "How do I…?" },
];

/** What “How do I…” offers on a new session. */
export const HOW_DO_I = [
  {
    q: "Train something new",
    start: "train",
    note: "A model, step by step",
  },
  {
    q: "Bring in outside work",
    start: "import",
    note: "Code, a notebook or a model",
  },
  {
    q: "Build a workflow",
    start: "workflow",
    note: "Steps that run on a timer",
  },
  {
    q: "Build a pod",
    ask: "Help me build a pod: ask me what I want it to protect against.",
    note: "Risk and sizing for some bots",
  },
  {
    q: "Make sense of an article",
    ask: "Explain the article I attach in plain words and list what I could test.",
    note: "Plain words, diagram or video",
  },
  {
    q: "Watch something while I'm away",
    ask: "Set up a server job that watches my paper pods and messages me if anything drifts.",
    note: "Runs on a server, not this laptop",
  },
];
