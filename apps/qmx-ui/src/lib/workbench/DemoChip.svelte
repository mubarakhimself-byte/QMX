<script lang="ts">
  /**
   * The single demo label (DESIGN-RULES.md): a small chip in the page header
   * instead of a full-width banner. It opens one line saying what is sample
   * data. Hidden when demo mode is off in Settings.
   */
  import * as Popover from "$lib/components/ui/popover";
  import { resolve } from "$app/paths";
  import { workbench } from "./workbench.svelte";

  let {
    note,
  }: { /** One line: what on this screen is sample data. */ note: string } =
    $props();
</script>

{#if workbench.demoMode}
  <Popover.Root>
    <Popover.Trigger
      class="border-warning/50 text-warning hover:bg-warning/10 data-[state=open]:bg-warning/10 inline-flex h-6 shrink-0 items-center rounded-full border px-2.5 text-xs font-medium"
      aria-label="Demo data. What is sample here?"
    >
      Demo
    </Popover.Trigger>
    <Popover.Content align="start" class="text-sm leading-relaxed">
      <p>{note}</p>
      <!-- eslint-disable svelte/no-navigation-without-resolve -- resolved path plus a query string -->
      <a
        class="text-primary mt-2 inline-block text-xs underline-offset-2 hover:underline"
        href={`${resolve("/settings")}?tab=developer`}>Turn demo off</a
      >
      <!-- eslint-enable svelte/no-navigation-without-resolve -->
    </Popover.Content>
  </Popover.Root>
{/if}
