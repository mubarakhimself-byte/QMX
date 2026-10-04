/**
 * One store for every copilot session: the main copilot and the Lab and
 * Portfolio side copilots read and write the same sessions, so a side
 * conversation can be continued in the main copilot by its id. A session is
 * an append-only list of blocks (the DeepSeek Harness rule: what the UI
 * shows is what the log holds). Answers to question and permission cards are
 * kept here too, so the composer can take over while one is pending.
 *
 * DEMO: replies come from a scripted responder, clearly labelled. The daemon
 * (LangGraph) streams the same block shapes once wired.
 */
import { SAMPLE_PANEL } from "$lib/sdk/spec";
import {
  SESSIONS,
  THREADS,
  type Block,
  type Origin,
  type Session,
} from "./demo";

const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T;
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

class CopilotStore {
  sessions = $state<Session[]>(clone(SESSIONS));
  threads = $state<Record<string, Block[]>>(clone(THREADS));
  /** Answers by session and block index. */
  answers = $state<Record<string, Record<number, string>>>({});
  busy = $state<Record<string, boolean>>({});

  session(id: string | null) {
    return this.sessions.find((s) => s.id === id);
  }
  blocks(id: string | null): Block[] {
    return id ? (this.threads[id] ?? []) : [];
  }
  childrenOf(id: string) {
    return this.sessions.filter((s) => s.parent === id);
  }

  /** The first question or permission card still waiting for you. */
  pending(id: string | null): { index: number; block: Block } | null {
    if (!id) return null;
    const blocks = this.blocks(id);
    for (let i = 0; i < blocks.length; i++) {
      const b = blocks[i];
      if (
        (b.kind === "ask" || b.kind === "permission") &&
        !this.answers[id]?.[i]
      )
        return { index: i, block: b };
    }
    return null;
  }

  answer(id: string, index: number, value: string) {
    this.answers[id] = { ...(this.answers[id] ?? {}), [index]: value };
    if (!this.pending(id)) {
      const s = this.session(id);
      if (s?.status === "waiting") s.status = "running";
    }
  }

  create(origin: Origin, title = "New session"): string {
    const id = `n-${Date.now().toString(36)}`;
    this.sessions = [
      { id, title, origin, status: "done", age: "Now" },
      ...this.sessions,
    ];
    this.threads[id] = [];
    return id;
  }

  /** Move a side conversation into the main copilot (it keeps its history). */
  absorb(id: string) {
    const s = this.session(id);
    if (!s || s.origin === "Main") return;
    s.origin = "Main";
    this.threads[id] = [
      ...this.blocks(id),
      {
        kind: "text",
        text: "Now in the main copilot: everything it can reach is open to this conversation.",
      },
    ];
  }

  private push(id: string, b: Block) {
    this.threads[id] = [...this.blocks(id), b];
  }

  /** Send a message; the demo responder streams a reply. */
  async send(id: string, text: string, attached: string[] = []) {
    const s = this.session(id);
    if (!s || this.busy[id]) return;
    this.push(id, {
      kind: "user",
      text,
      attached: attached.length ? attached : undefined,
    });
    if (s.title === "New session")
      s.title = text.length > 48 ? `${text.slice(0, 46)}…` : text;
    s.age = "Now";
    s.status = "running";
    this.busy[id] = true;
    await wait(500);

    const wantsPanel =
      /^\/panel|panel|widget|dashboard|show me/i.test(text) ||
      /build .*(screen|view)/i.test(text);
    this.push(id, {
      kind: "tools",
      calls: wantsPanel
        ? [
            {
              name: "library.search",
              args: "pods, weekend tests",
              ms: 180,
              ok: true,
            },
            {
              name: "pod.test.weekend_breakdown",
              args: "Trend rider, Weekend rider",
              ms: 640,
              ok: true,
            },
            {
              name: "ui.propose_panel",
              args: "catalog: Grid, Metric, LineChart, Table",
              ms: 220,
              ok: true,
            },
          ]
        : [
            {
              name: "library.search",
              args: text.slice(0, 40),
              ms: 210,
              ok: true,
            },
          ],
    });
    await wait(400);

    const reply = wantsPanel
      ? "Here is a draft panel. It is a description QMX drew with its own parts, so it can't break anything. Keep it, throw it away, or pin it to a Lab layout."
      : "This is a scripted demo reply: no model is connected yet. With the daemon, the copilot would answer here, using the tools and places you allowed in the mode-and-reach menu.";
    const idx = this.blocks(id).length;
    this.push(id, { kind: "text", text: "", demo: true });
    for (let i = 0; i <= reply.length; i += 6) {
      const blocks = [...this.blocks(id)];
      blocks[idx] = { kind: "text", text: reply.slice(0, i), demo: true };
      this.threads[id] = blocks;
      await wait(18);
    }
    const blocks = [...this.blocks(id)];
    blocks[idx] = { kind: "text", text: reply, demo: true };
    this.threads[id] = blocks;
    if (wantsPanel)
      this.push(id, {
        kind: "panel",
        spec: clone(SAMPLE_PANEL),
        state: "draft",
      });

    this.busy[id] = false;
    s.status = "done";
  }

  setPanel(id: string, index: number, state: "kept" | "discarded" | "pinned") {
    const blocks = [...this.blocks(id)];
    const b = blocks[index];
    if (b?.kind === "panel") blocks[index] = { ...b, state };
    this.threads[id] = blocks;
  }
}

export const copilot = new CopilotStore();
