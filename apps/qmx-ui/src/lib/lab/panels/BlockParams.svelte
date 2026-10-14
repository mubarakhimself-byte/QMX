<script lang="ts">
  /** A block's settings as sliders for one pod (podModel). */
  import { Slider } from "$lib/components/ui/slider";
  import { cn } from "$lib/utils";
  import { PARAMS, fmt, podModel } from "../pod-model.svelte";

  let { pod, block }: { pod: string; block: string } = $props();
  const params = $derived(PARAMS[block] ?? []);
</script>

{#if params.length}
  <ul class="flex flex-col">
    {#each params as x (x.key)}
      {@const v = podModel.get(pod, block, x.key)}
      <li
        class="py-row grid grid-cols-[minmax(0,8rem)_1fr_4.5rem] items-center gap-3 text-sm"
      >
        <span
          class={cn(
            "truncate",
            v !== podModel.defaultOf(pod, block, x.key) && "text-primary",
          )}>{x.label}</span
        >
        <Slider
          type="single"
          min={x.min}
          max={x.max}
          step={x.step}
          value={v}
          onValueChange={(n: number) => podModel.set(pod, block, x.key, n)}
          aria-label={x.label}
        />
        <span class="num text-right">{fmt(v, x.unit)}</span>
      </li>
    {/each}
  </ul>
{:else}
  <p class="text-muted-foreground text-sm">Nothing to set</p>
{/if}
