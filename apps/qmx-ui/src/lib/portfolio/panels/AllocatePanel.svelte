<script lang="ts">
  /**
   * Allocation what-if (new scope: the docs have no allocation across Books,
   * DEC-0154/0435). Pick an objective and limits, see the frontier with where
   * you are, and weights now against proposed. Applying a proposal drafts new
   * Book versions for you to sign; nothing moves money from here.
   */
  import { Button } from "$lib/components/ui/button";
  import { Slider } from "$lib/components/ui/slider";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ALLOC } from "../demo";

  const OBJECTIVES = [
    "Equal risk",
    "Max Sharpe",
    "Min drawdown",
    "Grow one account",
    "Your own…",
  ];
  let objective = $state("Equal risk");
  let cap = $state(35);
  let turnover = $state(15);

  // Frontier points (risk %, return %) and where today's mix sits.
  const FRONTIER = Array.from({ length: 24 }, (_, i) => {
    const x = 4 + i * 0.6;
    return [x, 3 + Math.sqrt(i) * 4.2 - i * 0.05] as [number, number];
  });
  const NOW: [number, number] = [9.4, 13.1];
  const PROPOSED: [number, number] = [8.2, 15.6];
  const W = 800;
  const H = 300;
  const sx = (x: number) => ((x - 3) / 16) * W;
  const sy = (y: number) => H - ((y - 2) / 22) * H;
  const path = FRONTIER.map(
    ([x, y], i) => `${i ? "L" : "M"}${sx(x).toFixed(1)},${sy(y).toFixed(1)}`,
  ).join("");
</script>

