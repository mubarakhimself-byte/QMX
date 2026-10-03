<script lang="ts">
  /**
   * Every time a pod shrank, refused, halted or stood down, and the block
   * that did it: from the tests on Test, from today's paper runs on Paper.
   */
  import { cn } from "$lib/utils";
  import { INTERVENTIONS, LAB_PODS, PAPER_INTERVENTIONS } from "../pods";
  import { lab } from "../lab.svelte";

  const list = $derived(
    lab.activeId === "pod-paper" ? PAPER_INTERVENTIONS : INTERVENTIONS,
  );

  const color = (name: string) =>
    LAB_PODS.find((p) => p.name === name)?.color ?? "var(--muted-foreground)";
</script>

<ul class="h-full overflow-auto">
  {#each list as it (it.time + it.pod)}
    <li class="flex items-start gap-3 border-b border-border/50 px-3 py-2">
      <span
        class="mt-1.5 size-2 shrink-0 rounded-full"
        style="background:{color(it.pod)}"
      ></span>
      <div class="min-w-0 flex-1">
        <p class="text-sm">
          <span
            class={cn(
              "font-medium",
              it.what.startsWith("Stood") && "text-destructive",
            )}>{it.what}</span
          > <span class="text-muted-foreground">by {it.by}</span>
        </p>
        <p class="text-muted-foreground text-xs">{it.pod} · {it.time}</p>
      </div>
    </li>
  {/each}
</ul>
