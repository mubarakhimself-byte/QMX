<script lang="ts">
  import type { Row } from "$lib/shell/data";
  import Icon from "./Icon.svelte";
  import { tone, stateLabel } from "./state";

  let { rows, onpick }: { rows: Row[]; onpick?: (r: Row) => void } = $props();
</script>

<ul class="flex flex-col">
  {#each rows as r, i (i)}
    <li>
      <button
        class="hover:bg-accent/60 flex w-full items-start gap-3 rounded-md px-2.5 py-2 text-left transition-colors duration-150"
        onclick={() => onpick?.(r)}
      >
        {#if r.state}
          <span class="dot mt-[0.5em] {tone[r.state]}" title={stateLabel[r.state]}></span>
        {/if}
        <span class="min-w-0 flex-1">
          <span class="line-clamp-2 [overflow-wrap:anywhere]" title={r.label}>{r.label}</span>
          {#if r.where}
            <span class="text-muted-foreground mt-0.5 flex items-center gap-1.5 text-sm">
              <Icon name={r.where === "This PC" ? "laptop" : "server"} class="size-3.5 shrink-0" />
              <span class="truncate" title={r.where}>{r.where}</span>
            </span>
          {/if}
        </span>
        {#if r.value}
          <span class="num shrink-0 whitespace-nowrap">{r.value}</span>
        {/if}
        {#if r.meta}
          <span
            class="shrink-0 text-sm whitespace-nowrap {r.tone ? `num ${tone[r.tone]}` : 'text-muted-foreground'}"
          >
            {r.meta}
          </span>
        {/if}
      </button>
    </li>
  {/each}
</ul>
