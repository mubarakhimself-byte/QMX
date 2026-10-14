<script lang="ts">
  /**
   * Every time a pod shrank, refused, halted or stood down, and the block
   * that did it: from the tests on Test, from today's paper runs on Paper.
   * Click one to tune that block in Design.
   */
  import { cn } from "$lib/utils";
  import PanelSummary from "$lib/workbench/PanelSummary.svelte";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { INTERVENTIONS, LAB_PODS, PAPER_INTERVENTIONS } from "../pods";
  import { lab } from "../lab.svelte";

  const size = panelSize();
  const list = $derived(
    lab.activeId === "pod-paper" ? PAPER_INTERVENTIONS : INTERVENTIONS,
  );
  const podOf = (name: string) => LAB_PODS.find((p) => p.name === name);
  const BLOCK_BY: [string, string][] = [
    ["Drawdown ladder", "ladder"],
    ["Volatility spike", "vol-spike"],
    ["Kill line", "kill"],
    ["Regime", "regime"],
    ["Thin hours", "thin-hours"],
    ["Correlation cap", "corr-cap"],
  ];
  function tune(it: (typeof list)[number]) {
    const pod = podOf(it.pod);
    const block = BLOCK_BY.find(([k]) => it.by.startsWith(k))?.[1];
    if (pod) lab.labPod = pod.id;
    if (block) lab.block = block;
    lab.open("pod-design");
  }
  const stoodDown = $derived(
    list.filter((it) => it.what.startsWith("Stood")).length,
  );
</script>

{#if size.mode === "compact"}
  <PanelSummary
    label="Steps in"
    value={String(list.length)}
    status={stoodDown ? `${stoodDown} stood down` : `Last: ${list[0]?.by}`}
    tone={stoodDown ? "bad" : "muted"}
  />
{:else}
  <ul class="h-full overflow-auto">
    {#each list as it (it.time + it.pod)}
      <li class="border-border/50 border-b">
        <button
          type="button"
          class="hover:bg-muted/40 px-panel py-row flex w-full items-start gap-3 text-left"
          title="Tune this block in Design"
          onclick={() => tune(it)}
        >
          <span
            class="mt-1.5 size-2 shrink-0 rounded-full"
            style="background:{podOf(it.pod)?.color ??
              'var(--muted-foreground)'}"
          ></span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm">
              <span
                class={cn(
                  "font-medium",
                  it.what.startsWith("Stood") && "text-destructive",
                )}>{it.what}</span
              > <span class="text-muted-foreground">by {it.by}</span>
            </span>
            <span class="text-muted-foreground block truncate text-xs"
              >{it.pod} · {it.time}</span
            >
          </span>
        </button>
      </li>
    {/each}
  </ul>
{/if}
