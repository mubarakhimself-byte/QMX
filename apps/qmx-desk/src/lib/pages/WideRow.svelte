<script lang="ts">
  import Icon from "$lib/qmx/Icon.svelte";
  import { tone, stateLabel } from "$lib/qmx/state";
  import { things } from "$lib/shell/things.svelte";
  import { shell } from "$lib/shell/state.svelte";
  import { lifeOrder, type Obj, type ListKind } from "$lib/shell/model";

  // A thing as a full-width row: enough evidence to choose without opening
  // it (where it is in its life per market, its curve, its number, where it
  // runs), and one click to its page.
  let { o, list }: { o: Obj; list: ListKind } = $props();
  const res = $derived(o.sections?.find((s) => s.id === "results")?.body);
  const curve = $derived(res && res.t === "spark" ? res.series : undefined);
  const nums = $derived(o.sections?.find((s) => s.id === "numbers" || s.id === "progress")?.body);
  const big = $derived(nums && nums.t === "stats" ? nums.stats[nums.stats.length > 1 && o.kind === "unit" ? 1 : 0] : undefined);
  const path = $derived.by(() => {
    if (!curve) return "";
    const lo = Math.min(...curve);
    const hi = Math.max(...curve);
    return curve.map((v, i) => `${i ? "L" : "M"}${((i / (curve.length - 1)) * 100).toFixed(1)},${(22 - ((v - lo) / (hi - lo || 1)) * 20).toFixed(1)}`).join(" ");
  });
  const ink: Record<string, string> = { live: "var(--live)", paper: "var(--paper)", tested: "var(--foreground)", draft: "var(--idle)" };
</script>

<button class="wr pick grid w-full min-w-0 items-center gap-x-6 rounded-md px-3 py-2.5 text-left" data-id={o.id} onclick={() => shell.open({ id: o.target ?? o.id, list })}>
  <span class="flex min-w-0 items-start gap-3">
    <span class="dot mt-[0.5em] {tone[o.tone]}" title={stateLabel[o.tone]}></span>
    <span class="min-w-0">
      <span class="text-foreground line-clamp-2 font-medium [overflow-wrap:anywhere]" title={o.name}>{o.name}</span>
      {#if o.line}<span class="text-muted-foreground block truncate text-sm" title={o.line}>{o.line}</span>{/if}
    </span>
  </span>

  <span class="c-life flex min-w-0 flex-col gap-1">
    {#each o.markets ?? [] as m (m.sym)}
      {@const ci = lifeOrder.indexOf(m.life)}
      <span class="flex min-w-0 items-center gap-2 text-sm" title="{m.sym}: {m.life}{m.paused ? ', paused' : ''}">
        <span class="num text-muted-foreground w-16 shrink-0">{m.sym}</span>
        <span class="flex items-center gap-1" aria-hidden="true">
          {#each lifeOrder as s, i (s)}
            <span class="size-2 rounded-full {i === ci ? '' : i < ci ? 'bg-foreground/40' : 'bg-foreground/12'} {m.target && i === lifeOrder.indexOf(m.target) ? 'outline-needs outline-1 outline-offset-1 outline-dashed' : ''}" style:background={i === ci ? ink[s] : undefined}></span>
          {/each}
        </span>
        <span class="truncate" style:color={ink[m.life]}>{m.life}{m.paused ? ", paused" : ""}</span>
      </span>
    {/each}
  </span>

  <span class="c-curve flex min-w-0 items-center gap-3">
    {#if curve}
      <svg viewBox="0 0 100 24" preserveAspectRatio="none" class="h-6 w-24 shrink-0" style:color={o.tone === "live" ? "var(--live)" : o.tone === "paper" ? "var(--paper)" : "var(--muted-foreground)"} aria-hidden="true">
        <path d={path} fill="none" stroke="currentColor" stroke-width="1.5" vector-effect="non-scaling-stroke" />
      </svg>
    {/if}
    {#if big}<span class="num truncate {big.tone ? tone[big.tone] : ''}" title={big.label}>{big.value}</span>{/if}
  </span>

  <span class="c-where text-muted-foreground flex min-w-0 items-center gap-1.5 text-sm">
    {#if o.where}<Icon name={o.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" /><span class="truncate" title={o.where}>{o.where}</span>{/if}
  </span>

  <span class="flex shrink-0 flex-col items-end text-sm">
    <span class="{tone[o.tone]} whitespace-nowrap">{o.word}</span>
    {#if o.when}<span class="num text-muted-foreground whitespace-nowrap">{o.when}</span>{/if}
  </span>
</button>

<style>
  .wr {
    grid-template-columns: minmax(0, 2.2fr) minmax(0, 1.5fr) minmax(0, 1.1fr) minmax(0, 0.9fr) 6.5rem;
  }
  @container (max-width: 60rem) {
    .wr {
      grid-template-columns: minmax(0, 2fr) minmax(0, 1.5fr) minmax(0, 0.8fr) 6.5rem;
    }
    .c-curve {
      display: none;
    }
  }
  @container (max-width: 42rem) {
    .wr {
      grid-template-columns: minmax(0, 1fr) 6.5rem;
    }
    .c-life,
    .c-where {
      display: none;
    }
  }
</style>