<div class="grid h-full grid-cols-[15rem_1fr] overflow-hidden">
  <aside class="flex flex-col gap-4 overflow-auto border-r p-3 text-sm">
    <div>
      <p class="mb-1.5 font-medium">Aim</p>
      <div class="grid gap-1">
        {#each OBJECTIVES as o (o)}
          <button
            type="button"
            class={cn(
              "rounded-md border px-2.5 py-1.5 text-left text-xs",
              objective === o
                ? "border-primary bg-primary/12"
                : "hover:border-ring/60",
            )}
            onclick={() => (objective = o)}>{o}</button
          >
        {/each}
      </div>
    </div>
    <div class="grid gap-2">
      <span class="flex justify-between"
        >Most in one Book <span class="num text-muted-foreground">{cap}%</span
        ></span
      >
      <Slider
        type="single"
        min={10}
        max={80}
        step={5}
        value={cap}
        onValueChange={(v: number) => (cap = v)}
        aria-label="Most in one Book"
      />
    </div>
    <div class="grid gap-2">
      <span class="flex justify-between"
        >Most to move at once <span class="num text-muted-foreground"
          >{turnover}%</span
        ></span
      >
      <Slider
        type="single"
        min={5}
        max={50}
        step={5}
        value={turnover}
        onValueChange={(v: number) => (turnover = v)}
        aria-label="Most to move at once"
      />
    </div>
    <p class="text-muted-foreground text-xs">
      Optimisers chase a few lucky bots. Weights below are checked over 200
      resamples; ones that swing a lot are marked.
    </p>
  </aside>
  <div class="flex min-h-0 flex-col overflow-auto">
    <div class="solid-backing flex min-h-[16rem] flex-1 flex-col border-b p-3">
      <p class="mb-1 text-sm font-medium">
        Risk against return <span class="text-muted-foreground font-normal"
          >yearly, from evidence runs</span
        >
      </p>
      <svg
        viewBox="0 0 {W} {H}"
        class="min-h-0 w-full flex-1"
        role="img"
        aria-label="Efficient frontier with today's mix and the proposal"
      >
        {#each [0.25, 0.5, 0.75] as g (g)}
          <line x1="0" x2={W} y1={g * H} y2={g * H} stroke="var(--border)" />
        {/each}
        <text x="4" y="14" font-size="11" fill="var(--muted-foreground)"
          >return ↑</text
        >
        <text x={W - 60} y={H - 6} font-size="11" fill="var(--muted-foreground)"
          >risk →</text
        >
        <path
          d={path}
          fill="none"
          stroke="var(--muted-foreground)"
          stroke-width="1.5"
        />
        <line
          x1={sx(NOW[0])}
          y1={sy(NOW[1])}
          x2={sx(PROPOSED[0])}
          y2={sy(PROPOSED[1])}
          stroke="var(--primary)"
          stroke-dasharray="4 3"
        />
        <circle
          cx={sx(NOW[0])}
          cy={sy(NOW[1])}
          r="5"
          fill="var(--foreground)"
        />
        <text
          x={sx(NOW[0]) + 8}
          y={sy(NOW[1]) + 4}
          font-size="11"
          fill="var(--foreground)">today</text
        >
        <circle
          cx={sx(PROPOSED[0])}
          cy={sy(PROPOSED[1])}
          r="5"
          fill="var(--primary)"
        />
        <text
          x={sx(PROPOSED[0]) + 8}
          y={sy(PROPOSED[1]) - 6}
          font-size="11"
          fill="var(--primary)">{objective}</text
        >
      </svg>
    </div>
    <table class="w-full text-sm">
      <thead class="text-muted-foreground text-left text-xs">
        <tr class="border-b"
          ><th class="py-1.5 pl-3 font-normal">Book</th><th class="font-normal"
            >Now</th
          ><th class="font-normal"
            >Proposed <span class="opacity-70">(band: resample range)</span></th
          ><th class="pr-3 text-right font-normal">Volatility</th></tr
        >
      </thead>
      <tbody>
        {#each ALLOC as a (a.book)}
          <tr class="border-b border-border/50">
            <td class="py-1.5 pl-3"
              >{a.book}{#if Math.abs(a.proposed - a.now) >= 8}<span
                  class="text-warning ml-1.5 text-xs">swings in resamples</span
                >{/if}</td
            >
            <td
              ><span class="flex items-center gap-2"
                ><span
                  class="bg-muted-foreground/50 h-2 rounded-sm"
                  style="width:{a.now * 2}px"
                ></span><span class="num text-xs">{a.now}%</span></span
              ></td
            >
            <td
              ><span class="flex items-center gap-2"
                ><span class="relative block h-3 w-24">
                  <span
                    class="bg-primary/20 absolute inset-y-0 rounded-sm"
                    style="left:{Math.max(
                      0,
                      Math.min(a.proposed, cap) -
                        (Math.abs(a.proposed - a.now) >= 8 ? 9 : 3),
                    ) * 2}px; width:{(Math.abs(a.proposed - a.now) >= 8
                      ? 18
                      : 6) * 2}px"
                    title="Range across 200 resamples"
                  ></span>
                  <span
                    class="bg-primary absolute inset-y-0.5 left-0 rounded-sm"
                    style="width:{Math.min(a.proposed, cap) * 2}px"
                  ></span></span
                ><span class="num text-xs">{Math.min(a.proposed, cap)}%</span
                ></span
              ></td
            >
            <td class="num text-muted-foreground pr-3 text-right text-xs"
              >{a.vol}%</td
            >
          </tr>
        {/each}
      </tbody>
    </table>
    <div class="mt-auto flex items-center gap-2 border-t px-3 py-2">
      <Button
        size="sm"
        onclick={() =>
          workbench.notify(
            "The proposal becomes new Book versions with new capital. Each needs your signature; money moves only through treasury acts you sign.",
          )}>Draft these changes</Button
      >
      <Button
        size="sm"
        variant="ghost"
        onclick={() => workbench.notify("Saved as an allocation preset.")}
        >Save as preset</Button
      >
      <span class="text-muted-foreground ml-auto text-xs"
        >New scope: no allocation in the docs yet</span
      >
    </div>
  </div>
</div>
