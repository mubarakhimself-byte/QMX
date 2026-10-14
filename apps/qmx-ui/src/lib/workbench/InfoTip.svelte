<script lang="ts">
  /**
   * The one place an explanation lives (DESIGN-RULES.md, word budget): a small
   * "i" that opens the text on click, Enter or Space; Escape closes it.
   */
  import type { Snippet } from "svelte";
  import Info from "@lucide/svelte/icons/info";
  import * as Popover from "$lib/components/ui/popover";
  import { cn } from "$lib/utils";

  let {
    text,
    children,
    label = "Explain",
    side = "bottom",
    class: className,
  }: {
    text?: string;
    children?: Snippet;
    /** Screen-reader name of the button, e.g. "Explain the stress colours". */
    label?: string;
    side?: "top" | "bottom" | "left" | "right";
    class?: string;
  } = $props();
</script>

<Popover.Root>
  <Popover.Trigger
    class={cn(
      "text-muted-foreground hover:text-foreground hover:bg-muted data-[state=open]:text-foreground inline-flex size-6 shrink-0 items-center justify-center rounded-full",
      className,
    )}
    aria-label={label}
  >
    <Info class="size-3.5" />
  </Popover.Trigger>
  <Popover.Content {side} class="text-sm leading-relaxed">
    {#if children}{@render children()}{:else}{text}{/if}
  </Popover.Content>
</Popover.Root>
