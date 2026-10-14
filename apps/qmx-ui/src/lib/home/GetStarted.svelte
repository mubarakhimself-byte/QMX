<script lang="ts">
  /**
   * First run (demo off): four steps, each one click to the screen that does
   * it. A step ticks off once opened (local state); the list leaves when all
   * four are done or hidden.
   */
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import { cn } from "$lib/utils";
  import { GET_STARTED } from "$lib/workbench/day-one";
  import { home } from "./home.svelte";

  const done = $derived(GET_STARTED.filter((s) => home.started.includes(s.id)));

  function open(id: string, href: string) {
    home.markStarted(id);
    const [path, query] = href.split("?");
    // eslint-disable-next-line svelte/no-navigation-without-resolve -- resolved path plus a query string
    goto(`${resolve(path as "/")}${query ? `?${query}` : ""}`);
  }
</script>

{#if done.length < GET_STARTED.length}
  <section
    class="bg-panel flex shrink-0 items-center gap-tile border-b px-4 py-2"
    aria-label="Get started"
  >
    <h2 class="mr-2 text-sm font-semibold whitespace-nowrap">Get started</h2>
    <span class="text-muted-foreground num mr-2 text-xs"
      >{done.length} of {GET_STARTED.length}</span
    >
    <ol class="flex min-w-0 flex-1 gap-tile">
      {#each GET_STARTED as s, i (s.id)}
        {@const ok = home.started.includes(s.id)}
        <li class="min-w-0 flex-1">
          <button
            type="button"
            class={cn(
              "hover:bg-muted flex h-10 w-full items-center gap-2 rounded-md border px-3 text-left text-sm",
              ok && "text-muted-foreground border-transparent",
            )}
            onclick={() => open(s.id, s.href)}
          >
            <span
              class={cn(
                "num flex size-5 shrink-0 items-center justify-center rounded-full border text-xs",
                ok && "bg-success/20 text-success border-transparent",
              )}
              >{#if ok}<Check class="size-3.5" />{:else}{i + 1}{/if}</span
            >
            <span class={cn("truncate", ok && "line-through")}>{s.label}</span>
          </button>
        </li>
      {/each}
    </ol>
    <button
      type="button"
      class="hover:bg-muted text-muted-foreground flex size-8 shrink-0 items-center justify-center rounded-md"
      aria-label="Hide get started"
      title="Hide"
      onclick={() => GET_STARTED.forEach((s) => home.markStarted(s.id))}
      ><X class="size-4" /></button
    >
  </section>
{/if}
