<script lang="ts">
  /**
   * A pod soaking on paper (operator, 2026-10-03: new risk and sizing
   * systems go through paper before money). Paper money, live prices. The
   * shaded band is what the pod's own test said to expect; the line is what
   * paper has done so far. Staying inside the band is the point.
   */
  import { cn } from "$lib/utils";
  import { LAB_PODS, PAPER_RUNS } from "../pods";
  import { lab } from "../lab.svelte";

  const run = $derived(
    PAPER_RUNS.find((r) => r.pod === lab.labPod) ?? PAPER_RUNS[0],
  );
  const pod = $derived(LAB_PODS.find((p) => p.id === run.pod)!);
  const VERDICT = {
    "as-tested": { text: "Behaving as tested", tone: "text-success" },
    drifting: { text: "Drifting from its test", tone: "text-warning" },
    ready: { text: "Soak done: ready for live", tone: "text-success" },
  };

  const W = 600;
  const H = 200;
  const n = $derived(run.p5.length);
  const lo = $derived(Math.min(...run.p5, ...run.equity));
  const hi = $derived(Math.max(...run.p95, ...run.equity));
  const x = (i: number) => (i / (n - 1)) * W;
  const y = (v: number) => H - ((v - lo) / (hi - lo || 1)) * H;
  const bandPath = $derived(
    `M${run.p95.map((v, i) => `${x(i)},${y(v)}`).join("L")}L${[...run.p5]
      .map((v, i) => [i, v] as const)
      .reverse()
      .map(([i, v]) => `${x(i)},${y(v)}`)
      .join("L")}Z`,
  );
  const linePath = $derived(
    `M${run.equity.map((v, i) => `${x(i)},${y(v)}`).join("L")}`,
  );
  const today = $derived(x(run.equity.length - 1));
</script>

<div class="flex h-full flex-col">
  <div class="flex h-10 shrink-0 items-center gap-1 border-b px-2">
    {#each PAPER_RUNS as r (r.pod)}
      {@const p = LAB_PODS.find((q) => q.id === r.pod)!}
      <button
        type="button"
        class={cn(
          "flex h-7 items-center gap-1.5 rounded-md px-2.5 text-sm",
          run.pod === r.pod
            ? "bg-muted font-medium"
            : "text-muted-foreground hover:text-foreground",
        )}
        aria-pressed={run.pod === r.pod}
        onclick={() => (lab.labPod = r.pod)}
        ><span class="size-2 rounded-full" style="background:{p.color}"
        ></span>{p.name}
        <span class="text-muted-foreground num text-xs"
          >{r.version} · day {r.day}</span
        ></button
      >
    {/each}
  </div>

  <div class="flex shrink-0 flex-wrap items-end gap-x-6 gap-y-2 px-3 pt-3">
    <div>
      <p class={cn("text-lg font-semibold", VERDICT[run.verdict].tone)}>
        {VERDICT[run.verdict].text}
      </p>
      <p class="text-muted-foreground text-xs">
        {pod.name}
        {run.version} on {run.money} · runs on {run.server} · since {run.started}
      </p>
    </div>
    <div class="ml-auto">
      <p class="text-muted-foreground mb-1 text-right text-xs">
        Soak day {run.day} of {run.of}
      </p>
      <div class="flex gap-1" aria-label={`Day ${run.day} of ${run.of}`}>
        {#each Array.from({ length: Math.max(run.of, run.day) }, (_, i) => i) as i (i)}
          <span
            class={cn("h-2 w-5 rounded-sm", i >= run.day && "bg-muted")}
            style={i < run.day ? "background: var(--tone-paper)" : ""}
          ></span>
        {/each}
      </div>
    </div>
  </div>

  <div class="min-h-0 flex-1 p-3">
    <div class="solid-backing flex h-full flex-col rounded-md">
      <svg
        viewBox="0 0 {W} {H}"
        preserveAspectRatio="none"
        class="min-h-24 w-full flex-1"
        role="img"
        aria-label="Paper equity against the band its test expected"
      >
        <path d={bandPath} fill={pod.color} opacity="0.16" />
        <line
          x1={today}
          x2={today}
          y1="0"
          y2={H}
          stroke="var(--muted-foreground)"
          stroke-opacity="0.6"
          stroke-dasharray="4 4"
          vector-effect="non-scaling-stroke"
        />
        <path
          d={linePath}
          fill="none"
          stroke="var(--tone-paper)"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        />
      </svg>
      <div class="text-muted-foreground flex gap-4 px-2 pb-1.5 text-xs">
        <span class="flex items-center gap-1.5"
          ><span class="h-0.5 w-4" style="background: var(--tone-paper)"
          ></span>Paper so far</span
        >
        <span class="flex items-center gap-1.5"
          ><span
            class="h-2.5 w-4 rounded-sm opacity-40"
            style="background:{pod.color}"
          ></span>What its test expected</span
        >
        <span class="ml-auto">Dashed line: today</span>
      </div>
    </div>
  </div>
</div>
