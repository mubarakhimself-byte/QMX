<script lang="ts">
  import { lifeOrder, type Market, type Life } from "$lib/shell/model";

  // Where a unit is in its life on one market: draft, tested, paper, live.
  // The current stop carries its state colour; a proposed move is a dashed
  // violet step to the stop it asks for. Stopped and retired sit off the line.
  let { market, target, big = false }: { market: Market; target?: Life; big?: boolean } = $props();

  const off = $derived(market.life === "stopped" || market.life === "retired");
  const cur = $derived(off ? -1 : lifeOrder.indexOf(market.life));
  const goal = $derived(target ?? market.target);
  const ti = $derived(goal ? lifeOrder.indexOf(goal) : -1);
  const colour: Record<string, string> = { draft: "var(--idle)", tested: "var(--foreground)", paper: "var(--paper)", live: "var(--live)" };
</script>

<div class="rail flex min-w-0 items-center gap-3 {big ? 'py-1' : ''}" aria-label="{market.sym}: {market.life}{market.paused ? ', paused' : ''}{goal ? `, asks to move to ${goal}` : ''}">
  <span class="num w-[4.5rem] shrink-0 {big ? 'text-base' : 'text-sm'} font-medium">{market.sym}</span>
  <ol class="relative grid min-w-0 flex-1 grid-cols-4 {off ? 'opacity-40' : ''}">
    {#each lifeOrder as stop, i (stop)}
      {@const isCur = i === cur}
      {@const past = i < cur}
      {@const isGoal = i === ti}
      <li class="relative flex min-w-0 flex-col items-start gap-1">
        {#if i < lifeOrder.length - 1}
          <!-- The segment from this stop to the next. -->
          <span
            class="absolute top-[0.4rem] right-0 left-[0.9rem] h-0 border-t-2 {isGoal || (i >= cur && i < ti) ? 'border-dashed border-needs' : i < cur ? 'border-foreground/45' : 'border-foreground/12'}"
            aria-hidden="true"
          ></span>
        {/if}
        <span
          class="relative z-10 size-[0.9rem] rounded-full border-2 {isCur ? '' : past ? 'bg-foreground/45 border-transparent' : isGoal ? 'border-dashed border-needs bg-background' : 'bg-background border-foreground/20'}"
          style:background={isCur ? colour[stop] : undefined}
          style:border-color={isCur ? colour[stop] : undefined}
          style:box-shadow={isCur ? `0 0 0 4px color-mix(in oklch, ${colour[stop]} 22%, transparent)` : undefined}
        ></span>
        <span
          class="truncate text-sm {isCur ? 'font-semibold' : isGoal ? 'text-needs font-medium' : past ? 'text-muted-foreground' : 'text-idle'}"
          style:color={isCur ? colour[stop] : undefined}
        >
          {stop}{#if isCur && market.paused}<span class="text-paper">, paused</span>{/if}
        </span>
      </li>
    {/each}
  </ol>
  {#if off}
    <span class="shrink-0 rounded-full px-2 py-0.5 text-sm font-semibold {market.life === 'stopped' ? 'text-down bg-down/15' : 'text-muted-foreground bg-muted'}">{market.life}</span>
  {/if}
</div>
