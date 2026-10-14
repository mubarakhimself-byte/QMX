<script lang="ts">
  /** A one-line select for settings rows. */
  import * as Select from "$lib/components/ui/select";
  import { cn } from "$lib/utils";

  let {
    value = $bindable(),
    options,
    label,
    disabled = false,
    class: className,
    onchange,
  }: {
    value: string;
    options: readonly (string | { value: string; label: string })[];
    /** Screen-reader name. */
    label: string;
    disabled?: boolean;
    class?: string;
    onchange?: (v: string) => void;
  } = $props();

  const items = $derived(
    options.map((o) => (typeof o === "string" ? { value: o, label: o } : o)),
  );
</script>

<Select.Root
  type="single"
  bind:value
  {disabled}
  onValueChange={(v) => onchange?.(v)}
>
  <Select.Trigger aria-label={label} class={cn("min-w-36", className)}>
    {items.find((i) => i.value === value)?.label ?? value}
  </Select.Trigger>
  <Select.Content>
    {#each items as i (i.value)}
      <Select.Item value={i.value} label={i.label} />
    {/each}
  </Select.Content>
</Select.Root>
