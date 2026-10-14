<script lang="ts">
  /**
   * A pod soaking on paper (operator, 2026-10-03: new risk and sizing
   * systems go through paper before money). Paper money, live prices. The
   * shaded band is what the pod's own test said to expect; the line is what
   * paper has done so far. Pause, resume and extend act on the run (demo).
   */
  import Pause from "@lucide/svelte/icons/pause";
  import Play from "@lucide/svelte/icons/play";
  import CalendarPlus from "@lucide/svelte/icons/calendar-plus";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, PAPER_RUNS } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const run = $derived(podModel.paper(lab.labPod));
  const pod = $derived(LAB_PODS.find((p) => p.id === run.pod)!);
  const verdict = $derived(
    run.stopped
      ? { text: "Stopped", tone: "text-muted-foreground" }
      : run.paused
        ? { text: "Paused", tone: "text-warning" }
        : run.ready
          ? { text: "Soak done: ready for live", tone: "text-success" }
          : run.verdict === "drifting"
            ? { text: "Drifting from its test", tone: "text-warning" }
            : { text: "Behaving as tested", tone: "text-success" },
  );

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

  function togglePause() {
    const pausing = !run.paused;
    podModel.paperPaused[run.pod] = pausing;
    workbench.notify(
      `${pod.name}'s paper run ${pausing ? "paused: no new paper trades" : "resumed"}.`,
    );
  }
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={`${pod.name} on paper`}
    value={`Day ${run.day} of ${run.of}`}
    status={verdict.text}
    tone={run.paused ? "warn" : run.stopped ? "muted" : "good"}
    values={run.equity}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-1">
      {#each PAPER_RUNS as r (r.pod)}
        {@const p = LAB_PODS.find((q) => q.id === r.pod)!}
        <button
          type="button"
          class={cn(
            "flex h-7 min-w-0 items-center gap-1.5 rounded-md px-2.5 text-sm",
            run.pod === r.pod
              ? "bg-muted font-medium"
              : "text-muted-foreground hover:text-foreground",
          )}
          aria-pressed={run.pod === r.pod}
          onclick={() => (lab.labPod = r.pod)}
          ><span
            class="size-2 shrink-0 rounded-full"
            style="background:{p.color}"
          ></span><span class="truncate">{p.name}</span></button
        >
      {/each}
      <span class="ml-auto flex shrink-0 items-center gap-1">
        <Button
          size="sm"
          variant={run.paused ? "default" : "outline"}
          disabled={run.stopped}
          aria-label={run.paused ? "Resume paper run" : "Pause paper run"}
          onclick={togglePause}
          >{#if run.paused}<Play /><span class="hidden @lg:inline">Resume</span
            >{:else}<Pause /><span class="hidden @lg:inline">Pause</span
            >{/if}</Button
        >
        <Button
          size="sm"
          variant="ghost"
          disabled={run.stopped}
          aria-label="Extend soak by 7 days"
          title="Extend soak by 7 days"
          onclick={() => {
            podModel.paperExtra[run.pod] =
              (podModel.paperExtra[run.pod] ?? 0) + 7;
            workbench.notify(`${pod.name} soaks 7 more days.`);
          }}
          ><CalendarPlus /><span class="hidden @2xl:inline">+7 days</span
          ></Button
        >
      </span>
    </div>

    <div class="px-panel flex shrink-0 flex-wrap items-end gap-x-6 gap-y-2">
      <div class="min-w-0">
        <p class={cn("text-lg font-semibold", verdict.tone)}>
          {verdict.text}
        </p>
        <p class="text-muted-foreground truncate text-xs">
          {run.version} · {run.money} · {run.server}
        </p>
      </div>
      <div class="ml-auto">
        <p class="text-muted-foreground num mb-1 text-right text-xs">
          Day {run.day} of {run.of}
        </p>
        <div class="flex gap-0.5" aria-label={`Day ${run.day} of ${run.of}`}>
          {#each Array.from({ length: Math.max(run.of, run.day) }, (_, i) => i) as i (i)}
            <span
              class={cn("h-2 w-3 rounded-sm", i >= run.day && "bg-muted")}
              style={i < run.day ? "background: var(--tone-paper)" : ""}
            ></span>
          {/each}
        </div>
      </div>
    </div>

    <div class="p-panel min-h-0 flex-1">
      <div class="solid-backing relative h-full rounded-md">
        <svg
          viewBox="0 0 {W} {H}"
          preserveAspectRatio="none"
          class={cn("h-full min-h-20 w-full", run.stopped && "opacity-40")}
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
        <InfoTip
          class="absolute top-1 right-1"
          label="Explain the paper chart"
          text="The line is paper equity so far, on paper money and live prices. The shaded band is what the pod's own test said to expect; staying inside it is the point. The dashed line is today."
        />
      </div>
    </div>
  </div>
{/if}
