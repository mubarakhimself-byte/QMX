<script lang="ts">
  import { Popover as PopoverPrimitive } from "bits-ui";
  import { cn } from "$lib/utils.js";

  let {
    ref = $bindable(null),
    class: className,
    sideOffset = 6,
    align = "center",
    ...restProps
  }: PopoverPrimitive.ContentProps = $props();
</script>

<PopoverPrimitive.Portal>
  <PopoverPrimitive.Content
    bind:ref
    data-slot="popover-content"
    {sideOffset}
    {align}
    class={cn(
      "data-open:animate-in data-closed:animate-out data-closed:fade-out-0 data-open:fade-in-0 data-closed:zoom-out-95 data-open:zoom-in-95 ring-foreground/5 dark:ring-foreground/10 bg-popover text-popover-foreground z-50 w-72 origin-(--bits-popover-content-transform-origin) rounded-2xl p-4 shadow-lg ring-1 outline-none",
      className,
    )}
    {...restProps}
  />
</PopoverPrimitive.Portal>
