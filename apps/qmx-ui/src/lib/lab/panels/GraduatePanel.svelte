<script lang="ts">
  /**
   * Ready for live? The checks a paper run must pass before the pod can be
   * promoted. Promoting builds the promotion card from the Lab's tests and
   * this paper run; you sign it in Portfolio, and activation is a separate
   * click that takes effect at the next 00:00 UTC (DEC-0205, DEC-0261).
   */
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import CircleDashed from "@lucide/svelte/icons/circle-dashed";
  import Rocket from "@lucide/svelte/icons/rocket";
  import { Button } from "$lib/components/ui/button";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS, PAPER_RUNS } from "../pods";
  import { lab } from "../lab.svelte";

  const run = $derived(
    PAPER_RUNS.find((r) => r.pod === lab.labPod) ?? PAPER_RUNS[0],
  );
  const pod = $derived(LAB_PODS.find((p) => p.id === run.pod)!);
  const done = $derived(run.checks.filter((c) => c.done).length);
  const ready = $derived(done === run.checks.length);
</script>

<div class="flex h-full flex-col">
  <div class="shrink-0 px-3 pt-3">
    <p class="text-lg font-semibold">
      {ready ? "Ready for live" : "Not yet"}
    </p>
    <p class="text-muted-foreground text-xs">
      {done} of {run.checks.length} checks passed for {pod.name}
      {run.version}
    </p>
  </div>
  <ul class="min-h-0 flex-1 overflow-auto px-3 py-2">
    {#each run.checks as c (c.label)}
      <li class="flex items-start gap-2 py-1.5">
        {#if c.done}<CircleCheck
            class="text-success mt-0.5 size-4 shrink-0"
          />{:else}<CircleDashed
            class="text-muted-foreground mt-0.5 size-4 shrink-0"
          />{/if}
        <span class="text-sm"
          >{c.label}<span class="text-muted-foreground block text-xs"
            >{c.note}</span
          ></span
        >
      </li>
    {/each}
  </ul>
  <div class="flex shrink-0 flex-wrap items-center gap-2 border-t px-3 py-2">
    <Button
      size="sm"
      disabled={!ready}
      title={ready ? undefined : "Finish the soak first"}
      onclick={() =>
        workbench.notify(
          `The promotion card for ${pod.name} ${run.version} is built from its Lab tests and this paper run. You sign it in Portfolio; activation is a separate click that takes effect at the next 00:00 UTC.`,
        )}><Rocket />Promote to live</Button
    >
    <Button
      size="sm"
      variant="ghost"
      onclick={() =>
        workbench.notify(
          `${pod.name} would soak 7 more days on ${run.money}. Needs the trading node.`,
        )}>Extend soak</Button
    >
    <Button
      size="sm"
      variant="ghost"
      class="text-destructive ml-auto"
      onclick={() =>
        workbench.notify(
          `Stopping the paper run closes ${pod.name}'s paper positions and keeps the record. Needs the trading node.`,
        )}>Stop paper run</Button
    >
  </div>
</div>
