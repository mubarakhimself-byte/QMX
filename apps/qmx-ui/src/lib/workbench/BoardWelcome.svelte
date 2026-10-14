<script lang="ts">
  /**
   * What a board shows while every panel is empty (day one): a title, one
   * line, the actions that fill the board, and optional content beneath
   * (a template gallery, the Get started steps).
   */
  import type { Snippet } from "svelte";
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import type { FirstAction } from "./day-one";

  let {
    title,
    line,
    actions = [],
    children,
  }: {
    title: string;
    line?: string;
    actions?: FirstAction[];
    children?: Snippet;
  } = $props();

  const hrefOf = (a: FirstAction) => {
    const [path, query] = a.href.split("?");
    return `${resolve(path as "/")}${query ? `?${query}` : ""}`;
  };
</script>

<section
  class="flex h-full overflow-auto"
  aria-label={title}
  data-board-welcome
>
  <div
    class={cn(
      "m-auto flex w-full flex-col gap-group px-page py-page",
      children ? "max-w-5xl" : "max-w-xl items-center text-center",
    )}
  >
    <div
      class={cn(
        "flex flex-wrap gap-x-6 gap-y-3",
        children ? "items-end" : "flex-col items-center",
      )}
    >
      <div class={cn("min-w-0", children && "mr-auto")}>
        <h2 class="text-2xl font-semibold tracking-tight">{title}</h2>
        {#if line}<p class="text-muted-foreground mt-1">{line}</p>{/if}
      </div>
      {#if actions.length}
        <div class="flex flex-wrap gap-2">
          {#each actions as a, i (a.href)}
            <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
            <Button variant={i === 0 ? "default" : "outline"} href={hrefOf(a)}
              >{a.label}</Button
            >
            <!-- eslint-enable svelte/no-navigation-without-resolve -->
          {/each}
        </div>
      {/if}
    </div>
    {@render children?.()}
  </div>
</section>
