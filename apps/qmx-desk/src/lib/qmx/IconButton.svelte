<script lang="ts">
  import * as Tooltip from "$lib/components/ui/tooltip";
  import Icon from "./Icon.svelte";

  // Every icon-only control goes through here, so none ships without a tooltip.
  let {
    icon,
    label,
    on = false,
    size = "size-8",
    side = "bottom",
    onclick,
    children,
  }: {
    icon: string;
    label: string;
    on?: boolean;
    size?: string;
    side?: "top" | "bottom" | "left" | "right";
    onclick?: (e: MouseEvent) => void;
    children?: import("svelte").Snippet;
  } = $props();
</script>

<Tooltip.Root>
  <Tooltip.Trigger>
    {#snippet child({ props })}
      <button {...props} class="press relative shrink-0 {size}" data-on={on} aria-label={label} {onclick}>
        <Icon name={icon} />
        {@render children?.()}
      </button>
    {/snippet}
  </Tooltip.Trigger>
  <Tooltip.Content {side}>{label}</Tooltip.Content>
</Tooltip.Root>
