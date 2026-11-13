<script lang="ts">
  import { tone } from "./state";
  let {
    stats,
    big = false,
  }: { stats: { label: string; value: string; delta?: string; tone?: "up" | "down" }[]; big?: boolean } = $props();
  // A long number gets the whole row rather than being cut or squeezed.
  const long = $derived(stats.some((s) => s.value.length > 10));
</script>

<dl class="grid {long ? 'grid-cols-1' : 'grid-cols-2'} gap-x-6 gap-y-4 p-2.5">
  {#each stats as s (s.label)}
    <div class="min-w-0">
      <dt class="text-muted-foreground line-clamp-2 text-sm" title={s.label}>{s.label}</dt>
      <dd
        class="display mt-0.5 font-semibold whitespace-nowrap {big ? 'text-4xl' : 'text-2xl'} {s.tone
          ? tone[s.tone]
          : ''} {/\d/.test(s.value) ? 'num' : ''}"
      >
        {s.value}
      </dd>
    </div>
  {/each}
</dl>
