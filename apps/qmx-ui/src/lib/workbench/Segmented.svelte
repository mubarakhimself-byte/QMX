<script lang="ts" generics="T extends string | boolean">
  /** Two to five options for a mode of the same data (DESIGN-RULES.md §4). */
  import { cn } from "$lib/utils";

  let {
    options,
    value = $bindable(),
    label,
    onchange,
    class: className,
  }: {
    options: { value: T; label: string; dot?: string; disabled?: boolean }[];
    value: T;
    label: string;
    onchange?: (v: T) => void;
    class?: string;
  } = $props();
</script>

<div
  class={cn(
    "bg-muted flex max-w-full shrink-0 flex-wrap rounded-md p-0.5 text-xs",
    className,
  )}
  role="radiogroup"
  aria-label={label}
>
  {#each options as o (o.value)}
    <button
      type="button"
      role="radio"
      aria-checked={value === o.value}
      disabled={o.disabled}
      class={cn(
        "flex h-6 min-w-0 items-center gap-1.5 truncate rounded px-2.5 disabled:opacity-40",
        value === o.value
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground",
      )}
      onclick={() => {
        value = o.value;
        onchange?.(o.value);
      }}
    >
      {#if o.dot}<span
          class="size-1.5 shrink-0 rounded-full"
          style="background:{o.dot}"
        ></span>{/if}{o.label}
    </button>
  {/each}
</div>
