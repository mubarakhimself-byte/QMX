/**
 * Everything that needs you, gathered from every screen: copilot questions
 * and approvals, promotion cards to sign, paper runs ready for live, kill
 * switch levels raised, failed runs. Home's inbox and the bell share it.
 */
import { ACCOUNTS, CANDIDATES } from "$lib/portfolio/demo";
import { LAB_PODS, PAPER_RUNS } from "$lib/lab/pods";
import { copilot } from "$lib/copilot/store.svelte";

export type Need = {
  id: string;
  kind: "Copilot" | "Sign" | "Paper" | "Risk" | "Run";
  title: string;
  why: string;
  path: string;
  query?: string;
  tone: "warning" | "info" | "destructive";
};

export function needs(): Need[] {
  const out: Need[] = [];
  for (const s of copilot.sessions) {
    const p = copilot.pending(s.id);
    if (!p) continue;
    out.push({
      id: `cp-${s.id}`,
      kind: "Copilot",
      title:
        p.block.kind === "ask"
          ? p.block.question
          : p.block.kind === "permission"
            ? `Needs your yes: ${p.block.action}`
            : s.title,
      why: s.title,
      path: "/copilot",
      query: `session=${s.id}`,
      tone: "warning",
    });
  }
  for (const c of CANDIDATES.filter((c) => c.stage === "ready"))
    out.push({
      id: `sign-${c.entity.id}`,
      kind: "Sign",
      title: `Sign ${c.entity.name} for live`,
      why: `${c.days} days on paper; every check passed`,
      path: "/portfolio",
      query: "layout=road",
      tone: "info",
    });
  for (const r of PAPER_RUNS.filter((r) => r.verdict === "ready")) {
    const pod = LAB_PODS.find((p) => p.id === r.pod);
    out.push({
      id: `paper-${r.pod}`,
      kind: "Paper",
      title: `${pod?.name} ${r.version} is ready for live`,
      why: `Soaked ${r.day} days on ${r.money}`,
      path: "/lab",
      query: "layout=pod-paper",
      tone: "info",
    });
  }
  for (const a of ACCOUNTS.filter(
    (a) => a.role !== "watch" && a.ksa !== "GREEN",
  ))
    out.push({
      id: `ksa-${a.id}`,
      kind: "Risk",
      title: `${a.name} kill switch at ${a.ksa}`,
      why: "Sizes are reduced until it comes back down",
      path: "/portfolio",
      query: "layout=live",
      tone: "destructive",
    });
  out.push({
    id: "run-link",
    kind: "Run",
    title: "USOIL 15m sweep cell failed",
    why: "Not enough data before 2021",
    path: "/lab",
    query: "layout=test",
    tone: "warning",
  });
  return out;
}
