<script lang="ts">
  /** A day-one empty state: one line and the action that fills it. */
  import { resolve } from "$app/paths";
  import { Button } from "$lib/components/ui/button";
  import { cn } from "$lib/utils";
  import type { DayOne } from "./day-one";

  let {
    line,
    action,
    class: className,
  }: DayOne & { class?: string } = $props();
  const [path, query] = $derived(action.href.split("?"));
</script>

<div
  class={cn(
    "flex h-full flex-col items-center justify-center gap-3 p-4 text-center",
    className,
  )}
  data-day-one
>
  <p class="text-muted-foreground text-sm">{line}</p>
  <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
  <Button
    size="sm"
    variant="outline"
    href={`${resolve(path as "/")}${query ? `?${query}` : ""}`}
    >{action.label}</Button
  >
  <!-- eslint-enable svelte/no-navigation-without-resolve -->
</div>
