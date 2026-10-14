<script lang="ts">
  /** What needs you right now, from every screen, newest problems first. */
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import CircleCheck from "@lucide/svelte/icons/circle-check";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import { panelSize } from "$lib/workbench/tiles/panel-size";
  import { needs } from "../needs";

  const size = panelSize();

  const list = $derived(needs());
  const TONE = {
    warning: "bg-warning",
    info: "bg-info",
    destructive: "bg-destructive",
  };
</script>

{#if !list.length}
  <p
    class="text-muted-foreground p-panel flex h-full items-center justify-center gap-2 text-sm"
  >
    <CircleCheck class="text-success size-4" />Nothing needs you
  </p>
{:else}
  <div class="p-panel h-full overflow-auto">
    {#if size.mode === "compact"}
      <p class="num text-2xl font-semibold">{list.length}</p>
      <p class="text-muted-foreground pb-row text-xs">waiting on you</p>
    {/if}
    <ul class="flex flex-col">
      <!-- eslint-disable svelte/no-navigation-without-resolve -->
      {#each list as n (n.id)}
        <li>
          <a
            href={`${resolve(n.path as "/")}${n.query ? `?${n.query}` : ""}`}
            class="hover:bg-muted/60 py-row group/need -mx-2 flex items-start gap-3 rounded-md px-2"
            title={`${n.kind} · ${n.why}`}
          >
            <span class={cn("mt-2 size-2 shrink-0 rounded-full", TONE[n.tone])}
            ></span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-sm">{n.title}</span>
              {#if size.mode === "expanded"}<span
                  class="text-muted-foreground block truncate text-xs"
                  >{n.why}</span
                >{/if}
            </span>
            {#if size.mode !== "compact"}<span
                class="text-muted-foreground mt-0.5 shrink-0 text-xs"
                >{n.kind}</span
              ><ArrowUpRight
                class="text-muted-foreground mt-1 size-4 shrink-0 opacity-0 group-hover/need:opacity-100"
              />{/if}
          </a>
        </li>
      {/each}
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    </ul>
  </div>
{/if}
