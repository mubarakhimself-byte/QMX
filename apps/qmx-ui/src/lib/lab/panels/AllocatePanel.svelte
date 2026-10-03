<script lang="ts">
  /**
   * Allocation experiments across tested pods (moved here from Portfolio):
   * pick a method, refit walk-forward, see how stable the weights are, save
   * the result as a fund plan that travels to Portfolio like any promotion.
   */
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { ALLOCATION } from "../pods";

  const METHODS = [
    "Equal",
    "Risk parity",
    "Min drawdown",
    "Max return ÷ drawdown",
    "Your own",
  ];
  let method = $state("Risk parity");
</script>

<div class="flex h-full flex-col">
  <div class="flex shrink-0 flex-wrap items-center gap-1.5 border-b px-3 py-2">
    {#each METHODS as m (m)}
      <button
        type="button"
        class={cn(
          "h-8 rounded-lg border px-3 text-sm",
          method === m
            ? "border-primary bg-primary/12"
            : "hover:border-ring/60",
        )}
        onclick={() => (method = m)}>{m}</button
      >
    {/each}
  </div>
  <div class="min-h-0 flex-1 overflow-auto p-4">
    <div class="grid gap-5">
      {#each ALLOCATION as a (a.pod)}
        <div>
          <div class="mb-1.5 flex items-baseline justify-between">
            <span class="text-base font-medium">{a.pod}</span>
            <span class="num text-sm"
              ><span class="text-muted-foreground">{a.now}% →</span>
              <span class="text-xl font-semibold">{a.proposed}%</span></span
            >
          </div>
          <div class="bg-muted relative h-6 rounded-md">
            <span
              class="bg-primary/20 absolute inset-y-0 rounded-md"
              style="left:{a.band[0]}%; width:{a.band[1] - a.band[0]}%"
              title="Range across walk-forward refits"
            ></span>
            <span
              class="bg-muted-foreground absolute -inset-y-0.5 w-0.5"
              style="left:{a.now}%"
              title="Now"
            ></span>
            <span
              class="bg-primary absolute top-1 bottom-1 left-0 rounded-sm"
              style="width:{a.proposed}%"
            ></span>
          </div>
          <p class="text-muted-foreground mt-1 text-xs">
            Moves between {a.band[0]}% and {a.band[1]}% across refits{a
              .band[1] -
              a.band[0] >
            14
              ? " — unstable, treat with care"
              : ""}
          </p>
        </div>
      {/each}
    </div>
  </div>
  <div class="flex items-center gap-2 border-t px-3 py-2">
    <Button
      size="sm"
      onclick={() =>
        workbench.notify(
          `Fund plan (${method}) saved. It goes to Portfolio on paper first, like any pod.`,
        )}>Save as fund plan</Button
    >
    <span class="text-muted-foreground text-xs"
      >Walk-forward refits, 2022–2025</span
    >
  </div>
</div>
