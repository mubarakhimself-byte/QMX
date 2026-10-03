<script lang="ts">
  /**
   * Pods side by side on the same bots and paths: return, pain, tail,
   * behaviour, fragility. Raw numbers, no total score; the best per row is
   * marked only where the difference is bigger than the Monte Carlo noise.
   */
  import { cn } from "$lib/utils";
  import { LAB_PODS, POD_MEASURES } from "../pods";
  import { lab } from "../lab.svelte";

  const pods = $derived(LAB_PODS.filter((p) => lab.podsTicked.includes(p.id)));
  const groups = [...new Set(POD_MEASURES.map((m) => m.group))];
  function toggle(id: string) {
    lab.podsTicked = lab.podsTicked.includes(id)
      ? lab.podsTicked.filter((x) => x !== id)
      : [...lab.podsTicked, id];
  }
</script>

<div class="flex h-full flex-col">
  <div class="flex h-9 shrink-0 items-center gap-2 border-b px-3 text-xs">
    <span class="text-muted-foreground">Compare</span>
    {#each LAB_PODS as p (p.id)}
      <label class="flex items-center gap-1.5">
        <input
          type="checkbox"
          class="accent-primary"
          checked={lab.podsTicked.includes(p.id)}
          onchange={() => toggle(p.id)}
        />
        <span class="size-2 rounded-full" style="background:{p.color}"
        ></span>{p.name}
      </label>
    {/each}
    <span class="text-muted-foreground ml-auto"
      >Same bots, 2022–2025, full rerun</span
    >
  </div>
  <div class="min-h-0 flex-1 overflow-auto">
    <table class="w-full text-sm">
      <thead
        class="bg-panel text-muted-foreground sticky top-0 text-left text-xs"
      >
        <tr class="border-b">
          <th class="py-2 pl-3 font-normal">Measure</th>
          {#each pods as p (p.id)}<th class="py-2 pr-3 text-right font-normal"
              ><span class="inline-flex items-center gap-1.5"
                ><span class="size-2 rounded-full" style="background:{p.color}"
                ></span>{p.name}</span
              ></th
            >{/each}
        </tr>
      </thead>
      <tbody>
        {#each groups as g (g)}
          <tr class="bg-muted/30"
            ><td colspan={pods.length + 1} class="px-3 py-1 text-xs font-medium"
              >{g}</td
            ></tr
          >
          {#each POD_MEASURES.filter((m) => m.group === g) as m (m.label)}
            <tr class="border-b border-border/50">
              <td class="py-1.5 pl-3">{m.label}</td>
              {#each pods as p (p.id)}
                <td
                  class={cn(
                    "num py-1.5 pr-3 text-right",
                    m.best === p.id && "text-success font-semibold",
                  )}>{m.values[p.id]}</td
                >
              {/each}
            </tr>
          {/each}
        {/each}
      </tbody>
    </table>
  </div>
  <p class="text-muted-foreground border-t px-3 py-1.5 text-xs">
    No single score. Vol-targeted core gives up $1,510 of net return for a third
    of Classic Book's worst stress loss.
  </p>
</div>
