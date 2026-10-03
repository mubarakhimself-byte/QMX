/**
 * Kill switch by scope (operator, 2026-10-03: "combine kill switch per
 * server or per pod"). A scope is everything, one server, one pod, or one
 * pod on one server. What a cell does is the strictest of the scopes above
 * it. The docs allow flatten at any scope (DEC-0150); stopping new trades or
 * halting a whole pod or server is not yet on the node's powers list, so
 * those are flagged for the backend. Demo state only; nothing reaches a node.
 */
import { accountById, type Pod } from "./demo";

export type KillState = "active" | "no-new" | "halted";
export const KILL_ORDER: KillState[] = ["active", "no-new", "halted"];
export const KILL_LABEL: Record<KillState, string> = {
  active: "Trading",
  "no-new": "No new trades",
  halted: "Halted",
};

/** Which side of a pod runs on a server, and how many bots. */
export type Cell = { side: "live" | "paper"; bots: number }[];

export function cellFor(pod: Pod, node: string): Cell {
  const out: Cell = [];
  if (pod.mode === "LIVE" && accountById(pod.account)?.node === node)
    out.push({ side: "live", bots: pod.bots.length });
  if (accountById(pod.paper.account)?.node === node)
    out.push({ side: "paper", bots: pod.bots.length });
  return out;
}

export const scopeKey = {
  all: "all",
  node: (n: string) => `node:${n}`,
  pod: (p: string) => `pod:${p}`,
  cell: (p: string, n: string) => `cell:${p}:${n}`,
};

class KillSwitch {
  states = $state<Record<string, KillState>>({});

  stateOf(key: string): KillState {
    return this.states[key] ?? "active";
  }

  /** The strictest state that applies to one pod on one server. */
  effective(pod: string, node: string): KillState {
    const keys = [
      scopeKey.all,
      scopeKey.node(node),
      scopeKey.pod(pod),
      scopeKey.cell(pod, node),
    ];
    return keys
      .map((k) => this.stateOf(k))
      .reduce((a, b) =>
        KILL_ORDER.indexOf(b) > KILL_ORDER.indexOf(a) ? b : a,
      );
  }

  set(key: string, state: KillState) {
    if (state === "active") delete this.states[key];
    else this.states[key] = state;
  }

  /** Scopes not trading, for the header chip. */
  get raised(): number {
    return Object.keys(this.states).length;
  }

  get worst(): KillState {
    return Object.values(this.states).reduce<KillState>(
      (a, b) => (KILL_ORDER.indexOf(b) > KILL_ORDER.indexOf(a) ? b : a),
      "active",
    );
  }
}

export const kill = new KillSwitch();
