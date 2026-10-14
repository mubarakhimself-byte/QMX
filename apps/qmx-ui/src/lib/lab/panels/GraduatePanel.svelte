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
  import InfoTip from "$lib/workbench/InfoTip.svelte";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { workbench } from "$lib/workbench/workbench.svelte";
  import { LAB_PODS } from "../pods";
  import { podModel } from "../pod-model.svelte";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const run = $derived(podModel.paper(lab.labPod));
  const pod = $derived(LAB_PODS.find((p) => p.id === run.pod)!);
  const done = $derived(run.checks.filter((c) => c.done).length);
  let stopArmed = $state(false);
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label={`Ready for live? · ${pod.name}`}
    value={`${done} of ${run.checks.length}`}
    status={run.stopped ? "Stopped" : run.ready ? "Ready" : "Not yet"}
    tone={run.ready ? "good" : run.stopped ? "muted" : "warn"}
  />
{:else}
  <div class="flex h-full flex-col">
    <div class="px-panel flex h-11 shrink-0 items-center gap-2">
      <p class="text-base font-semibold">
        {run.stopped ? "Stopped" : run.ready ? "Ready for live" : "Not yet"}
      </p>
      <span class="text-muted-foreground num text-xs"
        >{done}/{run.checks.length}</span
      >
      <InfoTip
        class="ml-auto"
        label="Explain promotion"
        text="Promote builds the promotion card from the Lab's tests and this paper run. You sign it in Portfolio; activation is a separate click that takes effect at the next 00:00 UTC."
      />
    </div>
    <ul class="px-panel min-h-0 flex-1 overflow-auto">
      {#each run.checks as c (c.label)}
        <li class="py-row flex items-center gap-2 text-sm" title={c.note}>
          {#if c.done}<CircleCheck
              class="text-success size-4 shrink-0"
            />{:else}<CircleDashed
              class="text-muted-foreground size-4 shrink-0"
            />{/if}
          <span class="min-w-0 flex-1 truncate">{c.label}</span>
          <span
            class="text-muted-foreground num hidden shrink-0 text-xs @md:inline"
            >{c.note}</span
          >
        </li>
      {/each}
    </ul>
    <div
      class="px-panel py-row flex shrink-0 flex-wrap items-center gap-2 border-t"
    >
      <Button
        size="sm"
        disabled={!run.ready}
        onclick={() =>
          workbench.notify(
            `Promotion card for ${pod.name} ${run.version} is waiting in Portfolio, Road to live.`,
          )}><Rocket />Promote</Button
      >
      {#if run.stopped}
        <Button
          size="sm"
          variant="ghost"
          class="ml-auto"
          onclick={() => (podModel.paperStopped[run.pod] = false)}
          >Restart paper run</Button
        >
      {:else}
        <Button
          size="sm"
          variant="ghost"
          class="text-destructive ml-auto"
          onclick={() => {
            if (!stopArmed) {
              stopArmed = true;
              setTimeout(() => (stopArmed = false), 4000);
              return;
            }
            stopArmed = false;
            podModel.paperStopped[run.pod] = true;
            workbench.notify(`${pod.name}'s paper run stopped. Record kept.`);
          }}>{stopArmed ? "Click again to stop" : "Stop paper run"}</Button
        >
      {/if}
    </div>
  </div>
{/if}
